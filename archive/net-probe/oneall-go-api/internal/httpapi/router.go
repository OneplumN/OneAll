package httpapi

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"oneall-go-api/internal/config"
	"oneall-go-api/internal/domain"
	"oneall-go-api/internal/store"
)

type RouterDependencies struct {
	Config config.Config
	Store  store.Store
}

func NewRouter(cfg config.Config) *gin.Engine {
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(corsMiddleware())
	RegisterRoutes(router, RouterDependencies{Config: cfg, Store: store.NewRuntimeStore(cfg.DatabaseURL)})
	return router
}

func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")
		if origin == "" {
			origin = "*"
		}
		c.Header("Access-Control-Allow-Origin", origin)
		c.Header("Vary", "Origin")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-OneAll-Role, x-oneall-role, X-OneAll-Probe-Id, x-oneall-probe-id")
		c.Header("Access-Control-Allow-Credentials", "false")
		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}

func RegisterRoutes(router *gin.Engine, deps RouterDependencies) {
	if deps.Store == nil {
		deps.Store = store.NewRuntimeStore(deps.Config.DatabaseURL)
	}

	router.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	api := router.Group("/api/v1")
	api.GET("/search", routeKey("search.global", searchHandler(deps.Store)))

	auth := api.Group("/auth")
	auth.POST("/login", routeKey("auth.login", loginHandler()))
	auth.GET("/profile", routeKey("auth.profile", profileHandler()))

	notifications := api.Group("/notifications")
	notifications.GET("", routeKey("notifications.list", listNotificationsHandler(deps.Store)))
	notifications.GET("/stream", routeKey("notifications.stream", notificationStreamHandler(deps.Store)))

	detection := api.Group("/detection")
	detection.POST("/one-off", routeKey("detection.oneOff.create", createDetectionHandler(deps.Store)))
	detection.GET("/tasks", routeKey("detection.tasks.list", listDetectionTasksHandler(deps.Store)))
	detection.GET("/tasks/:id", routeKey("detection.task.detail", getDetectionTaskHandler(deps.Store)))
	detection.GET("/cmdb/validate", routeKey("detection.cmdb.validate", validateCMDBDomainHandler(deps.Store)))

	workorders := api.Group("/workorders/requests")
	workorders.POST("", routeKey("workorders.create", createWorkorderHandler(deps.Store)))
	workorders.GET("", routeKey("workorders.list", listWorkordersHandler(deps.Store)))
	workorders.POST("/batch", routeKey("workorders.batch", batchWorkordersHandler(deps.Store)))
	workorders.GET("/:id", routeKey("workorders.detail", getWorkorderHandler(deps.Store)))
	workorders.POST("/:id/approve", routeKey("workorders.approve", transitionWorkorderHandler(deps.Store, "approved")))
	workorders.POST("/:id/reject", routeKey("workorders.reject", transitionWorkorderHandler(deps.Store, "rejected")))

	assets := api.Group("/assets")
	assets.GET("/models", routeKey("assets.models.list", listAssetModelsHandler(deps.Store)))
	assets.POST("/models", routeKey("assets.models.create", createAssetModelHandler(deps.Store)))
	assets.PUT("/models/:model_id", routeKey("assets.models.update", updateAssetModelHandler(deps.Store)))
	assets.GET("/records/query", routeKey("assets.records.query", listAssetRecordsHandler(deps.Store)))
	assets.POST("/records/batch", routeKey("assets.records.batch", batchAssetRecordsHandler(deps.Store)))
	assets.POST("/models/:model_id/sync/preview", routeKey("assets.sync.preview", previewAssetSyncHandler(deps.Store)))
	assets.POST("/models/:model_id/sync", routeKey("assets.sync.run", runAssetSyncHandler(deps.Store)))
	assets.GET("/sync/runs", routeKey("assets.sync.history", listSyncRunsHandler(deps.Store)))

	monitoring := api.Group("/monitoring")
	monitoring.GET("/overview", routeKey("monitoring.overview", overviewHandler(deps.Store)))
	monitoring.GET("/strategies", routeKey("monitoring.strategies.list", listStrategiesHandler(deps.Store)))
	monitoring.POST("/strategies", routeKey("monitoring.strategies.create", createStrategyHandler(deps.Store)))
	monitoring.POST("/strategies/batch", routeKey("monitoring.strategies.batch", batchStrategiesHandler(deps.Store)))

	alerts := api.Group("/alerts/events")
	alerts.GET("", routeKey("alerts.events.list", listAlertsHandler(deps.Store)))
	alerts.POST("/batch", routeKey("alerts.events.batch", batchAlertsHandler(deps.Store)))
	alerts.GET("/:id", routeKey("alerts.events.detail", getAlertHandler(deps.Store)))

	probes := api.Group("/probes")
	probes.POST("/register", routeKey("probes.register", registerProbeHandler(deps.Store)))
	probes.GET("/nodes", routeKey("probes.nodes.list", listProbesHandler(deps.Store)))
	probes.GET("/nodes/health", routeKey("probes.nodes.health", listProbeHealthHandler(deps.Store)))
	probes.GET("/nodes/:id/runtime", routeKey("probes.nodes.runtime", getProbeRuntimeHandler(deps.Store)))
	probes.POST("/nodes/:id/heartbeat", routeKey("probes.nodes.heartbeat", heartbeatProbeHandler(deps.Store)))
	probes.GET("/nodes/:id/metrics/history", routeKey("probes.nodes.metricsHistory", listProbeMetricsHistoryHandler(deps.Store)))
	probes.POST("/nodes/:id/retire", routeKey("probes.nodes.retire", retireProbeHandler(deps.Store)))
	probes.POST("/nodes/:id/config/refresh", routeKey("probes.config.refresh", refreshProbeConfigHandler(deps.Store)))
	probes.GET("/nodes/:id/config/versions", routeKey("probes.config.versions", listProbeConfigVersionsHandler(deps.Store)))
	probes.POST("/nodes/:id/config/rollback", routeKey("probes.config.rollback", rollbackProbeConfigHandler(deps.Store)))
	probes.POST("/tasks/claim", routeKey("probes.tasks.claim", claimProbeTasksHandler(deps.Store)))
	probes.POST("/tasks/:task_id/result", routeKey("probes.tasks.result", submitProbeResultHandler(deps.Store)))
	probes.POST("/schedules/:schedule_id/result", routeKey("probes.schedules.result", scheduleResultHandler()))

	settings := api.Group("/settings")
	settings.GET("/permissions/catalog", routeKey("settings.permissions.catalog", permissionCatalogHandler()))
	settings.GET("/users", routeKey("settings.users.list", usersHandler()))
	settings.GET("/data-sources", routeKey("settings.dataSources.list", dataSourcesHandler()))
	settings.GET("/credentials", routeKey("settings.credentials.list", credentialsHandler()))
	settings.GET("/notification-channels", routeKey("settings.notificationChannels.list", notificationChannelsHandler()))
	settings.GET("/notification-templates", routeKey("settings.notificationTemplates.list", notificationTemplatesHandler()))
	settings.GET("/webhooks", routeKey("settings.webhooks.list", webhooksHandler()))
	settings.POST("/webhooks/:id/test", routeKey("settings.webhooks.test", webhookTestHandler()))
	settings.GET("/audit-logs", routeKey("settings.auditLogs.list", listAuditLogsHandler(deps.Store)))

	tools := api.Group("/tools")
	tools.POST("/ip-regex/compile", routeKey("tools.ipRegex.compile", compileIPRegexHandler()))
	tools.POST("/ip-regex/expand", routeKey("tools.ipRegex.expand", expandIPRegexHandler()))

	_ = deps
}

func routeKey(_ string, handler gin.HandlerFunc) gin.HandlerFunc {
	return handler
}

func searchHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"items": memory.Search(c.Query("q"))})
	}
}

func loginHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"token": "dev-token-go", "profile": gin.H{"id": "dev-user", "name": "OpsAdmin", "role": "OpsAdmin"}})
	}
}

func roleFromRequest(c *gin.Context) string {
	role := c.GetHeader("x-oneall-role")
	if role == "" {
		return "OpsAdmin"
	}
	return role
}

func requirePermission(c *gin.Context, module string, action string) bool {
	role := roleFromRequest(c)
	if domain.HasPermission(role, module, action) {
		return true
	}
	c.JSON(http.StatusForbidden, gin.H{"error": "角色 " + role + " 缺少 " + module + "." + action + " 权限"})
	return false
}

func permissionCatalogHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"roles":               domain.Roles,
			"permissionMatrix":    domain.PermissionMatrix,
			"dataScopeMatrix":     domain.DataScopeMatrix,
			"workorderStatusMeta": domain.WorkorderStatusMeta,
		})
	}
}

func profileHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		role := roleFromRequest(c)
		c.JSON(http.StatusOK, gin.H{
			"id":   "dev-user",
			"name": role,
			"role": role,
		})
	}
}

func overviewHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "monitoringOverview", "read") {
			return
		}
		c.JSON(http.StatusOK, memory.Overview())
	}
}

func listAssetModelsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListAssetModels()})
	}
}

func createAssetModelHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "create") {
			return
		}

		var input domain.AssetModel
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if input.Name == "" || input.Code == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "name 和 code 必填"})
			return
		}

		model, errs := memory.CreateAssetModel(input, roleFromRequest(c))
		if len(errs) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errs[0], "errors": errs})
			return
		}
		c.JSON(http.StatusCreated, model)
	}
}

func updateAssetModelHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "update") {
			return
		}
		var input domain.AssetModel
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		model, found, errs := memory.UpdateAssetModel(c.Param("model_id"), input, roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "资产模型不存在"})
			return
		}
		if len(errs) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errs[0], "errors": errs})
			return
		}
		c.JSON(http.StatusOK, model)
	}
}

func listAssetRecordsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListAssetRecords(c.Query("model_id"))})
	}
}

func batchAssetRecordsHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		ModelID   string               `json:"model_id"`
		ModelCode string               `json:"model_code"`
		Records   []domain.AssetRecord `json:"records"`
	}
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "update") {
			return
		}
		var input request
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		modelID := input.ModelID
		if modelID == "" {
			modelID = input.ModelCode
		}
		items, errs, found := memory.BatchAssetRecords(modelID, input.Records, roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "资产模型不存在"})
			return
		}
		if len(errs) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errs[0], "errors": errs})
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": items, "count": len(items)})
	}
}

func previewAssetSyncHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "sync") {
			return
		}
		var input map[string]any
		_ = c.ShouldBindJSON(&input)
		if input == nil {
			input = map[string]any{}
		}
		preview, found := memory.PreviewAssetSync(c.Param("model_id"), input)
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "资产模型不存在"})
			return
		}
		c.JSON(http.StatusOK, preview)
	}
}

func runAssetSyncHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "sync") {
			return
		}
		var input map[string]any
		_ = c.ShouldBindJSON(&input)
		if input == nil {
			input = map[string]any{}
		}
		result, found, errs := memory.RunAssetSync(c.Param("model_id"), input, roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "资产模型不存在"})
			return
		}
		if len(errs) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errs[0], "errors": errs})
			return
		}
		c.JSON(http.StatusOK, result)
	}
}

func listSyncRunsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "assetCenter", "read") {
			return
		}
		items := memory.ListSyncRuns()
		if items == nil {
			items = []map[string]any{}
		}
		c.JSON(http.StatusOK, gin.H{"items": items})
	}
}

func validateCMDBDomainHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "oneOffDetection", "read") {
			return
		}
		domainName := c.Query("domain")
		if domainName == "" {
			domainName = c.Query("target")
		}
		c.JSON(http.StatusOK, memory.ValidateCMDBDomain(domainName))
	}
}

func listStrategiesHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "monitoringPolicies", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListStrategies()})
	}
}

func batchStrategiesHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		Action string   `json:"action"`
		IDs    []string `json:"ids"`
	}
	return func(c *gin.Context) {
		if !requirePermission(c, "monitoringPolicies", "execute") {
			return
		}
		var input request
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		items, message := memory.BatchStrategies(input.IDs, input.Action, roleFromRequest(c))
		if message != "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": message})
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": items})
	}
}

func createStrategyHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "monitoringPolicies", "create") {
			return
		}
		var input domain.Strategy
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		strategy, errs := memory.CreateStrategy(input, roleFromRequest(c))
		if len(errs) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errs[0], "errors": errs})
			return
		}
		c.JSON(http.StatusCreated, strategy)
	}
}

func createDetectionHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "oneOffDetection", "execute") {
			return
		}
		var input domain.DetectionTask
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if input.Target == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "target 必填"})
			return
		}
		c.JSON(http.StatusCreated, memory.CreateDetection(input, roleFromRequest(c)))
	}
}

func getDetectionTaskHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "oneOffDetection", "read") {
			return
		}
		task, found := memory.GetDetectionTask(c.Param("id"))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "检测任务不存在"})
			return
		}
		c.JSON(http.StatusOK, task)
	}
}

func listDetectionTasksHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "oneOffDetection", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListDetectionTasks()})
	}
}

func listWorkordersHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		role := roleFromRequest(c)
		action := "read"
		if role == "Approver" {
			action = "approve"
		}
		if !requirePermission(c, "workorders", action) {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListWorkorders(role)})
	}
}

func batchWorkordersHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		Action string   `json:"action"`
		IDs    []string `json:"ids"`
	}
	return func(c *gin.Context) {
		var input request
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		action := "manage"
		if input.Action == "approve" || input.Action == "reject" {
			action = "approve"
		}
		if !requirePermission(c, "workorders", action) {
			return
		}
		items, message := memory.BatchWorkorders(input.IDs, input.Action, roleFromRequest(c))
		if message != "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": message})
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": items})
	}
}

func createWorkorderHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "workorders", "create") {
			return
		}
		var input domain.Workorder
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if input.Title == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "工单 title 必填"})
			return
		}
		c.JSON(http.StatusCreated, memory.CreateWorkorder(input, roleFromRequest(c)))
	}
}

func getWorkorderHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		role := roleFromRequest(c)
		action := "read"
		if role == "Approver" {
			action = "approve"
		}
		if !requirePermission(c, "workorders", action) {
			return
		}
		item, found := memory.GetWorkorder(c.Param("id"))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "工单不存在"})
			return
		}
		c.JSON(http.StatusOK, item)
	}
}

func transitionWorkorderHandler(memory store.Store, nextStatus string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "workorders", "approve") {
			return
		}

		item, found, err := memory.TransitionWorkorder(c.Param("id"), nextStatus)
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "workorder not found"})
			return
		}
		if err != nil {
			c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, item)
	}
}

func claimProbeTasksHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		ProbeID string `json:"probe_id"`
		Limit   int    `json:"limit"`
	}
	return func(c *gin.Context) {
		var input request
		_ = c.ShouldBindJSON(&input)
		if !authorizeProbeRequest(c, memory, input.ProbeID) {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ClaimProbeTasks(input.ProbeID, input.Limit)})
	}
}

func submitProbeResultHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input map[string]any
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		probeID, _ := input["probe_id"].(string)
		if !authorizeProbeRequest(c, memory, probeID) {
			return
		}
		task, found := memory.SubmitProbeResult(c.Param("task_id"), input, "probe")
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "任务不存在"})
			return
		}
		c.JSON(http.StatusOK, task)
	}
}

func authorizeProbeRequest(c *gin.Context, memory store.Store, probeID string) bool {
	headerProbeID := c.GetHeader("x-oneall-probe-id")
	token := bearerToken(c.GetHeader("authorization"))
	if headerProbeID == "" && token == "" {
		return true
	}
	if probeID == "" {
		probeID = headerProbeID
	}
	if headerProbeID != "" && probeID != "" && headerProbeID != probeID {
		c.JSON(http.StatusForbidden, gin.H{"error": "探针身份不一致"})
		return false
	}
	if !memory.ValidateProbeToken(probeID, token) {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "探针 token 无效"})
		return false
	}
	return true
}

func bearerToken(value string) string {
	const prefix = "Bearer "
	if len(value) >= len(prefix) && value[:len(prefix)] == prefix {
		return value[len(prefix):]
	}
	return value
}

func scheduleResultHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "accepted", "schedule_id": c.Param("schedule_id")})
	}
}

func listAlertsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "alertEvents", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListAlerts()})
	}
}

func getAlertHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "alertEvents", "read") {
			return
		}
		alert, found := memory.GetAlert(c.Param("id"))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "告警不存在"})
			return
		}
		c.JSON(http.StatusOK, alert)
	}
}

func batchAlertsHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		Action string   `json:"action"`
		IDs    []string `json:"ids"`
	}
	return func(c *gin.Context) {
		if !requirePermission(c, "alertEvents", "close") {
			return
		}
		var input request
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if input.Action != "close" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "不支持的告警批量动作"})
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.CloseAlerts(input.IDs, roleFromRequest(c))})
	}
}

func registerProbeHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "manage") {
			return
		}
		var input domain.ProbeNode
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if input.Name == "" || input.Region == "" || len(input.Capabilities) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "name、region、capabilities 必填"})
			return
		}
		c.JSON(http.StatusCreated, memory.RegisterProbe(input))
	}
}

func listProbesHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListProbes()})
	}
}

func listProbeHealthHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "read") {
			return
		}
		c.JSON(http.StatusOK, memory.ListProbeHealth(queryPositiveInt(c, "hours", 6), queryPositiveInt(c, "interval_minutes", 10)))
	}
}

func getProbeRuntimeHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "read") {
			return
		}
		runtime, found := memory.GetProbeRuntime(c.Param("id"))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, runtime)
	}
}

func heartbeatProbeHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !authorizeProbeRequest(c, memory, c.Param("id")) {
			return
		}
		var input domain.ProbeNode
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		probe, found := memory.HeartbeatProbe(c.Param("id"), input, "probe")
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, probe)
	}
}

func listProbeMetricsHistoryHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "read") {
			return
		}
		metrics, found := memory.ListProbeMetricsHistory(c.Param("id"), queryPositiveInt(c, "hours", 6), queryPositiveInt(c, "interval_minutes", 60))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, metrics)
	}
}

func refreshProbeConfigHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "manage") {
			return
		}
		probe, found := memory.RefreshProbeConfig(c.Param("id"), roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, probe)
	}
}

func listProbeConfigVersionsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "read") {
			return
		}
		items, found := memory.ListProbeConfigVersions(c.Param("id"))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": items})
	}
}

func rollbackProbeConfigHandler(memory store.Store) gin.HandlerFunc {
	type request struct {
		Version int `json:"version"`
	}
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "manage") {
			return
		}
		var input request
		_ = c.ShouldBindJSON(&input)
		probe, found := memory.RollbackProbeConfig(c.Param("id"), input.Version, roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, probe)
	}
}

func retireProbeHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "probeNodes", "manage") {
			return
		}
		probe, found := memory.RetireProbe(c.Param("id"), roleFromRequest(c))
		if !found {
			c.JSON(http.StatusNotFound, gin.H{"error": "探针不存在"})
			return
		}
		c.JSON(http.StatusOK, probe)
	}
}

func queryPositiveInt(c *gin.Context, key string, fallback int) int {
	raw := c.Query(key)
	if raw == "" {
		return fallback
	}
	value, err := strconv.Atoi(raw)
	if err != nil || value <= 0 {
		return fallback
	}
	return value
}

func listNotificationsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"items": memory.ListNotifications()})
	}
}

func notificationStreamHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"items": memory.ListNotifications(), "mode": "snapshot"})
	}
}

func listAuditLogsHandler(memory store.Store) gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "auditLogs", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": memory.ListAuditLogs()})
	}
}

func usersHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "usersAndRoles", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{
			{"id": "user-1", "name": "平台管理员", "role": "PlatformAdmin"},
			{"id": "user-2", "name": "值班工程师", "role": "OpsEngineer"},
			{"id": "user-3", "name": "审批人", "role": "Approver"},
		}})
	}
}

func dataSourcesHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "dataSources", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{{"id": "ds-1", "name": "蓝鲸 CMDB", "type": "blueking_cmdb", "status": "connected"}}})
	}
}

func credentialsHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "credentials", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{{"id": "cred-1", "name": "bk-prod-token", "type": "token", "masked_secret": "******"}}})
	}
}

func notificationChannelsHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "notificationsWebhooks", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{
			{"id": "chn-1", "name": "站内通知", "type": "site", "status": "enabled"},
			{"id": "chn-2", "name": "告警 Webhook", "type": "webhook", "status": "enabled"},
		}})
	}
}

func notificationTemplatesHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "notificationsWebhooks", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{
			{"id": "tpl-1", "name": "P0 告警通知", "channel": "site", "variables": []string{"alert_title", "asset", "severity"}},
			{"id": "tpl-2", "name": "工单流转通知", "channel": "site", "variables": []string{"workorder_id", "status"}},
		}})
	}
}

func webhooksHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "notificationsWebhooks", "read") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"items": []gin.H{{"id": "wh-1", "name": "默认 Webhook", "status": "enabled"}}})
	}
}

func webhookTestHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		if !requirePermission(c, "notificationsWebhooks", "update") {
			return
		}
		c.JSON(http.StatusOK, gin.H{"id": c.Param("id"), "status": "delivered"})
	}
}

func compileIPRegexHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		var input struct {
			Input string `json:"input"`
		}
		_ = c.ShouldBindJSON(&input)
		c.JSON(http.StatusOK, domain.CompileIPRegexFromText(input.Input))
	}
}

func expandIPRegexHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		var input struct {
			Regex string `json:"regex"`
			Limit int    `json:"limit"`
		}
		_ = c.ShouldBindJSON(&input)
		limit := input.Limit
		if raw := c.Query("limit"); raw != "" {
			if parsed, err := strconv.Atoi(raw); err == nil {
				limit = parsed
			}
		}
		c.JSON(http.StatusOK, domain.ExpandIPRegex(input.Regex, limit))
	}
}
