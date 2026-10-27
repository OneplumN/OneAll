package store

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"oneall-go-api/internal/domain"
)

type PostgresStore struct {
	*MemoryStore
	DatabaseURL string
	pool        *pgxpool.Pool
}

const detectionTaskSelectColumns = `
	id, type, target, COALESCE(probe, ''), status,
	COALESCE(related_asset, ''), COALESCE(business_line, ''), COALESCE(environment, ''),
	COALESCE(protocol, ''), COALESCE(port, 0), COALESCE(timeout_seconds, 0),
	COALESCE(metadata, '{}'::jsonb), COALESCE(result, '{}'::jsonb),
	claimed_at, completed_at, COALESCE(claimed_by_probe_id, ''),
	COALESCE(latency_ms, 0), COALESCE(message, ''), COALESCE(result_id, ''),
	created_at, updated_at
`

func NewPostgresStore(databaseURL string) *PostgresStore {
	return &PostgresStore{
		MemoryStore: NewMemoryStore(),
		DatabaseURL: databaseURL,
	}
}

func (s *PostgresStore) Connect(ctx context.Context) error {
	pool, err := pgxpool.New(ctx, s.DatabaseURL)
	if err != nil {
		return err
	}
	s.pool = pool
	return nil
}

func (s *PostgresStore) Close() {
	if s.pool != nil {
		s.pool.Close()
	}
}

func (s *PostgresStore) ensurePool(ctx context.Context) error {
	if s.pool != nil {
		return nil
	}
	return s.Connect(ctx)
}

func (s *PostgresStore) nextID(ctx context.Context, prefix string, table string) (string, error) {
	return nextID(ctx, s.pool, prefix, table)
}

type idQuerier interface {
	QueryRow(ctx context.Context, sql string, args ...any) pgx.Row
}

func nextID(ctx context.Context, querier idQuerier, prefix string, table string) (string, error) {
	var next int
	idColumn := "id"
	if table == "event_outbox" {
		idColumn = "event_id"
	}
	query := fmt.Sprintf("SELECT COALESCE(MAX(NULLIF(regexp_replace(%s, '[^0-9]', '', 'g'), '')::int), 0) + 1 FROM %s", idColumn, table)
	if err := querier.QueryRow(ctx, query).Scan(&next); err != nil {
		return "", err
	}
	return fmt.Sprintf("%s-%04d", prefix, next), nil
}

func (s *PostgresStore) ListAssetModels() []domain.AssetModel {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListAssetModels()
	}

	rows, err := s.pool.Query(ctx, `
		SELECT id, name, code, fields, status, created_by, created_at
		FROM asset_models
		ORDER BY created_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListAssetModels()
	}
	defer rows.Close()

	var models []domain.AssetModel
	for rows.Next() {
		var model domain.AssetModel
		var fieldsJSON []byte
		var createdAt time.Time
		if err := rows.Scan(&model.ID, &model.Name, &model.Code, &fieldsJSON, &model.Status, &model.CreatedBy, &createdAt); err != nil {
			return s.MemoryStore.ListAssetModels()
		}
		_ = json.Unmarshal(fieldsJSON, &model.Fields)
		model.PrimaryKey = assetModelPrimaryKey(model)
		model.CreatedAt = createdAt.Format(time.RFC3339)
		models = append(models, model)
	}
	return models
}

func (s *PostgresStore) CreateAssetModel(input domain.AssetModel, actor string) (domain.AssetModel, []string) {
	if input.Name == "" || input.Code == "" {
		return domain.AssetModel{}, []string{"资产模型 name 和 code 必填"}
	}
	if errs := domain.ValidateAssetFields(input.Fields); len(errs) > 0 {
		return domain.AssetModel{}, errs
	}
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.CreateAssetModel(input, actor)
	}

	fieldsJSON, _ := json.Marshal(input.Fields)
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return domain.AssetModel{}, []string{err.Error()}
	}
	defer tx.Rollback(ctx)

	id, err := s.nextID(ctx, "MDL", "asset_models")
	if err != nil {
		return domain.AssetModel{}, []string{err.Error()}
	}
	var createdAt time.Time
	err = tx.QueryRow(ctx, `
		INSERT INTO asset_models (id, code, name, fields, status, created_by)
		VALUES ($1, $2, $3, $4::jsonb, 'active', $5)
		RETURNING created_at
	`, id, input.Code, input.Name, string(fieldsJSON), actor).Scan(&createdAt)
	if err != nil {
		return domain.AssetModel{}, []string{err.Error()}
	}
	if err := s.insertAuditNotificationOutbox(ctx, tx, actor, "创建资产模型", id, "资产模型已创建："+input.Name, "assets", "asset.sync.started", map[string]any{"model_id": id, "reason": "model_created"}); err != nil {
		return domain.AssetModel{}, []string{err.Error()}
	}
	if err := tx.Commit(ctx); err != nil {
		return domain.AssetModel{}, []string{err.Error()}
	}
	return domain.AssetModel{ID: id, Name: input.Name, Code: input.Code, Fields: input.Fields, PrimaryKey: assetModelPrimaryKey(input), Status: "active", CreatedBy: actor, CreatedAt: createdAt.Format(time.RFC3339)}, nil
}

func (s *PostgresStore) UpdateAssetModel(id string, input domain.AssetModel, actor string) (domain.AssetModel, bool, []string) {
	if input.Fields != nil {
		if errs := domain.ValidateAssetFields(input.Fields); len(errs) > 0 {
			return domain.AssetModel{}, true, errs
		}
	}
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.UpdateAssetModel(id, input, actor)
	}

	current, found := s.getAssetModel(ctx, id)
	if !found {
		return domain.AssetModel{}, false, nil
	}
	if input.Name != "" {
		current.Name = input.Name
	}
	if input.Fields != nil {
		current.Fields = input.Fields
	}
	if input.PrimaryKey != "" {
		current.PrimaryKey = input.PrimaryKey
	}
	if !assetModelHasField(current, current.PrimaryKey) {
		current.PrimaryKey = assetModelPrimaryKey(current)
	}
	if input.Status != "" {
		current.Status = input.Status
	}
	fieldsJSON, _ := json.Marshal(current.Fields)
	_, err := s.pool.Exec(ctx, `
		UPDATE asset_models
		SET name = $2, fields = $3::jsonb, status = $4, updated_at = now()
		WHERE id = $1 OR code = $1
	`, id, current.Name, string(fieldsJSON), current.Status)
	if err != nil {
		return domain.AssetModel{}, true, []string{err.Error()}
	}
	s.writeAuditNotification(ctx, actor, "更新资产模型", current.ID, "资产模型已更新："+current.Name, "assets", "asset.sync.started", map[string]any{"model_id": current.ID, "reason": "model_updated"})
	return current, true, nil
}

func (s *PostgresStore) ListAssetRecords(modelID string) []domain.AssetRecord {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListAssetRecords(modelID)
	}

	query := `
		SELECT id, model_id, model_code, name, owner, environment, business_line, fields, updated_at
		FROM asset_records
		WHERE $1 = '' OR model_id = $1 OR model_code = $1
		ORDER BY updated_at DESC
	`
	rows, err := s.pool.Query(ctx, query, modelID)
	if err != nil {
		return s.MemoryStore.ListAssetRecords(modelID)
	}
	defer rows.Close()

	var records []domain.AssetRecord
	for rows.Next() {
		var id, modelID, modelCode string
		var name, owner, environment, businessLine *string
		var fieldsJSON []byte
		var updatedAt time.Time
		if err := rows.Scan(&id, &modelID, &modelCode, &name, &owner, &environment, &businessLine, &fieldsJSON, &updatedAt); err != nil {
			return s.MemoryStore.ListAssetRecords(modelID)
		}
		record := domain.AssetRecord{}
		_ = json.Unmarshal(fieldsJSON, &record)
		record["id"] = id
		record["model_id"] = modelID
		record["model_code"] = modelCode
		if name != nil {
			record["name"] = *name
		}
		if owner != nil {
			record["owner"] = *owner
		}
		if environment != nil {
			record["environment"] = *environment
		}
		if businessLine != nil {
			record["business_line"] = *businessLine
		}
		record["updated_at"] = updatedAt.Format(time.RFC3339)
		records = append(records, record)
	}
	return records
}

func (s *PostgresStore) BatchAssetRecords(modelID string, records []domain.AssetRecord, actor string) ([]domain.AssetRecord, []string, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.BatchAssetRecords(modelID, records, actor)
	}
	model, found := s.getAssetModel(ctx, modelID)
	if !found {
		return nil, []string{"资产模型不存在"}, false
	}
	if len(records) == 0 {
		return nil, []string{"records 必须至少包含一条记录"}, true
	}

	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return nil, []string{err.Error()}, true
	}
	defer tx.Rollback(ctx)

	updated := make([]domain.AssetRecord, 0, len(records))
	for _, record := range records {
		if errs := domain.ValidateAssetRecord(model, record); len(errs) > 0 {
			return nil, errs, true
		}
		id, _ := record["id"].(string)
		if id == "" {
			id, err = s.nextID(ctx, "AST", "asset_records")
			if err != nil {
				return nil, []string{err.Error()}, true
			}
		}
		fieldsJSON, _ := json.Marshal(record)
		name, _ := record["name"].(string)
		owner, _ := record["owner"].(string)
		environment, _ := record["environment"].(string)
		businessLine, _ := record["business_line"].(string)
		var updatedAt time.Time
		err = tx.QueryRow(ctx, `
			INSERT INTO asset_records (id, model_id, model_code, name, owner, environment, business_line, fields)
			VALUES ($1, $2, $3, NULLIF($4, ''), NULLIF($5, ''), NULLIF($6, ''), NULLIF($7, ''), $8::jsonb)
			ON CONFLICT (id) DO UPDATE SET
			  name = EXCLUDED.name,
			  owner = EXCLUDED.owner,
			  environment = EXCLUDED.environment,
			  business_line = EXCLUDED.business_line,
			  fields = EXCLUDED.fields,
			  version = asset_records.version + 1,
			  updated_at = now()
			RETURNING updated_at
		`, id, model.ID, model.Code, name, owner, environment, businessLine, string(fieldsJSON)).Scan(&updatedAt)
		if err != nil {
			return nil, []string{err.Error()}, true
		}
		item := domain.AssetRecord{}
		for key, value := range record {
			item[key] = value
		}
		item["id"] = id
		item["model_id"] = model.ID
		item["model_code"] = model.Code
		item["updated_at"] = updatedAt.Format(time.RFC3339)
		updated = append(updated, item)
	}
	if err := s.insertAuditNotificationOutbox(ctx, tx, actor, "批量写入资产记录", model.ID, "资产记录已更新："+model.Name, "assets", "asset.sync.completed", map[string]any{"model_id": model.ID, "count": len(updated)}); err != nil {
		return nil, []string{err.Error()}, true
	}
	if err := tx.Commit(ctx); err != nil {
		return nil, []string{err.Error()}, true
	}
	return updated, nil, true
}

func (s *PostgresStore) PreviewAssetSync(modelID string, input map[string]any) (map[string]any, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.PreviewAssetSync(modelID, input)
	}
	model, found := s.getAssetModel(ctx, modelID)
	if !found {
		return nil, false
	}
	source := "manual"
	if value, ok := input["source"].(string); ok && value != "" {
		source = value
	}
	owner := "OpsAdmin"
	if value, ok := input["owner"].(string); ok && value != "" {
		owner = value
	}
	var existing int
	_ = s.pool.QueryRow(ctx, `SELECT count(*) FROM asset_records WHERE model_id = $1`, model.ID).Scan(&existing)
	creates := 1
	updates := 0
	if existing > 0 {
		creates = 0
		updates = 1
	}
	sample := domain.AssetRecord{
		"name":          model.Code + "-sample",
		"ip":            "10.0.0.10",
		"owner":         owner,
		"environment":   "prod",
		"business_line": "支付业务",
	}
	return map[string]any{"model_id": model.ID, "source": source, "total": 1, "creates": creates, "updates": updates, "deletes": 0, "sample": sample, "samples": []domain.AssetRecord{sample}}, true
}

func (s *PostgresStore) RunAssetSync(modelID string, input map[string]any, actor string) (map[string]any, bool, []string) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.RunAssetSync(modelID, input, actor)
	}
	preview, found := s.PreviewAssetSync(modelID, input)
	if !found {
		return nil, false, nil
	}
	sample, _ := preview["sample"].(domain.AssetRecord)
	records, errs, _ := s.BatchAssetRecords(modelID, []domain.AssetRecord{sample}, actor)
	if len(errs) > 0 {
		return nil, true, errs
	}
	runID, err := s.nextID(ctx, "RUN", "asset_sync_runs")
	if err != nil {
		return nil, true, []string{err.Error()}
	}
	payload := map[string]any{"model_id": modelID, "source": preview["source"], "count": len(records)}
	payloadJSON, _ := json.Marshal(payload)
	_, err = s.pool.Exec(ctx, `
		INSERT INTO asset_sync_runs (id, model_id, source, status, preview, result, started_by, finished_at)
		VALUES ($1, $2, $3, 'completed', $4::jsonb, $4::jsonb, $5, now())
	`, runID, modelID, preview["source"], string(payloadJSON), actor)
	if err != nil {
		return nil, true, []string{err.Error()}
	}
	preview["run_id"] = runID
	preview["records"] = records
	preview["count"] = len(records)
	return preview, true, nil
}

func (s *PostgresStore) ListSyncRuns() []map[string]any {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListSyncRuns()
	}
	rows, err := s.pool.Query(ctx, `
		SELECT id, source, result, started_at
		FROM asset_sync_runs
		ORDER BY started_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListSyncRuns()
	}
	defer rows.Close()
	var items []map[string]any
	for rows.Next() {
		var id, source string
		var resultJSON []byte
		var startedAt time.Time
		if err := rows.Scan(&id, &source, &resultJSON, &startedAt); err != nil {
			return s.MemoryStore.ListSyncRuns()
		}
		payload := map[string]any{}
		_ = json.Unmarshal(resultJSON, &payload)
		if payload["source"] == nil {
			payload["source"] = source
		}
		items = append(items, map[string]any{
			"event_id":   id,
			"event_type": "asset.sync.completed",
			"producer":   "assets",
			"payload":    payload,
			"created_at": startedAt.Format(time.RFC3339),
		})
	}
	if items == nil {
		return []map[string]any{}
	}
	return items
}

func (s *PostgresStore) ValidateCMDBDomain(domainName string) map[string]any {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ValidateCMDBDomain(domainName)
	}
	var id, modelID string
	err := s.pool.QueryRow(ctx, `
		SELECT id, model_id
		FROM asset_records
		WHERE name = $1 OR fields->>'domain' = $1 OR fields->>'target' = $1
		ORDER BY updated_at DESC
		LIMIT 1
	`, domainName).Scan(&id, &modelID)
	if err == pgx.ErrNoRows {
		return map[string]any{"domain": domainName, "matched": false, "model_id": nil, "asset_id": nil, "missing_fields": []string{"owner", "environment"}, "recommendation": "未命中资产记录，建议先创建模型并同步数据"}
	}
	if err != nil {
		return s.MemoryStore.ValidateCMDBDomain(domainName)
	}
	return map[string]any{"domain": domainName, "matched": true, "model_id": modelID, "asset_id": id, "missing_fields": []string{}, "recommendation": "可关联资产并进入监控策略"}
}

func (s *PostgresStore) ListStrategies() []domain.Strategy {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListStrategies()
	}
	rows, err := s.pool.Query(ctx, `
		SELECT id, name, scope, enabled, version, rule, created_at
		FROM monitoring_strategies
		ORDER BY created_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListStrategies()
	}
	defer rows.Close()

	var items []domain.Strategy
	for rows.Next() {
		var item domain.Strategy
		var ruleJSON []byte
		var createdAt time.Time
		if err := rows.Scan(&item.ID, &item.Name, &item.Scope, &item.Enabled, &item.Version, &ruleJSON, &createdAt); err != nil {
			return s.MemoryStore.ListStrategies()
		}
		_ = json.Unmarshal(ruleJSON, &item.Rule)
		item.CreatedAt = createdAt.Format(time.RFC3339)
		items = append(items, item)
	}
	return items
}

func (s *PostgresStore) CreateStrategy(input domain.Strategy, actor string) (domain.Strategy, []string) {
	if errs := domain.ValidateAlertRule(input.Rule); len(errs) > 0 {
		return domain.Strategy{}, errs
	}
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.CreateStrategy(input, actor)
	}
	ruleJSON, _ := json.Marshal(input.Rule)
	id, err := s.nextID(ctx, "STR", "monitoring_strategies")
	if err != nil {
		return domain.Strategy{}, []string{err.Error()}
	}
	name := input.Name
	if name == "" {
		name = "未命名策略"
	}
	scope := input.Scope
	if scope == "" {
		scope = input.Rule.Scope.AssetModel
	}
	var createdAt time.Time
	err = s.pool.QueryRow(ctx, `
		INSERT INTO monitoring_strategies (id, name, scope, enabled, version, rule, created_by)
		VALUES ($1, $2, $3, true, 'v1', $4::jsonb, $5)
		RETURNING created_at
	`, id, name, scope, string(ruleJSON), actor).Scan(&createdAt)
	if err != nil {
		return domain.Strategy{}, []string{err.Error()}
	}
	s.writeAuditNotification(ctx, actor, "创建监控策略", id, "监控策略已创建："+name, "monitoring", "monitoring.strategy.enabled", map[string]any{"strategy_id": id})
	return domain.Strategy{ID: id, Name: name, Scope: scope, Enabled: true, Version: "v1", Rule: input.Rule, CreatedAt: createdAt.Format(time.RFC3339)}, nil
}

func (s *PostgresStore) BatchStrategies(ids []string, action string, actor string) ([]domain.Strategy, string) {
	if action != "enable" && action != "disable" {
		return nil, "不支持的策略批量动作"
	}
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.BatchStrategies(ids, action, actor)
	}
	enabled := action == "enable"
	var updated []domain.Strategy
	for _, id := range ids {
		_, err := s.pool.Exec(ctx, `UPDATE monitoring_strategies SET enabled = $2, updated_at = now() WHERE id = $1`, id, enabled)
		if err != nil {
			return nil, err.Error()
		}
		s.writeAuditNotification(ctx, actor, "批量更新策略", id, "监控策略已更新："+id, "monitoring", "monitoring.strategy.enabled", map[string]any{"strategy_id": id, "enabled": enabled})
	}
	for _, item := range s.ListStrategies() {
		for _, id := range ids {
			if item.ID == id {
				updated = append(updated, item)
			}
		}
	}
	return updated, ""
}

func (s *PostgresStore) CreateDetection(input domain.DetectionTask, actor string) domain.DetectionTask {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.CreateDetection(input, actor)
	}
	id, err := s.nextID(ctx, "DET", "detection_tasks")
	if err != nil {
		return s.MemoryStore.CreateDetection(input, actor)
	}
	task := domain.DetectionTask{
		ID:           id,
		Type:         valueOrDefault(input.Type, "http"),
		Target:       input.Target,
		Probe:        valueOrDefault(input.Probe, "probe-sh-01"),
		Status:       "pending",
		RelatedAsset: valueOrDefault(input.RelatedAsset, "-"),
		BusinessLine: valueOrDefault(input.BusinessLine, "支付业务"),
		Environment:  valueOrDefault(input.Environment, "prod"),
		Protocol:     valueOrDefault(input.Protocol, strings.ToUpper(input.Type)),
		Port:         input.Port,
		TimeoutSec:   input.TimeoutSec,
		Metadata:     input.Metadata,
	}
	if task.TimeoutSec <= 0 {
		task.TimeoutSec = 10
	}
	if task.Metadata == nil {
		task.Metadata = map[string]any{}
	}
	metadataJSON, _ := json.Marshal(task.Metadata)
	var createdAt time.Time
	err = s.pool.QueryRow(ctx, `
		INSERT INTO detection_tasks (id, type, target, probe, status, related_asset, business_line, environment, protocol, port, timeout_seconds, metadata, created_by)
		VALUES ($1, $2, $3, $4, 'pending', $5, $6, $7, $8, $9, $10, $11::jsonb, $12)
		RETURNING created_at
	`, task.ID, task.Type, task.Target, task.Probe, task.RelatedAsset, task.BusinessLine, task.Environment, task.Protocol, task.Port, task.TimeoutSec, string(metadataJSON), actor).Scan(&createdAt)
	if err != nil {
		return s.MemoryStore.CreateDetection(input, actor)
	}
	task.CreatedAt = createdAt.Format(time.RFC3339)
	task.UpdatedAt = task.CreatedAt
	s.writeAuditNotification(ctx, actor, "创建一次性检测", task.ID, "检测任务已创建："+task.ID, "detection", "probe.result.received", map[string]any{"task_id": task.ID, "status": task.Status})
	return task
}

func (s *PostgresStore) ListDetectionTasks() []domain.DetectionTask {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListDetectionTasks()
	}
	rows, err := s.pool.Query(ctx, `
		SELECT `+detectionTaskSelectColumns+`
		FROM detection_tasks
		ORDER BY created_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListDetectionTasks()
	}
	defer rows.Close()

	items := []domain.DetectionTask{}
	for rows.Next() {
		task, err := scanDetectionTask(rows)
		if err != nil {
			return s.MemoryStore.ListDetectionTasks()
		}
		items = append(items, task)
	}
	return items
}

func (s *PostgresStore) GetDetectionTask(id string) (domain.DetectionTask, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.GetDetectionTask(id)
	}
	task, found, err := s.getDetectionTask(ctx, id)
	if err != nil {
		return s.MemoryStore.GetDetectionTask(id)
	}
	return task, found
}

func (s *PostgresStore) ClaimProbeTasks(probeID string, limit int) []domain.DetectionTask {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ClaimProbeTasks(probeID, limit)
	}
	_, _ = s.pool.Exec(ctx, `
		UPDATE detection_tasks
		SET status = 'pending',
		    updated_at = now(),
		    claimed_at = NULL,
		    claimed_by_probe_id = NULL,
		    message = '探针执行超时，任务已重新入队',
		    result = jsonb_set(COALESCE(result, '{}'::jsonb), '{message}', '"探针执行超时，任务已重新入队"'::jsonb, true)
		WHERE status = 'running'
		  AND COALESCE(claimed_at, updated_at) < now() - interval '2 minutes'
	`)
	if limit <= 0 {
		limit = 5
	}
	if limit > 10 {
		limit = 10
	}
	rows, err := s.pool.Query(ctx, `
		WITH claimed AS (
			SELECT id
			FROM detection_tasks
			WHERE status = 'pending'
			  AND ($1 = '' OR probe = $1)
			ORDER BY created_at ASC
			LIMIT $2
			FOR UPDATE SKIP LOCKED
		)
		UPDATE detection_tasks
		SET status = 'running',
		    claimed_at = now(),
		    claimed_by_probe_id = $1,
		    message = '探针已领取，等待回传',
		    updated_at = now()
		WHERE id IN (SELECT id FROM claimed)
		RETURNING `+detectionTaskSelectColumns+`
	`, probeID, limit)
	if err != nil {
		return s.MemoryStore.ClaimProbeTasks(probeID, limit)
	}
	defer rows.Close()

	var items []domain.DetectionTask
	for rows.Next() {
		task, err := scanDetectionTask(rows)
		if err != nil {
			return s.MemoryStore.ClaimProbeTasks(probeID, limit)
		}
		items = append(items, task)
	}
	return items
}

func (s *PostgresStore) SubmitProbeResult(taskID string, result map[string]any, actor string) (domain.DetectionTask, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
	}
	task, found, err := s.getDetectionTask(ctx, taskID)
	if err != nil || !found {
		return domain.DetectionTask{}, found
	}
	if isCompletedDetectionStatus(task.Status) {
		return task, true
	}
	success, _ := result["success"].(bool)
	if status, ok := result["status"].(string); ok {
		success = status == "success"
	}
	nextStatus := "failed"
	if success {
		nextStatus = "success"
	}
	resultID, _ := result["result_id"].(string)
	if resultID == "" {
		resultID = fmt.Sprintf("%s:%s", actor, taskID)
	}
	probeID, _ := result["probe_id"].(string)
	latencyMs := 0
	if latency, ok := numericInt(result["latency_ms"]); ok {
		latencyMs = latency
	} else if latency, ok := numericInt(result["response_time_ms"]); ok {
		latencyMs = latency
	}
	message, _ := result["message"].(string)
	resultJSON, _ := json.Marshal(result)
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
	}
	defer tx.Rollback(ctx)

	var updatedAt time.Time
	var completedAt time.Time
	err = tx.QueryRow(ctx, `
		UPDATE detection_tasks
		SET status = $2,
		    result = $3::jsonb,
		    result_id = $4,
		    completed_at = now(),
		    claimed_by_probe_id = COALESCE(NULLIF($5, ''), claimed_by_probe_id),
		    latency_ms = $6,
		    message = $7,
		    updated_at = now()
		WHERE id = $1
		  AND status NOT IN ('success', 'failed', 'canceled')
		RETURNING completed_at, updated_at
	`, taskID, nextStatus, string(resultJSON), resultID, probeID, latencyMs, message).Scan(&completedAt, &updatedAt)
	if err != nil {
		if err == pgx.ErrNoRows {
			if current, found, getErr := s.getDetectionTask(ctx, taskID); getErr == nil && found {
				return current, true
			}
		}
		return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
	}
	task.Status = nextStatus
	task.Result = result
	task.ResultID = resultID
	task.CompletedAt = completedAt.Format(time.RFC3339)
	task.ClaimedBy = probeID
	task.LatencyMs = latencyMs
	task.Message = message
	task.UpdatedAt = updatedAt.Format(time.RFC3339)
	if err := s.insertAuditNotificationOutbox(ctx, tx, actor, "回传探针结果", taskID, "探针结果已回传："+taskID, "probes", "probe.result.received", map[string]any{"task_id": taskID, "success": success}); err != nil {
		return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
	}
	if !success {
		if err := s.createAlertAndMaybeWorkorderPostgres(ctx, tx, task); err != nil {
			return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
		}
	}
	if err := tx.Commit(ctx); err != nil {
		return s.MemoryStore.SubmitProbeResult(taskID, result, actor)
	}
	return task, true
}

func (s *PostgresStore) RegisterProbe(input domain.ProbeNode) domain.ProbeNode {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.RegisterProbe(input)
	}
	capabilities := input.Capabilities
	if len(capabilities) == 0 {
		capabilities = []string{"HTTP"}
	}
	id, err := s.nextID(ctx, "PRB", "probe_nodes")
	if err != nil {
		return s.MemoryStore.RegisterProbe(input)
	}
	token := fmt.Sprintf("probe_token_%d", time.Now().UnixNano())
	capabilitiesJSON, _ := json.Marshal(capabilities)
	var createdAt time.Time
	var heartbeatAt time.Time
	err = s.pool.QueryRow(ctx, `
		INSERT INTO probe_nodes (id, name, region, capabilities, status, token_hash, heartbeat_at)
		VALUES ($1, $2, $3, $4::jsonb, 'online', $5, now())
		RETURNING created_at, heartbeat_at
	`, id, valueOrDefault(input.Name, strings.ToLower(id)), valueOrDefault(input.Region, "unknown"), string(capabilitiesJSON), probeTokenHash(token)).Scan(&createdAt, &heartbeatAt)
	if err != nil {
		return s.MemoryStore.RegisterProbe(input)
	}
	probe := domain.ProbeNode{
		ID:                 id,
		Name:               valueOrDefault(input.Name, strings.ToLower(id)),
		Region:             valueOrDefault(input.Region, "unknown"),
		NetworkType:        valueOrDefault(input.NetworkType, "unknown"),
		IPAddress:          input.IPAddress,
		Capabilities:       capabilities,
		Status:             "online",
		HeartbeatAt:        heartbeatAt.Format(time.RFC3339),
		Version:            valueOrDefault(input.Version, "v1"),
		ConnectionStatus:   "connected",
		ConfigStatus:       "acknowledged",
		RegisteredAt:       createdAt.Format(time.RFC3339),
		LastConfigSyncAt:   heartbeatAt.Format(time.RFC3339),
		Token:              token,
		BootstrapTokenHint: probeTokenHint(token),
		AgentConfig:        defaultProbeAgentConfig(capabilities),
	}
	s.writeAuditNotification(ctx, "probe-bootstrap", "注册探针", probe.ID, "探针已注册："+probe.Name, "probes", "probe.registered", map[string]any{"probe_id": probe.ID})
	return probe
}

func (s *PostgresStore) ListProbes() []domain.ProbeNode {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListProbes()
	}
	rows, err := s.pool.Query(ctx, `
		SELECT id, name, region, capabilities, status, heartbeat_at, created_at, updated_at
		FROM probe_nodes
		ORDER BY created_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListProbes()
	}
	defer rows.Close()
	items := []domain.ProbeNode{}
	for rows.Next() {
		probe, err := scanProbeNode(rows)
		if err != nil {
			return s.MemoryStore.ListProbes()
		}
		items = append(items, sanitizeProbe(probe))
	}
	return items
}

func (s *PostgresStore) ListProbeHealth(hours int, intervalMinutes int) map[string]any {
	probes := s.ListProbes()
	items := make([]map[string]any, 0, len(probes))
	for _, probe := range probes {
		items = append(items, map[string]any{
			"probe":                   probe,
			"probe_id":                probe.ID,
			"name":                    probe.Name,
			"status":                  probe.Status,
			"connection_status":       probe.ConnectionStatus,
			"config_status":           probe.ConfigStatus,
			"heartbeat_at":            probe.HeartbeatAt,
			"heartbeat_delay_seconds": heartbeatDelaySeconds(probe.HeartbeatAt),
			"success_rate":            probe.SuccessRate,
			"avg_latency_ms":          probe.AvgLatencyMs,
			"active_tasks":            probe.ActiveTasks,
			"queue_depth":             probe.QueueDepth,
			"version":                 probe.Version,
		})
	}
	return map[string]any{
		"items":  items,
		"window": map[string]any{"hours": hours, "interval_minutes": intervalMinutes},
	}
}

func (s *PostgresStore) GetProbeRuntime(id string) (map[string]any, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.GetProbeRuntime(id)
	}
	row := s.pool.QueryRow(ctx, `
		SELECT id, name, region, capabilities, status, heartbeat_at, created_at, updated_at
		FROM probe_nodes
		WHERE id = $1 OR name = $1
	`, id)
	probe, err := scanProbeNode(row)
	if err == pgx.ErrNoRows {
		return nil, false
	}
	if err != nil {
		return s.MemoryStore.GetProbeRuntime(id)
	}
	pending := countWhere(ctx, s.pool, "detection_tasks", fmt.Sprintf("status = 'pending' AND probe IN ('%s', '%s')", strings.ReplaceAll(probe.ID, "'", "''"), strings.ReplaceAll(probe.Name, "'", "''")))
	running := countWhere(ctx, s.pool, "detection_tasks", fmt.Sprintf("status = 'running' AND probe IN ('%s', '%s')", strings.ReplaceAll(probe.ID, "'", "''"), strings.ReplaceAll(probe.Name, "'", "''")))
	return map[string]any{
		"probe":                   sanitizeProbe(probe),
		"probe_id":                probe.ID,
		"name":                    probe.Name,
		"status":                  probe.Status,
		"connection_status":       probe.ConnectionStatus,
		"heartbeat_at":            probe.HeartbeatAt,
		"heartbeat_delay_seconds": heartbeatDelaySeconds(probe.HeartbeatAt),
		"pending_tasks":           pending,
		"running_tasks":           running,
		"capabilities":            probe.Capabilities,
		"tasks": map[string]any{
			"pending": pending,
			"running": running,
			"active":  running,
		},
		"resource_metrics": map[string]any{},
	}, true
}

func (s *PostgresStore) HeartbeatProbe(id string, input domain.ProbeNode, actor string) (domain.ProbeNode, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.HeartbeatProbe(id, input, actor)
	}
	capabilitiesJSON := "[]"
	if len(input.Capabilities) > 0 {
		raw, _ := json.Marshal(input.Capabilities)
		capabilitiesJSON = string(raw)
	}
	row := s.pool.QueryRow(ctx, `
		UPDATE probe_nodes
		SET status = 'online',
		    heartbeat_at = now(),
		    updated_at = now(),
		    capabilities = CASE WHEN $2::jsonb = '[]'::jsonb THEN capabilities ELSE $2::jsonb END
		WHERE id = $1 OR name = $1
		RETURNING id, name, region, capabilities, status, heartbeat_at, created_at, updated_at
	`, id, capabilitiesJSON)
	probe, err := scanProbeNode(row)
	if err == pgx.ErrNoRows {
		return domain.ProbeNode{}, false
	}
	if err != nil {
		return s.MemoryStore.HeartbeatProbe(id, input, actor)
	}
	return sanitizeProbe(probe), true
}

func (s *PostgresStore) ValidateProbeToken(id string, token string) bool {
	if id == "" || token == "" {
		return false
	}
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ValidateProbeToken(id, token)
	}
	var exists bool
	err := s.pool.QueryRow(ctx, `
		SELECT EXISTS(
			SELECT 1 FROM probe_nodes
			WHERE (id = $1 OR name = $1) AND token_hash = $2
		)
	`, id, probeTokenHash(token)).Scan(&exists)
	if err != nil {
		return false
	}
	return exists
}

func (s *PostgresStore) ListAlerts() []domain.AlertEvent {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListAlerts()
	}
	rows, err := s.pool.Query(ctx, `
		SELECT id, severity, title, asset, COALESCE(owner, ''), COALESCE(business_line, ''), COALESCE(environment, ''), status, COALESCE(notify_status, ''), COALESCE(workorder_id, ''), COALESCE(source_task_id, ''), created_at
		FROM alert_events
		ORDER BY created_at DESC
	`)
	if err != nil {
		return s.MemoryStore.ListAlerts()
	}
	defer rows.Close()
	var items []domain.AlertEvent
	for rows.Next() {
		item, err := scanAlert(rows)
		if err != nil {
			return s.MemoryStore.ListAlerts()
		}
		items = append(items, item)
	}
	return items
}

func (s *PostgresStore) GetAlert(id string) (domain.AlertEvent, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.GetAlert(id)
	}
	row := s.pool.QueryRow(ctx, `
		SELECT id, severity, title, asset, COALESCE(owner, ''), COALESCE(business_line, ''), COALESCE(environment, ''), status, COALESCE(notify_status, ''), COALESCE(workorder_id, ''), COALESCE(source_task_id, ''), created_at
		FROM alert_events
		WHERE id = $1
	`, id)
	item, err := scanAlert(row)
	if err == pgx.ErrNoRows {
		return domain.AlertEvent{}, false
	}
	if err != nil {
		return s.MemoryStore.GetAlert(id)
	}
	return item, true
}

func (s *PostgresStore) CloseAlerts(ids []string, actor string) []domain.AlertEvent {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.CloseAlerts(ids, actor)
	}
	var updated []domain.AlertEvent
	for _, id := range ids {
		_, err := s.pool.Exec(ctx, `UPDATE alert_events SET status = '已恢复', updated_at = now() WHERE id = $1`, id)
		if err != nil {
			return s.MemoryStore.CloseAlerts(ids, actor)
		}
		s.writeAuditNotification(ctx, actor, "关闭告警", id, "告警已关闭："+id, "alerts", "alert.closed", map[string]any{"alert_id": id})
		if item, found := s.GetAlert(id); found {
			updated = append(updated, item)
		}
	}
	return updated
}

func (s *PostgresStore) ListWorkorders(role string) []domain.Workorder {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListWorkorders(role)
	}
	rows, err := s.pool.Query(ctx, `
		SELECT id, type, title, applicant, COALESCE(assignee, ''), status, COALESCE(sla, ''), COALESCE(business_line, ''), COALESCE(environment, ''), COALESCE(related_object, ''), COALESCE(related_alert_id, ''), created_at, updated_at
		FROM workorder_requests
		WHERE $1 <> 'Approver' OR status IN ('submitted', 'approved')
		ORDER BY created_at DESC
	`, role)
	if err != nil {
		return s.MemoryStore.ListWorkorders(role)
	}
	defer rows.Close()
	var items []domain.Workorder
	for rows.Next() {
		item, err := scanWorkorder(rows)
		if err != nil {
			return s.MemoryStore.ListWorkorders(role)
		}
		items = append(items, item)
	}
	return items
}

func (s *PostgresStore) GetWorkorder(id string) (domain.Workorder, bool) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.GetWorkorder(id)
	}
	row := s.pool.QueryRow(ctx, `
		SELECT id, type, title, applicant, COALESCE(assignee, ''), status, COALESCE(sla, ''), COALESCE(business_line, ''), COALESCE(environment, ''), COALESCE(related_object, ''), COALESCE(related_alert_id, ''), created_at, updated_at
		FROM workorder_requests
		WHERE id = $1
	`, id)
	item, err := scanWorkorder(row)
	if err == pgx.ErrNoRows {
		return domain.Workorder{}, false
	}
	if err != nil {
		return s.MemoryStore.GetWorkorder(id)
	}
	return item, true
}

func (s *PostgresStore) CreateWorkorder(input domain.Workorder, actor string) domain.Workorder {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.CreateWorkorder(input, actor)
	}
	id, err := s.nextID(ctx, "WO", "workorder_requests")
	if err != nil {
		return s.MemoryStore.CreateWorkorder(input, actor)
	}
	workorder := domain.Workorder{
		ID:             id,
		Type:           valueOrDefault(input.Type, "拨测监控申请"),
		Title:          input.Title,
		Applicant:      valueOrDefault(input.Applicant, actor),
		Assignee:       valueOrDefault(input.Assignee, "待分配"),
		Status:         valueOrDefault(input.Status, "submitted"),
		SLA:            valueOrDefault(input.SLA, "4h"),
		BusinessLine:   valueOrDefault(input.BusinessLine, "支付业务"),
		Environment:    valueOrDefault(input.Environment, "prod"),
		RelatedObject:  valueOrDefault(input.RelatedObject, "-"),
		RelatedAlertID: input.RelatedAlertID,
	}
	if workorder.RelatedAlertID == "" && strings.HasPrefix(workorder.RelatedObject, "ALT-") {
		workorder.RelatedAlertID = workorder.RelatedObject
	}
	var createdAt time.Time
	var updatedAt time.Time
	err = s.pool.QueryRow(ctx, `
		INSERT INTO workorder_requests (id, type, title, applicant, assignee, status, sla, related_object, related_alert_id, business_line, environment)
		VALUES ($1, $2, $3, $4, NULLIF($5, ''), $6, $7, NULLIF($8, ''), NULLIF($9, ''), $10, $11)
		RETURNING created_at, updated_at
		`, workorder.ID, workorder.Type, workorder.Title, workorder.Applicant, workorder.Assignee, workorder.Status, workorder.SLA, workorder.RelatedObject, workorder.RelatedAlertID, workorder.BusinessLine, workorder.Environment).Scan(&createdAt, &updatedAt)
	if err != nil {
		return s.MemoryStore.CreateWorkorder(input, actor)
	}
	workorder.CreatedAt = createdAt.Format(time.RFC3339)
	workorder.UpdatedAt = updatedAt.Format(time.RFC3339)
	s.writeAuditNotification(ctx, actor, "创建工单", workorder.ID, "工单已创建："+workorder.ID, "workorders", "workorder.created", map[string]any{"workorder_id": workorder.ID})
	return workorder
}

func (s *PostgresStore) TransitionWorkorder(id string, nextStatus string) (domain.Workorder, bool, error) {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.TransitionWorkorder(id, nextStatus)
	}
	current, found := s.GetWorkorder(id)
	if !found {
		return domain.Workorder{}, false, nil
	}
	next, err := domain.TransitionWorkorder(current, nextStatus)
	if err != nil {
		return current, true, err
	}
	var updatedAt time.Time
	err = s.pool.QueryRow(ctx, `
		UPDATE workorder_requests
		SET status = $2, updated_at = now()
		WHERE id = $1
		RETURNING updated_at
	`, id, nextStatus).Scan(&updatedAt)
	if err != nil {
		return current, true, err
	}
	next.UpdatedAt = updatedAt.Format(time.RFC3339)
	s.writeAuditNotification(ctx, "Approver", "工单流转到 "+nextStatus, id, "工单状态已更新："+id, "workorders", "workorder.completed", map[string]any{"workorder_id": id, "status": nextStatus})
	return next, true, nil
}

func (s *PostgresStore) BatchWorkorders(ids []string, action string, actor string) ([]domain.Workorder, string) {
	nextStatus := map[string]string{"approve": "approved", "reject": "rejected", "execute": "executing", "complete": "completed", "fail": "failed"}[action]
	if nextStatus == "" {
		return nil, "不支持的工单批量动作"
	}
	var items []domain.Workorder
	for _, id := range ids {
		item, found, err := s.TransitionWorkorder(id, nextStatus)
		if found && err == nil {
			items = append(items, item)
		}
	}
	return items, ""
}

func (s *PostgresStore) ListNotifications() []domain.Notification {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListNotifications()
	}
	rows, err := s.pool.Query(ctx, `SELECT id, target, title, status, created_at FROM notifications ORDER BY created_at DESC`)
	if err != nil {
		return s.MemoryStore.ListNotifications()
	}
	defer rows.Close()
	var items []domain.Notification
	for rows.Next() {
		var item domain.Notification
		var createdAt time.Time
		if err := rows.Scan(&item.ID, &item.Target, &item.Title, &item.Status, &createdAt); err != nil {
			return s.MemoryStore.ListNotifications()
		}
		item.CreatedAt = createdAt.Format(time.RFC3339)
		items = append(items, item)
	}
	return items
}

func (s *PostgresStore) ListAuditLogs() []domain.AuditLog {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.ListAuditLogs()
	}
	rows, err := s.pool.Query(ctx, `SELECT id, actor, action, object, result, created_at FROM audit_logs ORDER BY created_at DESC`)
	if err != nil {
		return s.MemoryStore.ListAuditLogs()
	}
	defer rows.Close()
	var items []domain.AuditLog
	for rows.Next() {
		var item domain.AuditLog
		var createdAt time.Time
		if err := rows.Scan(&item.ID, &item.Actor, &item.Action, &item.Object, &item.Result, &createdAt); err != nil {
			return s.MemoryStore.ListAuditLogs()
		}
		item.CreatedAt = createdAt.Format(time.RFC3339)
		items = append(items, item)
	}
	return items
}

type rowScanner interface {
	Scan(dest ...any) error
}

func (s *PostgresStore) Overview() map[string]any {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.Overview()
	}
	count := func(table string) int {
		var value int
		query := fmt.Sprintf("SELECT count(*) FROM %s", table)
		_ = s.pool.QueryRow(ctx, query).Scan(&value)
		return value
	}
	return map[string]any{
		"assets_total":       count("asset_records"),
		"alerts_open":        countWhere(ctx, s.pool, "alert_events", "status <> '已恢复'"),
		"workorders_waiting": countWhere(ctx, s.pool, "workorder_requests", "status IN ('submitted', 'approved', 'executing')"),
		"probe_online":       countWhere(ctx, s.pool, "probe_nodes", "status = 'online'"),
	}
}

func countWhere(ctx context.Context, pool *pgxpool.Pool, table string, predicate string) int {
	var value int
	query := fmt.Sprintf("SELECT count(*) FROM %s WHERE %s", table, predicate)
	_ = pool.QueryRow(ctx, query).Scan(&value)
	return value
}

func (s *PostgresStore) Search(query string) []map[string]any {
	ctx := context.Background()
	if err := s.ensurePool(ctx); err != nil {
		return s.MemoryStore.Search(query)
	}
	like := "%" + query + "%"
	var items []map[string]any
	appendRows := func(kind string, sql string) {
		rows, err := s.pool.Query(ctx, sql, like)
		if err != nil {
			return
		}
		defer rows.Close()
		for rows.Next() {
			var id, title string
			if err := rows.Scan(&id, &title); err == nil {
				items = append(items, map[string]any{"type": kind, "id": id, "title": title})
			}
		}
	}
	appendRows("asset_model", `SELECT id, name FROM asset_models WHERE name ILIKE $1 OR code ILIKE $1 ORDER BY created_at DESC LIMIT 10`)
	appendRows("alert", `SELECT id, title FROM alert_events WHERE title ILIKE $1 OR id ILIKE $1 ORDER BY created_at DESC LIMIT 10`)
	appendRows("workorder", `SELECT id, title FROM workorder_requests WHERE title ILIKE $1 OR id ILIKE $1 ORDER BY created_at DESC LIMIT 10`)
	return items
}

func (s *PostgresStore) getDetectionTask(ctx context.Context, id string) (domain.DetectionTask, bool, error) {
	row := s.pool.QueryRow(ctx, `
		SELECT `+detectionTaskSelectColumns+`
		FROM detection_tasks
		WHERE id = $1
	`, id)
	task, err := scanDetectionTask(row)
	if err == pgx.ErrNoRows {
		return domain.DetectionTask{}, false, nil
	}
	if err != nil {
		return domain.DetectionTask{}, false, err
	}
	return task, true, nil
}

func scanDetectionTask(scanner rowScanner) (domain.DetectionTask, error) {
	var task domain.DetectionTask
	var metadataJSON []byte
	var resultJSON []byte
	var claimedAt sql.NullTime
	var completedAt sql.NullTime
	var createdAt time.Time
	var updatedAt time.Time
	if err := scanner.Scan(
		&task.ID, &task.Type, &task.Target, &task.Probe, &task.Status,
		&task.RelatedAsset, &task.BusinessLine, &task.Environment,
		&task.Protocol, &task.Port, &task.TimeoutSec,
		&metadataJSON, &resultJSON,
		&claimedAt, &completedAt, &task.ClaimedBy,
		&task.LatencyMs, &task.Message, &task.ResultID,
		&createdAt, &updatedAt,
	); err != nil {
		return domain.DetectionTask{}, err
	}
	_ = json.Unmarshal(metadataJSON, &task.Metadata)
	_ = json.Unmarshal(resultJSON, &task.Result)
	if claimedAt.Valid {
		task.ClaimedAt = claimedAt.Time.Format(time.RFC3339)
	}
	if completedAt.Valid {
		task.CompletedAt = completedAt.Time.Format(time.RFC3339)
	}
	task.CreatedAt = createdAt.Format(time.RFC3339)
	task.UpdatedAt = updatedAt.Format(time.RFC3339)
	return task, nil
}

func scanProbeNode(scanner rowScanner) (domain.ProbeNode, error) {
	var probe domain.ProbeNode
	var capabilitiesJSON []byte
	var heartbeatAt *time.Time
	var createdAt time.Time
	var updatedAt time.Time
	if err := scanner.Scan(&probe.ID, &probe.Name, &probe.Region, &capabilitiesJSON, &probe.Status, &heartbeatAt, &createdAt, &updatedAt); err != nil {
		return domain.ProbeNode{}, err
	}
	_ = json.Unmarshal(capabilitiesJSON, &probe.Capabilities)
	probe.NetworkType = "unknown"
	probe.Version = "v1"
	probe.ConnectionStatus = "connected"
	if probe.Status == "offline" || probe.Status == "retired" {
		probe.ConnectionStatus = "disconnected"
	}
	probe.ConfigStatus = "acknowledged"
	probe.RegisteredAt = createdAt.Format(time.RFC3339)
	probe.LastConfigSyncAt = updatedAt.Format(time.RFC3339)
	if heartbeatAt != nil {
		probe.HeartbeatAt = heartbeatAt.Format(time.RFC3339)
	}
	if heartbeatAt != nil && probe.Status != "retired" {
		delay := time.Since(*heartbeatAt)
		if delay >= 5*time.Minute {
			probe.Status = "offline"
			probe.ConnectionStatus = "disconnected"
		} else if delay >= 90*time.Second {
			probe.Status = "degraded"
			probe.ConnectionStatus = "degraded"
		}
	}
	probe.AgentConfig = defaultProbeAgentConfig(probe.Capabilities)
	return probe, nil
}

func probeTokenHash(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}

func scanAlert(scanner rowScanner) (domain.AlertEvent, error) {
	var alert domain.AlertEvent
	var createdAt time.Time
	if err := scanner.Scan(&alert.ID, &alert.Severity, &alert.Title, &alert.Asset, &alert.Owner, &alert.BusinessLine, &alert.Environment, &alert.Status, &alert.Notify, &alert.Workorder, &alert.SourceTaskID, &createdAt); err != nil {
		return domain.AlertEvent{}, err
	}
	alert.Duration = "刚刚"
	alert.CreatedAt = createdAt.Format(time.RFC3339)
	if alert.Workorder == "" {
		alert.Workorder = "-"
	}
	return alert, nil
}

func scanWorkorder(scanner rowScanner) (domain.Workorder, error) {
	var workorder domain.Workorder
	var createdAt time.Time
	var updatedAt time.Time
	if err := scanner.Scan(&workorder.ID, &workorder.Type, &workorder.Title, &workorder.Applicant, &workorder.Assignee, &workorder.Status, &workorder.SLA, &workorder.BusinessLine, &workorder.Environment, &workorder.RelatedObject, &workorder.RelatedAlertID, &createdAt, &updatedAt); err != nil {
		return domain.Workorder{}, err
	}
	workorder.CreatedAt = createdAt.Format(time.RFC3339)
	workorder.UpdatedAt = updatedAt.Format(time.RFC3339)
	return workorder, nil
}

func (s *PostgresStore) createAlertAndMaybeWorkorderPostgres(ctx context.Context, tx pgx.Tx, task domain.DetectionTask) error {
	asset := task.Target
	if task.RelatedAsset != "" && task.RelatedAsset != "-" {
		asset = task.RelatedAsset
	}
	alertID, err := s.nextID(ctx, "ALT", "alert_events")
	if err != nil {
		return err
	}
	alertTitle := task.Target + " 检测失败"
	_, err = tx.Exec(ctx, `
		INSERT INTO alert_events (id, severity, title, asset, owner, business_line, environment, status, notify_status, source_task_id)
		VALUES ($1, 'P1', $2, $3, '平台组', $4, $5, '待认领', '已投递', $6)
	`, alertID, alertTitle, asset, task.BusinessLine, task.Environment, task.ID)
	if err != nil {
		return err
	}
	if err := s.insertAuditNotificationOutbox(ctx, tx, "系统", "探针失败生成告警", alertID, "新告警："+alertTitle, "alerts", "alert.created", map[string]any{"alert_id": alertID, "task_id": task.ID}); err != nil {
		return err
	}

	var autoWorkorder bool
	err = tx.QueryRow(ctx, `
		SELECT EXISTS (
			SELECT 1
			FROM monitoring_strategies
			WHERE enabled = true
			  AND COALESCE((rule->'actions'->>'create_workorder')::boolean, false) = true
		)
	`).Scan(&autoWorkorder)
	if err != nil {
		return err
	}
	if !autoWorkorder {
		return nil
	}

	workorderID, err := s.nextID(ctx, "WO", "workorder_requests")
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `
		INSERT INTO workorder_requests (id, type, title, applicant, assignee, status, sla, related_object, related_alert_id, business_line, environment)
		VALUES ($1, '告警处理', $2, '系统', '待分配', 'submitted', '4h', $3, $3, $4, $5)
	`, workorderID, "处理 "+alertTitle, alertID, task.BusinessLine, task.Environment)
	if err != nil {
		return err
	}
	_, err = tx.Exec(ctx, `UPDATE alert_events SET workorder_id = $2, updated_at = now() WHERE id = $1`, alertID, workorderID)
	if err != nil {
		return err
	}
	if err := s.insertAuditNotificationOutbox(ctx, tx, "系统", "告警自动创建工单", workorderID, "告警已自动创建工单："+workorderID, "workorders", "workorder.created", map[string]any{"alert_id": alertID, "workorder_id": workorderID}); err != nil {
		return err
	}
	return nil
}

func (s *PostgresStore) getAssetModel(ctx context.Context, id string) (domain.AssetModel, bool) {
	if err := s.ensurePool(ctx); err != nil {
		return domain.AssetModel{}, false
	}
	var model domain.AssetModel
	var fieldsJSON []byte
	var createdAt time.Time
	err := s.pool.QueryRow(ctx, `
		SELECT id, name, code, fields, status, created_by, created_at
		FROM asset_models
		WHERE id = $1 OR code = $1
	`, id).Scan(&model.ID, &model.Name, &model.Code, &fieldsJSON, &model.Status, &model.CreatedBy, &createdAt)
	if err == pgx.ErrNoRows {
		return domain.AssetModel{}, false
	}
	if err != nil {
		return domain.AssetModel{}, false
	}
	_ = json.Unmarshal(fieldsJSON, &model.Fields)
	model.PrimaryKey = assetModelPrimaryKey(model)
	model.CreatedAt = createdAt.Format(time.RFC3339)
	return model, true
}

func (s *PostgresStore) writeAuditNotification(ctx context.Context, actor string, action string, object string, title string, producer string, eventType string, payload map[string]any) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return
	}
	defer tx.Rollback(ctx)
	if err := s.insertAuditNotificationOutbox(ctx, tx, actor, action, object, title, producer, eventType, payload); err != nil {
		return
	}
	_ = tx.Commit(ctx)
}

func (s *PostgresStore) insertAuditNotificationOutbox(ctx context.Context, tx pgx.Tx, actor string, action string, object string, title string, producer string, eventType string, payload map[string]any) error {
	payloadJSON, _ := json.Marshal(payload)
	auditID, err := nextID(ctx, tx, "AUD", "audit_logs")
	if err != nil {
		return err
	}
	notificationID, err := nextID(ctx, tx, "NTF", "notifications")
	if err != nil {
		return err
	}
	eventID, err := nextID(ctx, tx, "EVT", "event_outbox")
	if err != nil {
		return err
	}
	if _, err := tx.Exec(ctx, `INSERT INTO audit_logs (id, actor, action, object, result, payload) VALUES ($1, $2, $3, $4, '成功', $5::jsonb)`, auditID, actor, action, object, string(payloadJSON)); err != nil {
		return err
	}
	if _, err := tx.Exec(ctx, `INSERT INTO notifications (id, target, title, payload) VALUES ($1, $2, $3, $4::jsonb)`, notificationID, actor, title, string(payloadJSON)); err != nil {
		return err
	}
	if _, err := tx.Exec(ctx, `INSERT INTO event_outbox (event_id, trace_id, event_type, producer, payload) VALUES ($1, $2, $3, $4, $5::jsonb)`, eventID, "trace-"+eventID, eventType, producer, string(payloadJSON)); err != nil {
		return err
	}
	return nil
}

const postgresSchemaContract = `
asset_models(id, code, name, fields, status, created_by, created_at, updated_at)
asset_records(id, model_id, model_code, fields, owner, environment, business_line, updated_at)
monitoring_strategies(id, name, scope, enabled, version, rule, created_at, updated_at)
detection_tasks(id, type, target, probe, status, related_asset, protocol, port, timeout_seconds, metadata, result, result_id, claimed_at, completed_at, claimed_by_probe_id, latency_ms, message, created_at, updated_at)
alert_events(id, severity, title, asset, status, workorder_id, detection_task_id, created_at)
workorder_requests(id, type, title, applicant, assignee, status, related_object, created_at, updated_at)
notifications(id, target, title, status, payload, created_at)
audit_logs(id, actor, action, object, result, payload, created_at)
event_outbox(event_id, trace_id, event_type, producer, payload, status, created_at)
`
