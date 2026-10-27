package domain

import (
	"errors"
	"fmt"
	"net"
	"regexp"
	"strings"
	"time"
)

var Roles = []string{"PlatformAdmin", "OpsAdmin", "OpsEngineer", "Approver", "Viewer"}

var PermissionMatrix = map[string]map[string][]string{
	"monitoringOverview": {
		"PlatformAdmin": {"read"},
		"OpsAdmin":      {"read"},
		"OpsEngineer":   {"read"},
		"Approver":      {"read"},
		"Viewer":        {"read"},
	},
	"alertEvents": {
		"PlatformAdmin": {"read", "close"},
		"OpsAdmin":      {"read", "close"},
		"OpsEngineer":   {"read", "execute"},
		"Approver":      {"read"},
		"Viewer":        {"read"},
	},
	"monitoringPolicies": {
		"PlatformAdmin": {"read", "create", "update"},
		"OpsAdmin":      {"read", "create", "update", "execute"},
		"OpsEngineer":   {"read", "create", "update"},
		"Approver":      {"read"},
		"Viewer":        {"read"},
	},
	"probeNodes": {
		"PlatformAdmin": {"read", "manage"},
		"OpsAdmin":      {"read", "manage"},
		"OpsEngineer":   {"read"},
		"Approver":      {},
		"Viewer":        {"read"},
	},
	"assetCenter": {
		"PlatformAdmin": {"read", "create", "update"},
		"OpsAdmin":      {"read", "create", "update", "sync"},
		"OpsEngineer":   {"read", "create", "update"},
		"Approver":      {"read"},
		"Viewer":        {"read"},
	},
	"oneOffDetection": {
		"PlatformAdmin": {"read", "execute"},
		"OpsAdmin":      {"read", "execute"},
		"OpsEngineer":   {"read", "execute"},
		"Approver":      {"read"},
		"Viewer":        {"read"},
	},
	"workorders": {
		"PlatformAdmin": {"read", "manage"},
		"OpsAdmin":      {"read", "manage"},
		"OpsEngineer":   {"read", "create", "execute"},
		"Approver":      {"approve"},
		"Viewer":        {"read"},
	},
	"usersAndRoles": {
		"PlatformAdmin": {"read", "create", "update", "delete"},
		"OpsAdmin":      {},
		"OpsEngineer":   {},
		"Approver":      {},
		"Viewer":        {},
	},
	"credentials": {
		"PlatformAdmin": {"read", "create", "update", "delete", "manage"},
		"OpsAdmin":      {"read", "reference"},
		"OpsEngineer":   {"reference"},
		"Approver":      {},
		"Viewer":        {},
	},
	"dataSources": {
		"PlatformAdmin": {"read", "create", "update", "delete"},
		"OpsAdmin":      {"read", "create", "update"},
		"OpsEngineer":   {"read"},
		"Approver":      {},
		"Viewer":        {},
	},
	"notificationsWebhooks": {
		"PlatformAdmin": {"read", "create", "update", "delete"},
		"OpsAdmin":      {"read", "create", "update"},
		"OpsEngineer":   {"read"},
		"Approver":      {},
		"Viewer":        {},
	},
	"auditLogs": {
		"PlatformAdmin": {"read"},
		"OpsAdmin":      {"read"},
		"OpsEngineer":   {},
		"Approver":      {},
		"Viewer":        {},
	},
}

var DataScopeMatrix = map[string]map[string]string{
	"PlatformAdmin": {"assets": "all", "alerts": "all", "workorders": "all", "auditLogs": "all"},
	"OpsAdmin":      {"assets": "all", "alerts": "all", "workorders": "all", "auditLogs": "all"},
	"OpsEngineer":   {"assets": "owned_or_prod", "alerts": "owned_or_team", "workorders": "owned_or_assigned", "auditLogs": "none"},
	"Approver":      {"assets": "prod", "alerts": "readable", "workorders": "approval_queue", "auditLogs": "none"},
	"Viewer":        {"assets": "prod", "alerts": "readable", "workorders": "readable", "auditLogs": "none"},
}

var WorkorderTransitions = map[string][]string{
	"draft":     {"submitted", "withdrawn"},
	"submitted": {"approved", "rejected", "withdrawn"},
	"rejected":  {"draft"},
	"approved":  {"executing", "canceled"},
	"executing": {"completed", "failed"},
	"completed": {},
	"failed":    {"executing"},
	"canceled":  {},
	"withdrawn": {"submitted"},
}

type WorkorderStatusMetadata struct {
	Tab     string   `json:"tab"`
	Actions []string `json:"actions"`
}

var WorkorderStatusMeta = map[string]WorkorderStatusMetadata{
	"draft":     {Tab: "我的申请", Actions: []string{"编辑", "提交", "删除"}},
	"submitted": {Tab: "待我审批", Actions: []string{"审批", "驳回", "撤回"}},
	"rejected":  {Tab: "我的申请", Actions: []string{"重新编辑", "归档"}},
	"approved":  {Tab: "待我执行", Actions: []string{"执行", "取消"}},
	"executing": {Tab: "待我执行", Actions: []string{"更新进度", "标记失败", "完成"}},
	"completed": {Tab: "工单详情", Actions: []string{"查看", "关联告警关闭记录"}},
	"failed":    {Tab: "工单详情", Actions: []string{"重试", "转人工处理"}},
	"canceled":  {Tab: "工单详情", Actions: []string{"查看"}},
	"withdrawn": {Tab: "我的申请", Actions: []string{"查看", "重新提交"}},
}

var assetFieldTypes = map[string]bool{
	"string": true, "number": true, "boolean": true, "datetime": true,
	"enum": true, "ip": true, "url": true, "user": true,
}

var fieldKeyPattern = regexp.MustCompile(`^[a-zA-Z][a-zA-Z0-9_]*$`)

type AssetField struct {
	Key      string   `json:"key"`
	Type     string   `json:"type"`
	Label    string   `json:"label,omitempty"`
	Required bool     `json:"required,omitempty"`
	Options  []string `json:"options,omitempty"`
}

type AssetModel struct {
	ID         string       `json:"id"`
	Name       string       `json:"name"`
	Code       string       `json:"code"`
	Fields     []AssetField `json:"fields"`
	PrimaryKey string       `json:"primary_key,omitempty"`
	Status     string       `json:"status"`
	CreatedBy  string       `json:"created_by"`
	CreatedAt  string       `json:"created_at"`
}

type AssetRecord map[string]any

type AlertRule struct {
	Scope struct {
		AssetModel  string         `json:"asset_model"`
		AssetFilter map[string]any `json:"asset_filter,omitempty"`
	} `json:"scope"`
	Signal struct {
		Metric string `json:"metric"`
		Source string `json:"source"`
	} `json:"signal"`
	Condition AlertCondition `json:"condition"`
	Severity  string         `json:"severity"`
	Actions   struct {
		NotifyChannels  []string `json:"notify_channels"`
		CreateWorkorder bool     `json:"create_workorder"`
	} `json:"actions"`
}

type AlertCondition struct {
	Operator    string `json:"operator"`
	Value       any    `json:"value"`
	Duration    string `json:"duration,omitempty"`
	Consecutive int    `json:"consecutive,omitempty"`
}

type Strategy struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Scope     string    `json:"scope"`
	Enabled   bool      `json:"enabled"`
	Version   string    `json:"version"`
	Rule      AlertRule `json:"rule"`
	CreatedAt string    `json:"created_at"`
}

type Workorder struct {
	ID             string `json:"id"`
	Type           string `json:"type"`
	Title          string `json:"title"`
	Applicant      string `json:"applicant"`
	Assignee       string `json:"assignee"`
	Status         string `json:"status"`
	SLA            string `json:"sla"`
	BusinessLine   string `json:"business_line,omitempty"`
	Environment    string `json:"environment,omitempty"`
	RelatedObject  string `json:"related_object,omitempty"`
	RelatedAlertID string `json:"relatedAlertId,omitempty"`
	UpdatedAt      string `json:"updated_at"`
	CreatedAt      string `json:"created_at"`
}

type DetectionTask struct {
	ID           string         `json:"id"`
	Type         string         `json:"type"`
	Target       string         `json:"target"`
	Probe        string         `json:"probe"`
	Status       string         `json:"status"`
	RelatedAsset string         `json:"related_asset"`
	BusinessLine string         `json:"business_line,omitempty"`
	Environment  string         `json:"environment,omitempty"`
	Protocol     string         `json:"protocol,omitempty"`
	Port         int            `json:"port,omitempty"`
	TimeoutSec   int            `json:"timeout_seconds,omitempty"`
	Metadata     map[string]any `json:"metadata,omitempty"`
	Result       map[string]any `json:"result,omitempty"`
	ResultID     string         `json:"result_id,omitempty"`
	ClaimedAt    string         `json:"claimed_at,omitempty"`
	CompletedAt  string         `json:"completed_at,omitempty"`
	ClaimedBy    string         `json:"claimed_by_probe_id,omitempty"`
	LatencyMs    int            `json:"latency_ms,omitempty"`
	Message      string         `json:"message,omitempty"`
	CreatedAt    string         `json:"created_at"`
	UpdatedAt    string         `json:"updated_at"`
}

type AlertEvent struct {
	ID           string `json:"id"`
	Severity     string `json:"severity"`
	Title        string `json:"title"`
	Asset        string `json:"asset"`
	Duration     string `json:"duration"`
	Owner        string `json:"owner"`
	BusinessLine string `json:"business_line,omitempty"`
	Environment  string `json:"environment,omitempty"`
	Notify       string `json:"notify"`
	Workorder    string `json:"workorder"`
	Status       string `json:"status"`
	SourceTaskID string `json:"sourceTaskId,omitempty"`
	CreatedAt    string `json:"created_at"`
}

type Notification struct {
	ID        string `json:"id"`
	Target    string `json:"target"`
	Title     string `json:"title"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

type ProbeNode struct {
	ID                 string         `json:"id"`
	Name               string         `json:"name"`
	Region             string         `json:"region"`
	NetworkType        string         `json:"network_type,omitempty"`
	IPAddress          string         `json:"ip_address,omitempty"`
	Capabilities       []string       `json:"capabilities"`
	Status             string         `json:"status"`
	HeartbeatAt        string         `json:"heartbeat_at"`
	Version            string         `json:"version,omitempty"`
	ActiveTasks        int            `json:"active_tasks,omitempty"`
	SuccessRate        float64        `json:"success_rate,omitempty"`
	AvgLatencyMs       int            `json:"avg_latency_ms,omitempty"`
	QueueDepth         int            `json:"queue_depth,omitempty"`
	Executions         int            `json:"executions,omitempty"`
	Failed             int            `json:"failed,omitempty"`
	CPUUsage           float64        `json:"cpu_usage,omitempty"`
	MemoryUsageMB      int            `json:"memory_usage_mb,omitempty"`
	MemoryUsagePct     float64        `json:"memory_usage_pct,omitempty"`
	LoadAvg            float64        `json:"load_avg,omitempty"`
	Uptime             string         `json:"uptime,omitempty"`
	ConnectionStatus   string         `json:"connection_status,omitempty"`
	ConfigStatus       string         `json:"config_status,omitempty"`
	GatewayURL         string         `json:"gateway_url,omitempty"`
	BootstrapTokenHint string         `json:"bootstrap_token_hint,omitempty"`
	RegisteredAt       string         `json:"registered_at,omitempty"`
	LastConfigSyncAt   string         `json:"last_config_sync_at,omitempty"`
	AgentConfig        map[string]any `json:"agent_config,omitempty"`
	Token              string         `json:"token,omitempty"`
}

type AuditLog struct {
	ID        string `json:"id"`
	Actor     string `json:"actor"`
	Action    string `json:"action"`
	Object    string `json:"object"`
	Result    string `json:"result"`
	CreatedAt string `json:"created_at"`
}

func HasPermission(role string, module string, action string) bool {
	actions := PermissionMatrix[module][role]
	for _, allowed := range actions {
		if allowed == action {
			return true
		}
	}
	return false
}

func ValidateAlertRule(rule AlertRule) []string {
	var errs []string
	if rule.Scope.AssetModel == "" {
		errs = append(errs, "scope.asset_model 必填")
	}
	if rule.Signal.Metric == "" {
		errs = append(errs, "signal.metric 必填")
	}
	if rule.Signal.Source == "" {
		errs = append(errs, "signal.source 必填")
	}
	if !contains([]string{"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "regex"}, rule.Condition.Operator) {
		errs = append(errs, "condition.operator 不支持")
	}
	if !contains([]string{"info", "warning", "critical"}, rule.Severity) {
		errs = append(errs, "severity 必须是 info、warning、critical")
	}
	if rule.Actions.NotifyChannels == nil {
		errs = append(errs, "actions.notify_channels 必须是数组")
	}
	return errs
}

func ValidateAssetFields(fields []AssetField) []string {
	var errs []string
	seen := map[string]bool{}
	for index, field := range fields {
		path := fmt.Sprintf("fields[%d]", index)
		if field.Key == "" || !fieldKeyPattern.MatchString(field.Key) {
			errs = append(errs, path+".key 必须是字母开头的标识符")
		}
		if field.Key != "" && seen[field.Key] {
			errs = append(errs, path+".key 重复")
		}
		seen[field.Key] = true
		if !assetFieldTypes[field.Type] {
			errs = append(errs, path+".type 不支持")
		}
		if field.Type == "enum" && len(field.Options) == 0 {
			errs = append(errs, path+".options 必须包含枚举值")
		}
	}
	return errs
}

func ValidateAssetRecord(model AssetModel, record AssetRecord) []string {
	var errs []string
	for _, field := range model.Fields {
		value, exists := record[field.Key]
		if field.Required && (!exists || value == nil || fmt.Sprint(value) == "") {
			errs = append(errs, field.Key+" 必填")
			continue
		}
		if !exists || value == nil || fmt.Sprint(value) == "" {
			continue
		}
		if field.Type == "ip" && !IsIPv4(fmt.Sprint(value)) {
			errs = append(errs, field.Key+" 必须是 IPv4")
		}
		if field.Type == "url" && !strings.HasPrefix(fmt.Sprint(value), "http://") && !strings.HasPrefix(fmt.Sprint(value), "https://") {
			errs = append(errs, field.Key+" 必须是 URL")
		}
		if field.Type == "enum" && !contains(field.Options, fmt.Sprint(value)) {
			errs = append(errs, field.Key+" 不在枚举范围内")
		}
	}
	return errs
}

func CanTransitionWorkorder(from string, to string) bool {
	for _, allowed := range WorkorderTransitions[from] {
		if allowed == to {
			return true
		}
	}
	return false
}

func TransitionWorkorder(item Workorder, nextStatus string) (Workorder, error) {
	if !CanTransitionWorkorder(item.Status, nextStatus) {
		return item, errors.New("工单状态不能从 " + item.Status + " 流转到 " + nextStatus)
	}
	item.Status = nextStatus
	item.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
	return item, nil
}

func IsIPv4(value string) bool {
	ip := net.ParseIP(value)
	return ip != nil && ip.To4() != nil
}

func CompileIPRegexFromText(input string) map[string]any {
	lines := strings.FieldsFunc(input, func(r rune) bool {
		return r == '\n' || r == '\r' || r == ',' || r == ' ' || r == '\t'
	})
	seen := map[string]bool{}
	var items []string
	var invalid []string
	for _, line := range lines {
		value := strings.TrimSpace(line)
		if value == "" {
			continue
		}
		if !IsIPv4(value) {
			invalid = append(invalid, value)
			continue
		}
		if !seen[value] {
			items = append(items, value)
			seen[value] = true
		}
	}
	if len(invalid) > 0 {
		return map[string]any{"valid": false, "items": items, "invalid": invalid, "regex": ""}
	}
	escaped := make([]string, 0, len(items))
	for _, item := range items {
		escaped = append(escaped, regexp.QuoteMeta(item))
	}
	return map[string]any{"valid": true, "items": items, "invalid": invalid, "regex": "^(" + strings.Join(escaped, "|") + ")$"}
}

func ExpandIPRegex(regexText string, limit int) map[string]any {
	if limit <= 0 {
		limit = 500
	}
	if !strings.HasPrefix(regexText, "^(") || !strings.HasSuffix(regexText, ")$") {
		return map[string]any{"items": []string{}, "truncated": false, "error": "仅支持本工具生成的精确 IP 正则"}
	}
	body := strings.TrimSuffix(strings.TrimPrefix(regexText, "^("), ")$")
	parts := strings.Split(body, "|")
	var items []string
	for _, part := range parts {
		value := strings.ReplaceAll(part, `\.`, ".")
		if IsIPv4(value) {
			items = append(items, value)
		}
		if len(items) == limit {
			return map[string]any{"items": items, "truncated": len(parts) > limit}
		}
	}
	return map[string]any{"items": items, "truncated": false}
}

func contains(items []string, value string) bool {
	for _, item := range items {
		if item == value {
			return true
		}
	}
	return false
}
