package store

import "oneall-go-api/internal/domain"

type Store interface {
	Search(query string) []map[string]any
	Overview() map[string]any

	ListAssetModels() []domain.AssetModel
	CreateAssetModel(input domain.AssetModel, actor string) (domain.AssetModel, []string)
	UpdateAssetModel(id string, input domain.AssetModel, actor string) (domain.AssetModel, bool, []string)
	ListAssetRecords(modelID string) []domain.AssetRecord
	BatchAssetRecords(modelID string, records []domain.AssetRecord, actor string) ([]domain.AssetRecord, []string, bool)
	PreviewAssetSync(modelID string, input map[string]any) (map[string]any, bool)
	RunAssetSync(modelID string, input map[string]any, actor string) (map[string]any, bool, []string)
	ListSyncRuns() []map[string]any
	ValidateCMDBDomain(domainName string) map[string]any

	ListWorkorders(role string) []domain.Workorder
	GetWorkorder(id string) (domain.Workorder, bool)
	CreateWorkorder(input domain.Workorder, actor string) domain.Workorder
	TransitionWorkorder(id string, nextStatus string) (domain.Workorder, bool, error)
	BatchWorkorders(ids []string, action string, actor string) ([]domain.Workorder, string)

	ListStrategies() []domain.Strategy
	CreateStrategy(input domain.Strategy, actor string) (domain.Strategy, []string)
	BatchStrategies(ids []string, action string, actor string) ([]domain.Strategy, string)

	CreateDetection(input domain.DetectionTask, actor string) domain.DetectionTask
	ListDetectionTasks() []domain.DetectionTask
	GetDetectionTask(id string) (domain.DetectionTask, bool)
	ClaimProbeTasks(probeID string, limit int) []domain.DetectionTask
	SubmitProbeResult(taskID string, result map[string]any, actor string) (domain.DetectionTask, bool)

	ListAlerts() []domain.AlertEvent
	GetAlert(id string) (domain.AlertEvent, bool)
	CloseAlerts(ids []string, actor string) []domain.AlertEvent

	RegisterProbe(input domain.ProbeNode) domain.ProbeNode
	ListProbes() []domain.ProbeNode
	ListProbeHealth(hours int, intervalMinutes int) map[string]any
	GetProbeRuntime(id string) (map[string]any, bool)
	HeartbeatProbe(id string, input domain.ProbeNode, actor string) (domain.ProbeNode, bool)
	ValidateProbeToken(id string, token string) bool
	ListProbeMetricsHistory(id string, hours int, intervalMinutes int) (map[string]any, bool)
	ListProbeConfigVersions(id string) ([]map[string]any, bool)
	RefreshProbeConfig(id string, actor string) (domain.ProbeNode, bool)
	RollbackProbeConfig(id string, version int, actor string) (domain.ProbeNode, bool)
	RetireProbe(id string, actor string) (domain.ProbeNode, bool)

	ListNotifications() []domain.Notification
	ListAuditLogs() []domain.AuditLog
}

func NewRuntimeStore(databaseURL string) Store {
	if databaseURL != "" {
		return NewPostgresStore(databaseURL)
	}
	return NewMemoryStore()
}
