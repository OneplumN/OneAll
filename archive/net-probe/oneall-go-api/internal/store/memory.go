package store

import (
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"oneall-go-api/internal/domain"
)

type MemoryStore struct {
	mu              sync.Mutex
	assetSeq        int
	recordSeq       int
	strategySeq     int
	detectionSeq    int
	alertSeq        int
	probeSeq        int
	workorderSeq    int
	notificationSeq int
	auditSeq        int
	workorders      []domain.Workorder
	assetModels     []domain.AssetModel
	assetRecords    []domain.AssetRecord
	strategies      []domain.Strategy
	detectionTasks  []domain.DetectionTask
	alerts          []domain.AlertEvent
	probes          []domain.ProbeNode
	syncRuns        []map[string]any
	notifications   []domain.Notification
	auditLogs       []domain.AuditLog
}

func NewMemoryStore() *MemoryStore {
	now := time.Now().UTC().Format(time.RFC3339)
	return &MemoryStore{
		assetSeq:        1,
		recordSeq:       1,
		strategySeq:     4,
		detectionSeq:    10,
		alertSeq:        5,
		probeSeq:        4,
		workorderSeq:    16,
		notificationSeq: 1,
		auditSeq:        1,
		assetModels:     []domain.AssetModel{},
		assetRecords:    []domain.AssetRecord{},
		detectionTasks:  []domain.DetectionTask{},
		notifications:   []domain.Notification{},
		auditLogs:       []domain.AuditLog{},
		strategies:      []domain.Strategy{},
		syncRuns:        []map[string]any{},
		probes: []domain.ProbeNode{
			{
				ID:                 "PRB-0001",
				Name:               "probe-sh-01",
				Region:             "上海",
				NetworkType:        "公网出口",
				IPAddress:          "10.10.1.21",
				Capabilities:       []string{"HTTP", "TCP", "DNS"},
				Status:             "online",
				HeartbeatAt:        now,
				Version:            "v18",
				ActiveTasks:        0,
				SuccessRate:        99.3,
				AvgLatencyMs:       41,
				QueueDepth:         0,
				Executions:         1286,
				Failed:             9,
				CPUUsage:           32,
				MemoryUsageMB:      612,
				MemoryUsagePct:     41,
				LoadAvg:            0.72,
				Uptime:             "18 天",
				ConnectionStatus:   "connected",
				ConfigStatus:       "acknowledged",
				GatewayURL:         "https://gateway.oneall.internal/probes/PRB-0001",
				BootstrapTokenHint: "probe_token…",
				RegisteredAt:       now,
				LastConfigSyncAt:   now,
				AgentConfig:        defaultProbeAgentConfig([]string{"HTTP", "TCP", "DNS"}),
				Token:              "probe_token_sh_01",
			},
		},
		alerts: []domain.AlertEvent{
			{
				ID:           "ALT-0001",
				Severity:     "P0",
				Title:        "api.oneall.internal HTTP 检测连续超时",
				Asset:        "api.oneall.internal",
				Duration:     "18m",
				Owner:        "张三",
				BusinessLine: "支付业务",
				Environment:  "prod",
				Notify:       "已投递",
				Workorder:    "WO-0014",
				Status:       "处理中",
				CreatedAt:    now,
			},
			{
				ID:           "ALT-0002",
				Severity:     "P1",
				Title:        "www.oneall.internal 证书 7 天后过期",
				Asset:        "www.oneall.internal",
				Duration:     "2h",
				Owner:        "李四",
				BusinessLine: "增长业务",
				Environment:  "prod",
				Notify:       "待重试",
				Workorder:    "-",
				Status:       "待认领",
				CreatedAt:    now,
			},
		},
		workorders: []domain.Workorder{
			{
				ID:             "WO-0014",
				Type:           "拨测监控申请",
				Title:          "新增 api.oneall.internal HTTP 监控",
				Applicant:      "张三",
				Assignee:       "李四",
				Status:         "submitted",
				SLA:            "3h 20m",
				BusinessLine:   "支付业务",
				Environment:    "prod",
				RelatedObject:  "ALT-0001",
				RelatedAlertID: "ALT-0001",
				CreatedAt:      now,
				UpdatedAt:      now,
			},
			{
				ID:             "WO-0015",
				Type:           "告警处理",
				Title:          "pay DNS 解析异常处理",
				Applicant:      "系统",
				Assignee:       "王五",
				Status:         "executing",
				SLA:            "42m",
				BusinessLine:   "支付业务",
				Environment:    "prod",
				RelatedObject:  "ALT-0003",
				RelatedAlertID: "ALT-0003",
				CreatedAt:      now,
				UpdatedAt:      now,
			},
		},
	}
}

func (s *MemoryStore) ListAssetModels() []domain.AssetModel {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.AssetModel(nil), s.assetModels...)
}

func (s *MemoryStore) CreateAssetModel(input domain.AssetModel, actor string) (domain.AssetModel, []string) {
	if errs := domain.ValidateAssetFields(input.Fields); len(errs) > 0 {
		return domain.AssetModel{}, errs
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	model := domain.AssetModel{
		ID:         fmt.Sprintf("MDL-%04d", s.assetSeq),
		Name:       input.Name,
		Code:       input.Code,
		Fields:     input.Fields,
		PrimaryKey: assetModelPrimaryKey(input),
		Status:     "active",
		CreatedBy:  actor,
		CreatedAt:  time.Now().UTC().Format(time.RFC3339),
	}
	s.assetSeq++
	s.assetModels = append([]domain.AssetModel{model}, s.assetModels...)
	s.recordAuditLocked(actor, "创建资产模型", model.ID)
	s.recordNotificationLocked(actor, "资产模型已创建："+model.Name)
	return model, nil
}

func (s *MemoryStore) UpdateAssetModel(id string, input domain.AssetModel, actor string) (domain.AssetModel, bool, []string) {
	if errs := domain.ValidateAssetFields(input.Fields); len(errs) > 0 && input.Fields != nil {
		return domain.AssetModel{}, true, errs
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	for index, model := range s.assetModels {
		if model.ID != id && model.Code != id {
			continue
		}
		if input.Name != "" {
			model.Name = input.Name
		}
		if len(input.Fields) > 0 {
			model.Fields = input.Fields
		}
		if input.PrimaryKey != "" {
			model.PrimaryKey = input.PrimaryKey
		}
		if !assetModelHasField(model, model.PrimaryKey) {
			model.PrimaryKey = assetModelPrimaryKey(model)
		}
		if input.Status != "" {
			model.Status = input.Status
		}
		s.assetModels[index] = model
		s.recordAuditLocked(actor, "更新资产模型", model.ID)
		s.recordNotificationLocked(actor, "资产模型已更新："+model.Name)
		return model, true, nil
	}
	return domain.AssetModel{}, false, nil
}

func assetModelPrimaryKey(model domain.AssetModel) string {
	if model.PrimaryKey != "" {
		return model.PrimaryKey
	}
	if len(model.Fields) == 0 {
		return ""
	}
	return model.Fields[0].Key
}

func assetModelHasField(model domain.AssetModel, key string) bool {
	if key == "" {
		return false
	}
	for _, field := range model.Fields {
		if field.Key == key {
			return true
		}
	}
	return false
}

func (s *MemoryStore) getAssetModelLocked(id string) (domain.AssetModel, bool) {
	for _, model := range s.assetModels {
		if model.ID == id || model.Code == id {
			return model, true
		}
	}
	return domain.AssetModel{}, false
}

func (s *MemoryStore) BatchAssetRecords(modelID string, records []domain.AssetRecord, actor string) ([]domain.AssetRecord, []string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	model, found := s.getAssetModelLocked(modelID)
	if !found {
		return nil, []string{"资产模型不存在"}, false
	}
	if len(records) == 0 {
		return nil, []string{"records 必须至少包含一条记录"}, true
	}

	updated := make([]domain.AssetRecord, 0, len(records))
	for _, record := range records {
		if errs := domain.ValidateAssetRecord(model, record); len(errs) > 0 {
			return nil, errs, true
		}
		item := domain.AssetRecord{}
		for key, value := range record {
			item[key] = value
		}
		item["id"] = fmt.Sprintf("AST-%04d", s.recordSeq)
		item["model_id"] = model.ID
		item["model_code"] = model.Code
		item["updated_at"] = time.Now().UTC().Format(time.RFC3339)
		s.recordSeq++
		s.assetRecords = append([]domain.AssetRecord{item}, s.assetRecords...)
		updated = append(updated, item)
	}
	s.recordAuditLocked(actor, "批量写入资产记录", model.ID)
	s.recordNotificationLocked(actor, "资产记录已更新："+model.Name)
	return updated, nil, true
}

func (s *MemoryStore) ListAssetRecords(modelID string) []domain.AssetRecord {
	s.mu.Lock()
	defer s.mu.Unlock()

	var items []domain.AssetRecord
	for _, record := range s.assetRecords {
		if modelID == "" || record["model_id"] == modelID || record["model_code"] == modelID {
			items = append(items, record)
		}
	}
	return items
}

func (s *MemoryStore) PreviewAssetSync(modelID string, input map[string]any) (map[string]any, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	model, found := s.getAssetModelLocked(modelID)
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
	sample := domain.AssetRecord{"name": model.Code + "-sample", "owner": owner, "environment": "prod"}
	exists := false
	for _, record := range s.assetRecords {
		if record["model_id"] == model.ID {
			exists = true
			break
		}
	}
	creates := 1
	updates := 0
	if exists {
		creates = 0
		updates = 1
	}
	return map[string]any{"model_id": model.ID, "source": source, "total": 1, "creates": creates, "updates": updates, "deletes": 0, "sample": sample, "samples": []domain.AssetRecord{sample}}, true
}

func (s *MemoryStore) RunAssetSync(modelID string, input map[string]any, actor string) (map[string]any, bool, []string) {
	preview, found := s.PreviewAssetSync(modelID, input)
	if !found {
		return nil, false, nil
	}
	sample, _ := preview["sample"].(domain.AssetRecord)
	records, errs, _ := s.BatchAssetRecords(modelID, []domain.AssetRecord{sample}, actor)
	if len(errs) > 0 {
		return nil, true, errs
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	run := map[string]any{
		"event_id":   fmt.Sprintf("EVT-%04d", len(s.syncRuns)+1),
		"event_type": "asset.sync.completed",
		"producer":   "assets",
		"payload":    map[string]any{"model_id": modelID, "source": preview["source"], "count": len(records)},
		"created_at": time.Now().UTC().Format(time.RFC3339),
	}
	s.syncRuns = append([]map[string]any{run}, s.syncRuns...)
	preview["run_id"] = run["event_id"]
	preview["records"] = records
	preview["count"] = len(records)
	return preview, true, nil
}

func (s *MemoryStore) ListSyncRuns() []map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.syncRuns == nil {
		return []map[string]any{}
	}
	return append([]map[string]any(nil), s.syncRuns...)
}

func (s *MemoryStore) ValidateCMDBDomain(domainName string) map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, record := range s.assetRecords {
		if record["name"] == domainName || record["domain"] == domainName || record["target"] == domainName {
			return map[string]any{"domain": domainName, "matched": true, "model_id": record["model_id"], "asset_id": record["id"], "missing_fields": []string{}, "recommendation": "可关联资产并进入监控策略"}
		}
	}
	return map[string]any{"domain": domainName, "matched": false, "model_id": nil, "asset_id": nil, "missing_fields": []string{"owner", "environment"}, "recommendation": "未命中资产记录，建议先创建模型并同步数据"}
}

func (s *MemoryStore) ListWorkorders(role string) []domain.Workorder {
	s.mu.Lock()
	defer s.mu.Unlock()

	items := append([]domain.Workorder(nil), s.workorders...)
	if role != "Approver" {
		return items
	}

	var scoped []domain.Workorder
	for _, item := range items {
		if item.Status == "submitted" || item.Status == "approved" {
			scoped = append(scoped, item)
		}
	}
	return scoped
}

func (s *MemoryStore) Overview() map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	waiting := 0
	for _, item := range s.workorders {
		if item.Status == "submitted" || item.Status == "approved" || item.Status == "executing" {
			waiting++
		}
	}
	online := 0
	for _, probe := range s.probes {
		if probe.Status == "online" {
			online++
		}
	}
	return map[string]any{
		"unresolved_alerts":  len(s.alerts),
		"p0":                 countSeverity(s.alerts, "P0"),
		"asset_models":       len(s.assetModels),
		"workorders_waiting": waiting,
		"probes_online":      online,
	}
}

func (s *MemoryStore) Search(query string) []map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	var items []map[string]any
	for _, model := range s.assetModels {
		if query == "" || containsText(model.Name, query) || containsText(model.Code, query) {
			items = append(items, map[string]any{"type": "asset_model", "id": model.ID, "title": model.Name})
		}
	}
	for _, alert := range s.alerts {
		if query == "" || containsText(alert.Title, query) || containsText(alert.ID, query) {
			items = append(items, map[string]any{"type": "alert", "id": alert.ID, "title": alert.Title})
		}
	}
	for _, workorder := range s.workorders {
		if query == "" || containsText(workorder.Title, query) || containsText(workorder.ID, query) {
			items = append(items, map[string]any{"type": "workorder", "id": workorder.ID, "title": workorder.Title})
		}
	}
	return items
}

func (s *MemoryStore) GetWorkorder(id string) (domain.Workorder, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, item := range s.workorders {
		if item.ID == id {
			return item, true
		}
	}
	return domain.Workorder{}, false
}

func (s *MemoryStore) CreateWorkorder(input domain.Workorder, actor string) domain.Workorder {
	s.mu.Lock()
	defer s.mu.Unlock()
	workorder := domain.Workorder{
		ID:             fmt.Sprintf("WO-%04d", s.workorderSeq),
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
		CreatedAt:      time.Now().UTC().Format(time.RFC3339),
		UpdatedAt:      time.Now().UTC().Format(time.RFC3339),
	}
	if workorder.RelatedAlertID == "" && strings.HasPrefix(workorder.RelatedObject, "ALT-") {
		workorder.RelatedAlertID = workorder.RelatedObject
	}
	s.workorderSeq++
	s.workorders = append([]domain.Workorder{workorder}, s.workorders...)
	s.recordAuditLocked(actor, "创建工单", workorder.ID)
	s.recordNotificationLocked(actor, "工单已创建："+workorder.ID)
	return workorder
}

func (s *MemoryStore) TransitionWorkorder(id string, nextStatus string) (domain.Workorder, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for index, item := range s.workorders {
		if item.ID != id {
			continue
		}
		updated, err := domain.TransitionWorkorder(item, nextStatus)
		if err != nil {
			return item, true, err
		}
		s.workorders[index] = updated
		s.recordAuditLocked("Approver", "工单流转到 "+nextStatus, id)
		s.recordNotificationLocked("OpsAdmin", "工单状态已更新："+id)
		return updated, true, nil
	}
	return domain.Workorder{}, false, nil
}

func (s *MemoryStore) BatchWorkorders(ids []string, action string, actor string) ([]domain.Workorder, string) {
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

func (s *MemoryStore) CreateStrategy(input domain.Strategy, actor string) (domain.Strategy, []string) {
	if errs := domain.ValidateAlertRule(input.Rule); len(errs) > 0 {
		return domain.Strategy{}, errs
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	strategy := domain.Strategy{
		ID:        fmt.Sprintf("STR-%04d", s.strategySeq),
		Name:      input.Name,
		Scope:     input.Rule.Scope.AssetModel,
		Enabled:   true,
		Version:   "v1",
		Rule:      input.Rule,
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}
	s.strategySeq++
	s.strategies = append([]domain.Strategy{strategy}, s.strategies...)
	s.recordAuditLocked(actor, "创建监控策略", strategy.ID)
	s.recordNotificationLocked(actor, "监控策略已创建："+strategy.Name)
	return strategy, nil
}

func (s *MemoryStore) ListStrategies() []domain.Strategy {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.Strategy(nil), s.strategies...)
}

func (s *MemoryStore) BatchStrategies(ids []string, action string, actor string) ([]domain.Strategy, string) {
	if action != "enable" && action != "disable" {
		return nil, "不支持的策略批量动作"
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	var updated []domain.Strategy
	for index, item := range s.strategies {
		for _, id := range ids {
			if item.ID == id {
				s.strategies[index].Enabled = action == "enable"
				updated = append(updated, s.strategies[index])
				s.recordAuditLocked(actor, "批量更新策略", id)
			}
		}
	}
	return updated, ""
}

func (s *MemoryStore) CreateDetection(input domain.DetectionTask, actor string) domain.DetectionTask {
	s.mu.Lock()
	defer s.mu.Unlock()

	task := domain.DetectionTask{
		ID:           fmt.Sprintf("DET-%04d", s.detectionSeq),
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
		CreatedAt:    time.Now().UTC().Format(time.RFC3339),
		UpdatedAt:    time.Now().UTC().Format(time.RFC3339),
	}
	if task.TimeoutSec <= 0 {
		task.TimeoutSec = 10
	}
	s.detectionSeq++
	s.detectionTasks = append([]domain.DetectionTask{task}, s.detectionTasks...)
	s.recordAuditLocked(actor, "创建一次性检测", task.ID)
	s.recordNotificationLocked(actor, "检测任务已创建："+task.ID)
	return task
}

func (s *MemoryStore) ListDetectionTasks() []domain.DetectionTask {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.DetectionTask(nil), s.detectionTasks...)
}

func (s *MemoryStore) GetDetectionTask(id string) (domain.DetectionTask, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, task := range s.detectionTasks {
		if task.ID == id {
			return task, true
		}
	}
	return domain.DetectionTask{}, false
}

func (s *MemoryStore) ClaimProbeTasks(probeID string, limit int) []domain.DetectionTask {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.requeueExpiredDetectionTasksLocked(time.Now().UTC())
	if limit <= 0 {
		limit = 5
	}
	if limit > 10 {
		limit = 10
	}
	probe, probeFound := s.findProbeLocked(probeID)
	probeKey := probeID
	if probeFound {
		probeKey = probe.ID
	}
	claimedAt := time.Now().UTC().Format(time.RFC3339)
	claimed := []domain.DetectionTask{}
	for index, task := range s.detectionTasks {
		if task.Status == "pending" {
			if probeFound && task.Probe != "" && task.Probe != probe.Name && task.Probe != probe.ID {
				continue
			}
			task.Status = "running"
			task.ClaimedAt = claimedAt
			task.ClaimedBy = probeKey
			task.Message = "探针已领取，等待回传"
			task.UpdatedAt = claimedAt
			s.detectionTasks[index] = task
			claimed = append(claimed, task)
		}
		if len(claimed) == limit {
			break
		}
	}
	if len(claimed) > 0 {
		for index, item := range s.probes {
			if item.ID == probeKey || item.Name == probeID {
				item.Status = "online"
				item.ConnectionStatus = "connected"
				item.HeartbeatAt = claimedAt
				item.ActiveTasks += len(claimed)
				if item.QueueDepth >= len(claimed) {
					item.QueueDepth -= len(claimed)
				}
				s.probes[index] = item
				break
			}
		}
		s.recordAuditLocked("probe", "探针领取任务", fmt.Sprintf("%s x%d", probeKey, len(claimed)))
	}
	return claimed
}

func (s *MemoryStore) SubmitProbeResult(taskID string, result map[string]any, actor string) (domain.DetectionTask, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for index, task := range s.detectionTasks {
		if task.ID != taskID {
			continue
		}
		if isCompletedDetectionStatus(task.Status) && task.CompletedAt != "" {
			return task, true
		}
		success, _ := result["success"].(bool)
		if status, ok := result["status"].(string); ok {
			success = status == "success"
		}
		task.Status = "failed"
		if success {
			task.Status = "success"
		}
		task.Result = result
		task.CompletedAt = time.Now().UTC().Format(time.RFC3339)
		if resultID, ok := result["result_id"].(string); ok && resultID != "" {
			task.ResultID = resultID
		}
		if probeID, ok := result["probe_id"].(string); ok && probeID != "" {
			task.ClaimedBy = probeID
		}
		if latency, ok := numericInt(result["latency_ms"]); ok {
			task.LatencyMs = latency
		} else if latency, ok := numericInt(result["response_time_ms"]); ok {
			task.LatencyMs = latency
		}
		if message, ok := result["message"].(string); ok {
			task.Message = message
		}
		task.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
		s.detectionTasks[index] = task
		s.updateProbeAfterResultLocked(task, success)
		s.recordAuditLocked(actor, "回传探针结果", taskID)
		s.recordNotificationLocked("OpsAdmin", "探针结果已回传："+taskID)
		if !success {
			s.createAlertAndMaybeWorkorderLocked(task)
		}
		return task, true
	}
	return domain.DetectionTask{}, false
}

func (s *MemoryStore) requeueExpiredDetectionTasksLocked(now time.Time) {
	for index, task := range s.detectionTasks {
		if task.Status != "running" {
			continue
		}
		claimedAt, ok := parseProbeTimestamp(task.ClaimedAt)
		if !ok {
			claimedAt, ok = parseProbeTimestamp(task.UpdatedAt)
		}
		if !ok {
			continue
		}
		timeout := time.Duration(maxInt(task.TimeoutSec*3, 120)) * time.Second
		if now.Sub(claimedAt) < timeout {
			continue
		}
		task.Status = "pending"
		task.ClaimedAt = ""
		task.ClaimedBy = ""
		task.Message = "探针执行超时，任务已重新入队"
		task.UpdatedAt = now.Format(time.RFC3339)
		s.detectionTasks[index] = task
		s.recordAuditLocked("system", "探针任务超时回收", task.ID)
	}
}

func isCompletedDetectionStatus(status string) bool {
	return status == "success" || status == "failed" || status == "canceled"
}

func (s *MemoryStore) findProbeLocked(idOrName string) (domain.ProbeNode, bool) {
	for _, probe := range s.probes {
		if probe.ID == idOrName || probe.Name == idOrName {
			return probe, true
		}
	}
	return domain.ProbeNode{}, false
}

func (s *MemoryStore) updateProbeAfterResultLocked(task domain.DetectionTask, success bool) {
	for index, probe := range s.probes {
		if task.ClaimedBy != "" && probe.ID != task.ClaimedBy && probe.Name != task.ClaimedBy {
			continue
		}
		if task.ClaimedBy == "" && task.Probe != "" && probe.ID != task.Probe && probe.Name != task.Probe {
			continue
		}
		probe.ActiveTasks = maxInt(0, probe.ActiveTasks-1)
		probe.Executions++
		if !success {
			probe.Failed++
		}
		if task.LatencyMs > 0 {
			if probe.AvgLatencyMs <= 0 {
				probe.AvgLatencyMs = task.LatencyMs
			} else {
				probe.AvgLatencyMs = (probe.AvgLatencyMs + task.LatencyMs) / 2
			}
		}
		if probe.Executions > 0 {
			probe.SuccessRate = roundMetric(float64(probe.Executions-probe.Failed) * 100 / float64(probe.Executions))
		}
		probe.HeartbeatAt = time.Now().UTC().Format(time.RFC3339)
		probe.ConnectionStatus = "connected"
		s.probes[index] = probe
		return
	}
}

func (s *MemoryStore) ListAlerts() []domain.AlertEvent {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.AlertEvent(nil), s.alerts...)
}

func (s *MemoryStore) GetAlert(id string) (domain.AlertEvent, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, alert := range s.alerts {
		if alert.ID == id {
			return alert, true
		}
	}
	return domain.AlertEvent{}, false
}

func (s *MemoryStore) CloseAlerts(ids []string, actor string) []domain.AlertEvent {
	s.mu.Lock()
	defer s.mu.Unlock()
	var updated []domain.AlertEvent
	for index, item := range s.alerts {
		for _, id := range ids {
			if item.ID == id {
				s.alerts[index].Status = "已恢复"
				updated = append(updated, s.alerts[index])
				s.recordAuditLocked(actor, "关闭告警", id)
				s.recordNotificationLocked(actor, "告警已关闭："+id)
			}
		}
	}
	return updated
}

func (s *MemoryStore) RegisterProbe(input domain.ProbeNode) domain.ProbeNode {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC().Format(time.RFC3339)
	probe := domain.ProbeNode{
		ID:               fmt.Sprintf("PRB-%04d", s.probeSeq),
		Name:             valueOrDefault(input.Name, fmt.Sprintf("probe-%04d", s.probeSeq)),
		Region:           valueOrDefault(input.Region, "unknown"),
		NetworkType:      valueOrDefault(input.NetworkType, "unknown"),
		IPAddress:        input.IPAddress,
		Capabilities:     input.Capabilities,
		Status:           "online",
		HeartbeatAt:      now,
		Version:          valueOrDefault(input.Version, "v1"),
		ConnectionStatus: "connected",
		ConfigStatus:     "acknowledged",
		RegisteredAt:     now,
		LastConfigSyncAt: now,
		Token:            fmt.Sprintf("probe_token_%d", time.Now().UnixNano()),
	}
	if len(probe.Capabilities) == 0 {
		probe.Capabilities = []string{"HTTP"}
	}
	probe.BootstrapTokenHint = probeTokenHint(probe.Token)
	probe.GatewayURL = "https://gateway.oneall.internal/probes/" + probe.ID
	probe.AgentConfig = defaultProbeAgentConfig(probe.Capabilities)
	probe = s.enrichProbeLocked(probe)
	s.probeSeq++
	s.probes = append([]domain.ProbeNode{probe}, s.probes...)
	s.recordAuditLocked("probe-bootstrap", "注册探针", probe.ID)
	s.recordNotificationLocked("OpsAdmin", "探针已注册："+probe.Name)
	return probe
}

func (s *MemoryStore) ListProbes() []domain.ProbeNode {
	s.mu.Lock()
	defer s.mu.Unlock()
	items := append([]domain.ProbeNode(nil), s.probes...)
	for index := range items {
		items[index] = sanitizeProbe(s.enrichProbeLocked(items[index]))
	}
	return items
}

func (s *MemoryStore) ListProbeHealth(hours int, intervalMinutes int) map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	if hours <= 0 {
		hours = 6
	}
	if intervalMinutes <= 0 {
		intervalMinutes = 10
	}
	items := make([]map[string]any, 0, len(s.probes))
	for _, item := range s.probes {
		probe := sanitizeProbe(s.enrichProbeLocked(item))
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
		"items": items,
		"window": map[string]any{
			"hours":            hours,
			"interval_minutes": intervalMinutes,
		},
	}
}

func (s *MemoryStore) GetProbeRuntime(id string) (map[string]any, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, probe := range s.probes {
		if probe.ID == id || probe.Name == id {
			probe = sanitizeProbe(s.enrichProbeLocked(probe))
			pending, running, executed, failed, avgLatency := s.probeTaskStatsLocked(probe)
			return map[string]any{
				"probe":                   probe,
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
					"pending":     pending,
					"running":     running,
					"active":      probe.ActiveTasks,
					"queue_depth": probe.QueueDepth,
					"executed":    executed,
					"failed":      failed,
				},
				"resource_metrics": map[string]any{
					"cpu_usage":        probe.CPUUsage,
					"memory_usage_mb":  probe.MemoryUsageMB,
					"memory_usage_pct": probe.MemoryUsagePct,
					"load_avg":         probe.LoadAvg,
					"avg_latency_ms":   avgLatency,
				},
			}, true
		}
	}
	return nil, false
}

func (s *MemoryStore) HeartbeatProbe(id string, input domain.ProbeNode, actor string) (domain.ProbeNode, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UTC().Format(time.RFC3339)
	for index, probe := range s.probes {
		if probe.ID != id && probe.Name != id {
			continue
		}
		if len(input.Capabilities) > 0 {
			probe.Capabilities = input.Capabilities
		}
		if input.IPAddress != "" {
			probe.IPAddress = input.IPAddress
		}
		if input.Version != "" {
			probe.Version = input.Version
		}
		if input.CPUUsage > 0 {
			probe.CPUUsage = input.CPUUsage
		}
		if input.MemoryUsageMB > 0 {
			probe.MemoryUsageMB = input.MemoryUsageMB
		}
		if input.MemoryUsagePct > 0 {
			probe.MemoryUsagePct = input.MemoryUsagePct
		}
		if input.LoadAvg > 0 {
			probe.LoadAvg = input.LoadAvg
		}
		if input.Uptime != "" {
			probe.Uptime = input.Uptime
		}
		probe.Status = "online"
		probe.ConnectionStatus = "connected"
		probe.HeartbeatAt = now
		s.probes[index] = probe
		s.recordAuditLocked(actor, "探针心跳", probe.ID)
		return sanitizeProbe(s.enrichProbeLocked(probe)), true
	}
	return domain.ProbeNode{}, false
}

func (s *MemoryStore) ValidateProbeToken(id string, token string) bool {
	if id == "" || token == "" {
		return false
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, probe := range s.probes {
		if (probe.ID == id || probe.Name == id) && probe.Token == token {
			return true
		}
	}
	return false
}

func (s *MemoryStore) ListProbeMetricsHistory(id string, hours int, intervalMinutes int) (map[string]any, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if hours <= 0 {
		hours = 6
	}
	if intervalMinutes <= 0 {
		intervalMinutes = 60
	}
	if intervalMinutes > hours*60 {
		intervalMinutes = hours * 60
	}
	for _, item := range s.probes {
		if item.ID != id && item.Name != id {
			continue
		}
		probe := s.enrichProbeLocked(item)
		pointCount := hours * 60 / intervalMinutes
		if pointCount < 4 {
			pointCount = 4
		}
		if pointCount > 48 {
			pointCount = 48
		}
		now := time.Now().UTC()
		points := make([]map[string]any, 0, pointCount)
		for index := pointCount - 1; index >= 0; index-- {
			timestamp := now.Add(-time.Duration(index*intervalMinutes) * time.Minute)
			offset := float64((pointCount-index)%6) * 1.7
			points = append(points, map[string]any{
				"timestamp":        timestamp.Format(time.RFC3339),
				"cpu_usage":        roundMetric(probe.CPUUsage + offset),
				"memory_usage_mb":  probe.MemoryUsageMB + (pointCount-index)*2,
				"memory_usage_pct": roundMetric(probe.MemoryUsagePct + offset/2),
				"queue_depth":      probe.QueueDepth,
				"active_workers":   probe.ActiveTasks,
				"tasks_executed":   probe.Executions + pointCount - index,
				"heartbeats_sent":  pointCount - index,
			})
		}
		from := ""
		if len(points) > 0 {
			from, _ = points[0]["timestamp"].(string)
		}
		return map[string]any{
			"probe_id": probe.ID,
			"name":     probe.Name,
			"from":     from,
			"to":       now.Format(time.RFC3339),
			"points":   points,
			"window": map[string]any{
				"hours":            hours,
				"interval_minutes": intervalMinutes,
			},
		}, true
	}
	return nil, false
}

func (s *MemoryStore) ListProbeConfigVersions(id string) ([]map[string]any, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, probe := range s.probes {
		if probe.ID == id || probe.Name == id {
			probe = s.enrichProbeLocked(probe)
			current := probeVersionNumber(probe.Version)
			createdAt := valueOrDefault(probe.LastConfigSyncAt, probe.HeartbeatAt)
			items := []map[string]any{{
				"id":              fmt.Sprintf("%s-v%d", probe.ID, current),
				"probe_id":        probe.ID,
				"version":         current,
				"version_label":   fmt.Sprintf("v%d", current),
				"status":          probe.ConfigStatus,
				"content_hash":    fmt.Sprintf("cfg-%s-v%d", probe.ID, current),
				"checksum":        fmt.Sprintf("cfg-%s-v%d", probe.ID, current),
				"created_at":      createdAt,
				"published_at":    createdAt,
				"acknowledged_at": createdAt,
				"created_by":      "OpsAdmin",
				"config":          probe.AgentConfig,
			}}
			if current > 1 {
				items = append(items, map[string]any{
					"id":            fmt.Sprintf("%s-v%d", probe.ID, current-1),
					"probe_id":      probe.ID,
					"version":       current - 1,
					"version_label": fmt.Sprintf("v%d", current-1),
					"status":        "superseded",
					"content_hash":  fmt.Sprintf("cfg-%s-v%d", probe.ID, current-1),
					"checksum":      fmt.Sprintf("cfg-%s-v%d", probe.ID, current-1),
					"created_at":    probe.RegisteredAt,
					"published_at":  probe.RegisteredAt,
					"created_by":    "OpsAdmin",
					"config":        probe.AgentConfig,
				})
			}
			return items, true
		}
	}
	return nil, false
}

func (s *MemoryStore) RefreshProbeConfig(id string, actor string) (domain.ProbeNode, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for index, probe := range s.probes {
		if probe.ID != id && probe.Name != id {
			continue
		}
		version := probeVersionNumber(probe.Version) + 1
		probe.Version = fmt.Sprintf("v%d", version)
		probe.ConfigStatus = "acknowledged"
		probe.LastConfigSyncAt = time.Now().UTC().Format(time.RFC3339)
		probe.AgentConfig = defaultProbeAgentConfig(probe.Capabilities)
		s.probes[index] = probe
		s.recordAuditLocked(actor, "刷新探针配置", probe.ID)
		s.recordNotificationLocked(actor, "探针配置已刷新："+probe.Name)
		return sanitizeProbe(s.enrichProbeLocked(probe)), true
	}
	return domain.ProbeNode{}, false
}

func (s *MemoryStore) RollbackProbeConfig(id string, version int, actor string) (domain.ProbeNode, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if version <= 0 {
		version = 1
	}
	for index, probe := range s.probes {
		if probe.ID != id && probe.Name != id {
			continue
		}
		probe.Version = fmt.Sprintf("v%d", version)
		probe.ConfigStatus = "acknowledged"
		probe.LastConfigSyncAt = time.Now().UTC().Format(time.RFC3339)
		probe.AgentConfig = defaultProbeAgentConfig(probe.Capabilities)
		s.probes[index] = probe
		s.recordAuditLocked(actor, "回滚探针配置", fmt.Sprintf("%s@v%d", probe.ID, version))
		s.recordNotificationLocked(actor, "探针配置已回滚："+probe.Name)
		return sanitizeProbe(s.enrichProbeLocked(probe)), true
	}
	return domain.ProbeNode{}, false
}

func (s *MemoryStore) RetireProbe(id string, actor string) (domain.ProbeNode, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for index, probe := range s.probes {
		if probe.ID != id && probe.Name != id {
			continue
		}
		probe.Status = "retired"
		probe.ConnectionStatus = "disconnected"
		probe.ActiveTasks = 0
		probe.QueueDepth = 0
		s.probes[index] = probe
		s.recordAuditLocked(actor, "退役探针", probe.ID)
		s.recordNotificationLocked(actor, "探针已退役："+probe.Name)
		return sanitizeProbe(s.enrichProbeLocked(probe)), true
	}
	return domain.ProbeNode{}, false
}

func (s *MemoryStore) ListNotifications() []domain.Notification {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.Notification(nil), s.notifications...)
}

func (s *MemoryStore) ListAuditLogs() []domain.AuditLog {
	s.mu.Lock()
	defer s.mu.Unlock()
	return append([]domain.AuditLog(nil), s.auditLogs...)
}

func (s *MemoryStore) createAlertAndMaybeWorkorderLocked(task domain.DetectionTask) {
	asset := task.Target
	if task.RelatedAsset != "" && task.RelatedAsset != "-" {
		asset = task.RelatedAsset
	}
	alert := domain.AlertEvent{
		ID:           fmt.Sprintf("ALT-%04d", s.alertSeq),
		Severity:     "P1",
		Title:        task.Target + " 检测失败",
		Asset:        asset,
		Duration:     "刚刚",
		Owner:        "平台组",
		BusinessLine: task.BusinessLine,
		Environment:  task.Environment,
		Notify:       "已投递",
		Workorder:    "-",
		Status:       "待认领",
		SourceTaskID: task.ID,
		CreatedAt:    time.Now().UTC().Format(time.RFC3339),
	}
	s.alertSeq++
	s.alerts = append([]domain.AlertEvent{alert}, s.alerts...)
	s.recordNotificationLocked("OpsAdmin", "新告警："+alert.Title)

	autoWorkorder := false
	for _, strategy := range s.strategies {
		if strategy.Enabled && strategy.Rule.Actions.CreateWorkorder {
			autoWorkorder = true
			break
		}
	}
	if !autoWorkorder {
		return
	}

	workorder := domain.Workorder{
		ID:             fmt.Sprintf("WO-%04d", s.workorderSeq),
		Type:           "告警处理",
		Title:          "处理 " + alert.Title,
		Applicant:      "系统",
		Assignee:       "待分配",
		Status:         "submitted",
		SLA:            "4h",
		BusinessLine:   alert.BusinessLine,
		Environment:    alert.Environment,
		RelatedObject:  alert.ID,
		RelatedAlertID: alert.ID,
		CreatedAt:      time.Now().UTC().Format(time.RFC3339),
		UpdatedAt:      time.Now().UTC().Format(time.RFC3339),
	}
	s.workorderSeq++
	s.workorders = append([]domain.Workorder{workorder}, s.workorders...)
	s.alerts[0].Workorder = workorder.ID
	s.recordAuditLocked("系统", "告警自动创建工单", workorder.ID)
	s.recordNotificationLocked("OpsAdmin", "告警已自动创建工单："+workorder.ID)
}

func (s *MemoryStore) recordAudit(actor string, action string, object string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.recordAuditLocked(actor, action, object)
}

func (s *MemoryStore) recordAuditLocked(actor string, action string, object string) {
	s.auditLogs = append([]domain.AuditLog{{
		ID:        fmt.Sprintf("AUD-%04d", s.auditSeq),
		Actor:     actor,
		Action:    action,
		Object:    object,
		Result:    "成功",
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}}, s.auditLogs...)
	s.auditSeq++
}

func (s *MemoryStore) recordNotification(target string, title string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.recordNotificationLocked(target, title)
}

func (s *MemoryStore) recordNotificationLocked(target string, title string) {
	s.notifications = append([]domain.Notification{{
		ID:        fmt.Sprintf("NTF-%04d", s.notificationSeq),
		Target:    target,
		Title:     title,
		Status:    "unread",
		CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}}, s.notifications...)
	s.notificationSeq++
}

func defaultProbeAgentConfig(capabilities []string) map[string]any {
	caps := append([]string(nil), capabilities...)
	if len(caps) == 0 {
		caps = []string{"HTTP"}
	}
	return map[string]any{
		"heartbeat_interval_seconds": 30,
		"task_claim_limit":           5,
		"capabilities":               caps,
		"result_endpoint":            "/api/v1/probes/tasks/{task_id}/result",
		"schedule_result_endpoint":   "/api/v1/probes/schedules/{schedule_id}/result",
	}
}

func sanitizeProbe(probe domain.ProbeNode) domain.ProbeNode {
	probe.Token = ""
	return probe
}

func probeTokenHint(token string) string {
	if token == "" {
		return ""
	}
	if len(token) <= 10 {
		return token
	}
	return token[:10] + "…"
}

func probeVersionNumber(version string) int {
	trimmed := strings.TrimPrefix(strings.TrimSpace(version), "v")
	value, err := strconv.Atoi(trimmed)
	if err != nil || value <= 0 {
		return 1
	}
	return value
}

func (s *MemoryStore) enrichProbeLocked(probe domain.ProbeNode) domain.ProbeNode {
	nowTime := time.Now().UTC()
	now := nowTime.Format(time.RFC3339)
	if probe.Name == "" {
		probe.Name = probe.ID
	}
	if probe.Region == "" {
		probe.Region = "unknown"
	}
	if probe.NetworkType == "" {
		probe.NetworkType = "公网出口"
	}
	if probe.Status == "" {
		probe.Status = "online"
	}
	if probe.HeartbeatAt == "" {
		probe.HeartbeatAt = now
	}
	if probe.Version == "" {
		probe.Version = "v1"
	}
	if probe.RegisteredAt == "" {
		probe.RegisteredAt = probe.HeartbeatAt
	}
	if probe.LastConfigSyncAt == "" {
		probe.LastConfigSyncAt = probe.HeartbeatAt
	}
	if len(probe.Capabilities) == 0 {
		probe.Capabilities = []string{"HTTP"}
	}
	if probe.ConnectionStatus == "" {
		probe.ConnectionStatus = "connected"
		if probe.Status != "online" {
			probe.ConnectionStatus = "disconnected"
		}
	}
	if heartbeatAt, ok := parseProbeTimestamp(probe.HeartbeatAt); ok && probe.Status != "retired" {
		delay := nowTime.Sub(heartbeatAt)
		if delay >= 5*time.Minute {
			probe.Status = "offline"
			probe.ConnectionStatus = "disconnected"
		} else if delay >= 90*time.Second {
			probe.Status = "degraded"
			probe.ConnectionStatus = "degraded"
		}
	}
	if probe.ConfigStatus == "" {
		probe.ConfigStatus = "acknowledged"
	}
	if probe.GatewayURL == "" && probe.ID != "" {
		probe.GatewayURL = "https://gateway.oneall.internal/probes/" + probe.ID
	}
	if probe.BootstrapTokenHint == "" {
		probe.BootstrapTokenHint = probeTokenHint(probe.Token)
	}
	if probe.AgentConfig == nil {
		probe.AgentConfig = defaultProbeAgentConfig(probe.Capabilities)
	}

	pending, running, executed, failed, avgLatency := s.probeTaskStatsLocked(probe)
	if probe.ActiveTasks == 0 {
		probe.ActiveTasks = running
	}
	if probe.QueueDepth == 0 {
		probe.QueueDepth = pending
	}
	if probe.Executions == 0 {
		probe.Executions = executed
	}
	if probe.Failed == 0 {
		probe.Failed = failed
	}
	if probe.AvgLatencyMs == 0 {
		probe.AvgLatencyMs = avgLatency
	}
	if probe.SuccessRate == 0 {
		if probe.Executions > 0 {
			probe.SuccessRate = roundMetric(float64(probe.Executions-probe.Failed) * 100 / float64(probe.Executions))
		} else {
			probe.SuccessRate = 100
		}
	}
	if probe.CPUUsage == 0 {
		probe.CPUUsage = 12
	}
	if probe.MemoryUsageMB == 0 {
		probe.MemoryUsageMB = 256
	}
	if probe.MemoryUsagePct == 0 {
		probe.MemoryUsagePct = 24
	}
	if probe.LoadAvg == 0 {
		probe.LoadAvg = 0.2
	}
	if probe.Uptime == "" {
		probe.Uptime = "刚刚"
	}
	return probe
}

func (s *MemoryStore) probeTaskStatsLocked(probe domain.ProbeNode) (int, int, int, int, int) {
	pending := 0
	running := 0
	executed := 0
	failed := 0
	totalLatency := 0
	latencyCount := 0
	for _, task := range s.detectionTasks {
		if task.Probe != probe.Name && task.Probe != probe.ID {
			continue
		}
		switch task.Status {
		case "pending":
			pending++
		case "running":
			running++
		case "success":
			executed++
		case "failed":
			executed++
			failed++
		}
		if task.Result != nil {
			if latency, ok := numericAny(task.Result["latency_ms"]); ok {
				totalLatency += int(latency)
				latencyCount++
			}
			if latency, ok := numericAny(task.Result["duration_ms"]); ok {
				totalLatency += int(latency)
				latencyCount++
			}
		}
	}
	avgLatency := probe.AvgLatencyMs
	if avgLatency == 0 {
		avgLatency = 89
	}
	if latencyCount > 0 {
		avgLatency = totalLatency / latencyCount
	}
	return pending, running, executed, failed, avgLatency
}

func numericAny(value any) (float64, bool) {
	switch typed := value.(type) {
	case int:
		return float64(typed), true
	case int64:
		return float64(typed), true
	case float64:
		return typed, true
	case float32:
		return float64(typed), true
	case string:
		number, err := strconv.ParseFloat(typed, 64)
		return number, err == nil
	default:
		return 0, false
	}
}

func numericInt(value any) (int, bool) {
	number, ok := numericAny(value)
	if !ok {
		return 0, false
	}
	return int(number), true
}

func maxInt(left int, right int) int {
	if left > right {
		return left
	}
	return right
}

func parseProbeTimestamp(value string) (time.Time, bool) {
	if value == "" {
		return time.Time{}, false
	}
	if parsed, err := time.Parse(time.RFC3339, value); err == nil {
		return parsed, true
	}
	if parsed, err := time.Parse("2006-01-02 15:04:05", value); err == nil {
		return parsed, true
	}
	return time.Time{}, false
}

func heartbeatDelaySeconds(value string) int {
	parsed, ok := parseProbeTimestamp(value)
	if !ok {
		return 0
	}
	delay := int(time.Since(parsed).Seconds())
	if delay < 0 {
		return 0
	}
	return delay
}

func roundMetric(value float64) float64 {
	if value < 0 {
		value = 0
	}
	if value > 100 {
		value = 100
	}
	return float64(int(value*10+0.5)) / 10
}

func valueOrDefault(value string, fallback string) string {
	if value == "" {
		return fallback
	}
	return value
}

func countSeverity(items []domain.AlertEvent, severity string) int {
	count := 0
	for _, item := range items {
		if item.Severity == severity {
			count++
		}
	}
	return count
}

func containsText(value string, query string) bool {
	return query == "" || strings.Contains(strings.ToLower(value), strings.ToLower(query))
}
