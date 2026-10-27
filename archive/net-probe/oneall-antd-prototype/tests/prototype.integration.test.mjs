import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const source = readFileSync(new URL('../src/main.tsx', import.meta.url), 'utf8');
const apiClientSource = readFileSync(new URL('../src/apiClient.ts', import.meta.url), 'utf8');
const navigationSource = readFileSync(new URL('../src/navigationContract.ts', import.meta.url), 'utf8');
const stylesSource = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
const packageSource = readFileSync(new URL('../package.json', import.meta.url), 'utf8');
const uiAuditSource = readFileSync(new URL('../scripts/audit-ui.mjs', import.meta.url), 'utf8');

test('prototype consumes the shared navigation contract', () => {
  assert.match(source, /navigationGroups/);
  assert.match(source, /isPageKey\(key\)/);
  assert.match(source, /getNavParentKey\(active\)/);
  assert.doesNotMatch(source, /const nextNavGroups = \[/);
});

test('prototype exposes model assets as the asset center entry', () => {
  assert.match(navigationSource, /label: '模型资产'/);
  assert.match(source, /businessAssetModels/);
  assert.match(source, /CMDB 域名/);
  assert.match(source, /Zabbix 主机/);
  assert.match(source, /IPMP 项目/);
  assert.match(source, /工单纳管主机信息/);
});

test('prototype does not restore fixed asset model navigation', () => {
  assert.doesNotMatch(source, /\['全部资产'|\['域名资产'|\['主机资产'|\['应用资产'/);
  assert.doesNotMatch(source, /label: '域名资产'|label: '主机资产'|label: '应用资产'/);
  assert.doesNotMatch(source, /value="domain"|value="host"|value="app"/);
});

test('prototype keeps model assets page focused on concrete data', () => {
  assert.doesNotMatch(source, /可选模型模板/);
  assert.doesNotMatch(source, /assetModelTemplates/);
  const assetsPage = source.match(/function AssetsPage\(\)[\s\S]*?function AssetModelManagementPage/)?.[0] ?? '';
  assert.doesNotMatch(assetsPage, /新增模型|编辑字段|同步配置|导入|导出|刷新|模型配置/);
  assert.match(assetsPage, /cmdb-model-sidebar/);
  assert.match(assetsPage, /asset-model-data-shell/);
  assert.doesNotMatch(assetsPage, /asset-legacy-summary/);
  assert.match(assetsPage, /全部字段/);
  assert.doesNotMatch(assetsPage, /title="模型资产"/);
  assert.doesNotMatch(assetsPage, /列显隐/);
  assert.doesNotMatch(assetsPage, /紧凑列宽|标准列宽|宽松列宽/);
  assert.doesNotMatch(assetsPage, /label: '关系'/);
  assert.match(assetsPage, /label: '变更记录'/);
  assert.match(assetsPage, /asset-table-head-title">操作/);
  assert.match(assetsPage, />新增实例</);
  assert.match(assetsPage, />查看</);
  assert.match(assetsPage, />编辑</);
  assert.match(assetsPage, />删除</);
});

test('prototype keeps CMDB scope to model assets and model management', () => {
  const navigationSource = readFileSync(new URL('../src/navigationContract.ts', import.meta.url), 'utf8');

  assert.match(navigationSource, /label: '模型管理'/);
  assert.doesNotMatch(navigationSource, /label: '模型关系'/);
  assert.doesNotMatch(navigationSource, /label: '业务拓扑'/);
  assert.match(source, /<AssetModelManagementPage \/>/);
  assert.doesNotMatch(source, /<AssetModelRelationsPage \/>/);
  assert.doesNotMatch(source, /<AssetTopologyPage \/>/);
  const managementPage = source.match(/function AssetModelManagementPage\(\)[\s\S]*?function AssetSyncPage/)?.[0] ?? '';
  assert.doesNotMatch(managementPage, /title="模型管理"/);
  assert.doesNotMatch(managementPage, /配置边界/);
  assert.doesNotMatch(managementPage, /当前模型/);
  assert.match(managementPage, /activeModelId/);
  assert.match(managementPage, /setActiveModelId\(record\.id\)/);
  assert.doesNotMatch(managementPage, /title=\{`\$\{activeModel\?\.name \?\? '模型'\} 字段清单`\}/);
  assert.match(managementPage, /字段配置/);
  assert.doesNotMatch(managementPage, /businessAssetModels\.flatMap/);
  assert.match(managementPage, /createAssetModel/);
  assert.match(managementPage, /updateAssetModel/);
  assert.match(managementPage, /deleteAssetModel/);
  assert.match(managementPage, /primaryKey/);
  assert.match(managementPage, /primary_key/);
  assert.match(managementPage, /removeEditorField/);
  assert.doesNotMatch(managementPage, />上移</);
  assert.doesNotMatch(managementPage, />下移</);
  assert.match(managementPage, /已被实例数据使用，不能删除/);
  assert.match(managementPage, /disabled/);
  assert.match(managementPage, /删除前会校验实例、同步任务、工单、告警和策略引用/);
  assert.match(managementPage, /platformDefault/);
  assert.match(managementPage, /平台默认/);
  assert.doesNotMatch(managementPage, /内置业务模型只读/);
  assert.doesNotMatch(managementPage, /导入模型定义/);
});

test('prototype makes asset sync a real model-bound workflow', () => {
  const syncPage = source.match(/function AssetSyncPage\(\)[\s\S]*?function useAssetModelsSnapshot/)?.[0] ?? '';
  assert.match(syncPage, /useAssetModelsSnapshot/);
  assert.match(syncPage, /listAssetSyncRuns/);
  assert.match(syncPage, /runAssetSync\(selectedModel\.id/);
  assert.match(syncPage, /selectedModel\?\.fields/);
  assert.match(syncPage, /fieldMapping/);
  assert.match(syncPage, /mappingRows/);
  assert.match(syncPage, /mappingErrors/);
  assert.match(syncPage, /脚本输出字段/);
  assert.match(syncPage, /选择文件/);
  assert.match(syncPage, /获取模板文件/);
  assert.match(syncPage, /保存配置/);
  assert.match(syncPage, /activeScriptId/);
  assert.match(syncPage, /applyScript/);
  assert.match(syncPage, /loadModelScriptDraft/);
  assert.match(syncPage, /activeScriptForSelectedModel/);
  assert.match(syncPage, /scripts\.find\(\(script\) => script\.model_id === model\.id\)/);
  assert.match(syncPage, /saveAssetSyncScript/);
  assert.match(syncPage, /listAssetSyncScripts/);
  assert.match(syncPage, /配置状态/);
  assert.match(syncPage, /脚本版本/);
  assert.match(syncPage, /scriptVersion/);
  assert.match(syncPage, /currentScriptVersion/);
  assert.match(syncPage, /currentScriptVersion = activeScriptForSelectedModel/);
  assert.match(syncPage, /hasSavedConfig/);
  assert.match(syncPage, /hasUnsavedChanges/);
  assert.match(syncPage, /canRunSync/);
  assert.match(syncPage, /configStatusText/);
  assert.match(syncPage, /有未保存变更/);
  assert.match(syncPage, /请先保存配置生成版本后再执行同步/);
  assert.match(syncPage, /当前配置有未保存变更，请先保存配置/);
  assert.match(syncPage, /disabled=\{!canRunSync\}/);
  assert.match(syncPage, /Python 脚本输出 records 列表/);
  assert.match(syncPage, /recordAssetSyncFailure/);
  assert.match(syncPage, /同步失败详情/);
  assert.match(syncPage, /错误分类/);
  assert.match(syncPage, /处理建议/);
  assert.match(syncPage, /查看失败详情/);
  assert.match(syncPage, /AntApp\.useApp/);
  assert.match(syncPage, /notificationApi\.error/);
  assert.match(syncPage, /notificationApi\.success/);
  assert.match(syncPage, /placement: 'topRight'/);
  assert.match(syncPage, /失败原因/);
  assert.match(syncPage, /按当前配置重新执行同步/);
  assert.match(syncPage, />重试</);
  assert.match(syncPage, /event_type\.includes\('failed'\)/);
  assert.match(syncPage, /执行同步/);
  assert.match(syncPage, /查看模型资产/);
  assert.match(syncPage, /notifySyncSuccess\(`写入/);
  assert.match(syncPage, /selectedModel\.id\)/);
  assert.match(syncPage, /oneall\.asset\.activeModelId/);
  assert.match(syncPage, /openAssetModel/);
  assert.doesNotMatch(syncPage, /className="model-message"/);
  assert.doesNotMatch(syncPage, /sync-inline-feedback/);
  assert.match(syncPage, /保存草稿/);
  assert.match(syncPage, /必映射/);
  assert.match(syncPage, /model: selectedModel/);
  assert.doesNotMatch(syncPage, /scriptId: activeScript\?\.id/);
  assert.doesNotMatch(syncPage, /保存配置前没有脚本标识/);
  assert.doesNotMatch(syncPage, /保存任务|保存脚本|新建任务|任务状态|脚本状态|按当前配置重试|createNewScriptDraft/);
  assert.doesNotMatch(syncPage, /dataSource=\{\[\]\}/);
  assert.doesNotMatch(syncPage, /已创建模型', value: 0/);
  assert.doesNotMatch(syncPage, /运行环境|超时秒数|日志级别|允许包|敏感参数|执行策略|executionPolicy/);
});

test('prototype keeps asset center usable without a live backend', () => {
  assert.match(apiClientSource, /LOCAL_ASSET_MODELS_KEY/);
  assert.match(apiClientSource, /LOCAL_ASSET_RECORDS_KEY/);
  assert.match(apiClientSource, /localCreateAssetModel/);
  assert.match(apiClientSource, /localUpdateAssetModel/);
  assert.match(apiClientSource, /localDeleteAssetModel/);
  assert.match(apiClientSource, /LOCAL_ASSET_MODEL_DELETIONS_KEY/);
  assert.match(apiClientSource, /localCreateAssetRecord/);
  assert.match(apiClientSource, /localUpdateAssetRecord/);
  assert.match(apiClientSource, /localDeleteAssetRecord/);
  assert.match(apiClientSource, /localPreviewAssetSync/);
  assert.match(apiClientSource, /localRunAssetSync/);
  assert.match(apiClientSource, /touchedIds/);
  assert.match(apiClientSource, /untouchedRows/);
  assert.match(apiClientSource, /updateCount/);
  assert.match(apiClientSource, /\[model\.id\]: \[\.\.\.syncedRows, \.\.\.untouchedRows\]/);
  assert.match(apiClientSource, /LOCAL_ASSET_SYNC_SCRIPTS_KEY/);
  assert.match(apiClientSource, /localSaveAssetSyncScript/);
  assert.match(apiClientSource, /listAssetSyncScripts/);
  assert.match(apiClientSource, /saveAssetSyncScript/);
  assert.match(apiClientSource, /sync-script-\$\{input\.model_id\}-\$\{Date\.now\(\)\}/);
  assert.match(apiClientSource, /ApiAssetSyncScriptVersion/);
  assert.match(apiClientSource, /script_versions/);
  assert.match(apiClientSource, /script_version/);
  assert.match(apiClientSource, /content_hash/);
  assert.match(apiClientSource, /mapping_hash/);
  assert.match(apiClientSource, /const changed = !latestVersion/);
  assert.match(apiClientSource, /changed \? \[nextVersion, \.\.\.currentVersions\]\.slice\(0, 20\) : currentVersions/);
  assert.match(apiClientSource, /recordAssetSyncFailure/);
  assert.match(apiClientSource, /localRecordAssetSyncFailure/);
  assert.match(apiClientSource, /error_type/);
  assert.match(apiClientSource, /error_message/);
  assert.match(apiClientSource, /suggestion/);
  assert.match(apiClientSource, /AssetSyncInput/);
  assert.doesNotMatch(apiClientSource, /ApiAssetSyncExecutionPolicy|execution_policy|secret_refs|allowed_packages|log_level/);
  assert.match(apiClientSource, /defaultSourceFieldKey/);
  assert.match(apiClientSource, /mapping/);
  assert.match(apiClientSource, /mergeLocalAssetModels/);
  assert.match(apiClientSource, /findLocalAssetModel\(modelId\)/);
  assert.match(apiClientSource, /writeLocalJson\(LOCAL_ASSET_RECORDS_KEY/);
  assert.match(apiClientSource, /listAssetRecords\(modelId\?: string\)/);
});

test('prototype exposes local fallbacks for remaining business loops', () => {
  for (const symbol of [
    'LOCAL_ALERTS_KEY',
    'LOCAL_WORKORDERS_KEY',
    'LOCAL_STRATEGIES_KEY',
    'LOCAL_PROBES_KEY',
    'LOCAL_DETECTIONS_KEY',
    'LOCAL_NOTIFICATIONS_KEY',
    'localCloseAlert',
    'localTransitionWorkorder',
    'localCreateStrategy',
    'localToggleStrategy',
    'localRegisterProbe',
    'localRefreshProbeConfig',
    'localRetireProbe',
    'localListProbeConfigVersions',
    'localRollbackProbeConfig',
    'localGetProbeRuntime',
    'localListProbeHealth',
    'localListProbeMetricsHistory',
    'localClaimProbeTasks',
    'localSubmitProbeTaskResult',
    'localCreateDetection',
    'localNotify'
  ]) {
    assert.match(apiClientSource, new RegExp(symbol));
  }
  assert.match(source, /closeAlertEvent\(closeTarget\.id, closeReason\.trim\(\) \|\| '人工确认恢复'\)\.then/);
  assert.match(source, /createMonitoringStrategy/);
  assert.match(source, /toggleMonitoringStrategy/);
  assert.match(source, /rejectWorkorder\(row\.id, reason\)\.then/);
  assert.match(source, /executeWorkorder\(workorder\.id\)/);
  assert.match(source, /completeWorkorder\(workorder\.id\)\.then/);
});

test('prototype completes IP helper probe and one-off detection workflows', () => {
  const detectionContractSource = readFileSync(new URL('../src/detectionContracts.ts', import.meta.url), 'utf8');
  const ipRegexSource = readFileSync(new URL('../src/ipRegexTool.ts', import.meta.url), 'utf8');
  const probesPage = source.match(/function ProbesPage\(\)[\s\S]*?function AssetsPage/)?.[0] ?? '';
  const detectionPage = source.match(/function DetectionPage\(\)[\s\S]*?function IpRegexToolPage/)?.[0] ?? '';
  const ipRegexPage = source.match(/function IpRegexToolPage\(\)[\s\S]*?function SettingsPage/)?.[0] ?? '';

  assert.match(ipRegexSource, /testIpAgainstRegex/);
  assert.match(ipRegexSource, /duplicateCount/);
  assert.match(ipRegexPage, /命中测试/);
  assert.match(ipRegexPage, /覆盖校验/);
  assert.match(ipRegexPage, /ip-regex-flow-block/);

  assert.match(detectionContractSource, /validateProbeRegistration/);
  assert.match(detectionContractSource, /validateDetectionInput/);
  assert.match(detectionContractSource, /buildDetectionRequest/);
  assert.match(apiClientSource, /localValidateCmdbDomain/);
  assert.match(apiClientSource, /network_type/);
  assert.match(apiClientSource, /certificate_days/);
  assert.match(apiClientSource, /cmdb_matched/);

  assert.match(probesPage, /注册探针/);
  assert.match(probesPage, /validateProbeRegistration/);
  assert.match(probesPage, /mode="multiple"/);
  assert.match(probesPage, /openProbeDetail/);
  assert.match(probesPage, /registeredProbe/);
  assert.match(probesPage, /接入信息/);
  assert.match(probesPage, /retireProbeNode/);
  assert.match(source, /refreshProbeConfig/);
  assert.match(source, /listProbeConfigVersions/);
  assert.match(source, /listProbeHealth/);
  assert.match(source, /getProbeRuntime/);
  assert.match(source, /listProbeMetricsHistory/);
  assert.match(source, /rollbackProbeConfig/);
  assert.match(source, /claimProbeTasks/);
  assert.match(source, /submitProbeTaskResult/);
  assert.match(source, /同步配置/);
  assert.match(source, /接入与配置/);
  assert.match(source, /资源快照/);
  assert.match(source, /指标历史/);
  assert.match(source, /配置版本/);
  assert.match(source, /领取任务/);
  assert.match(source, /回传成功/);
  assert.match(source, /心跳延迟/);
  assert.match(probesPage, /rememberDetailReturn\('probe', 'probes'\)/);
  assert.match(source, /key\.startsWith\('probes\/'\)/);
  assert.match(source, /getHashEntityId\('probes'\)/);
  assert.doesNotMatch(probesPage, /probe-auto-/);

  assert.match(detectionPage, /域名拨测/);
  assert.match(detectionPage, /证书检测/);
  assert.match(detectionPage, /CMDB 校验/);
  assert.match(detectionPage, /validateDetectionInput/);
  assert.match(detectionPage, /buildDetectionRequest/);
  assert.match(detectionPage, /mode="multiple"/);
  assert.match(detectionPage, /检测历史/);
  assert.match(detectionPage, /detection-history-body/);
  assert.doesNotMatch(source, /再次检测|再次检验/);
  assert.doesNotMatch(detectionPage, /蓝鲸 CMDB/);
  assert.doesNotMatch(detectionPage, /CMDB 校验只查询模型资产，不调度探针。/);
});

test('prototype keeps the whole platform on the legacy layout migration path', () => {
  const migration = readFileSync(new URL('../../oneall-redesign/09-legacy-layout-migration.md', import.meta.url), 'utf8');
  assert.match(migration, /所有一级和二级页面统一采用旧平台/);
  assert.match(migration, /所有页面的页面布局、信息密度、筛选区、表格位置、分页、详情抽屉和弹窗形式复刻旧 OneAll 平台/);
  assert.match(migration, /表格统一使用 AntD 原生 `Table`/);
  assert.match(migration, /列表页结构固定为：工具条 -> 可选摘要条 -> 表格 -> 底部分页/);
  assert.match(migration, /详情页结构固定为：详情标题 -> 基础信息区 -> 证据\/记录表格 -> 右侧时间线或动作区/);
  assert.match(stylesSource, /legacy-list-toolbar/);
  assert.doesNotMatch(stylesSource, /legacy-list-footer/);
  assert.match(stylesSource, /:where\(\.page, \.ant-modal, \.ant-drawer\) :where\(\.ant-table-container table\)/);
  assert.match(stylesSource, /:where\(\.page, \.ant-modal, \.ant-drawer\) :where\(\.ant-table-thead, \.ant-table-tbody\) > tr > :where\(th, td\)\.ant-table-cell:first-child/);
  assert.match(stylesSource, /:where\(\.page, \.ant-modal, \.ant-drawer\) :where\(\.ant-table-thead, \.ant-table-tbody\) > tr > :where\(th, td\)\.ant-table-cell:last-child/);
  assert.doesNotMatch(stylesSource, /linear-gradient|backdrop-filter|filter: blur/);
  assert.doesNotMatch(stylesSource, /box-shadow:\s*0\s+[1-9]/);
  assert.doesNotMatch(stylesSource, /\.setting-icon\s*\{[^}]*background:/);
  assert.match(source, /function SectionBlock/);
  assert.match(stylesSource, /\.section-block-title/);
  assert.doesNotMatch(source, /className="page-desc"|className="breadcrumb"|<Title level=\{3\}>/);
  assert.doesNotMatch(stylesSource, /\.page-header|\.page-desc|\.breadcrumb/);
  assert.match(source, /className="page-action-bar"/);
  assert.doesNotMatch(stylesSource, /\.settings-grid,\s*[\s\S]*?\.sync-page-shell,/);
  assert.match(source, /pagination=\{tablePagination\(20\)\}/);
  assert.match(stylesSource, /\.platform-table-panel/);
  assert.doesNotMatch(source, /className="legacy-list-footer"/);
  assert.doesNotMatch(source, /className="asset-legacy-footer"/);
  assert.doesNotMatch(source, /<Card className="filter-card"/);
  assert.match(stylesSource, /\.data-card\s*\{\s*border: 0;/);
  assert.doesNotMatch(source, /<Card/);
  assert.doesNotMatch(stylesSource, /\.ant-card/);
  assert.doesNotMatch(source, /className="asset-model-table"/);
});

test('prototype keeps full-route UI audit as an executable acceptance gate', () => {
  const pkg = JSON.parse(packageSource);

  assert.equal(pkg.scripts['audit:ui'], 'node scripts/audit-ui.mjs');
  assert.match(uiAuditSource, /src', 'navigationContract\.ts'/);
  assert.match(uiAuditSource, /viewport/);
  assert.match(uiAuditSource, /horizontal-overflow/);
  assert.match(uiAuditSource, /nested-cards/);
  assert.match(uiAuditSource, /too-many-titles/);
  assert.match(uiAuditSource, /console-warning-or-error/);
  assert.match(uiAuditSource, /output', 'ui-audit'/);
});

test('prototype keeps IP regex helper under the tools navigation group', () => {
  assert.match(source, /'ip-regex'/);
  assert.match(source, /<IpRegexToolPage \/>/);
  assert.doesNotMatch(source, /onClick=\{\(\) => switchPage\('ip-regex'\)\}>IP 正则助手/);
  assert.match(navigationSource, /module: '工具', label: 'IP 正则助手', level: 2, nav: true/);
});

test('prototype consumes domain contracts instead of hardcoding key business rules', () => {
  assert.match(source, /validateAlertRuleDsl\(httpAvailabilityRule\)/);
  assert.match(source, /previewAlertRule\(httpAvailabilityRule/);
  assert.match(source, /monitoringRequestDefaults/);
  assert.match(source, /buildMonitoringRequest/);
  assert.match(source, /canTransitionWorkorder\(row\.status, 'approved'\)/);
  assert.match(source, /hasPermission\(props\.currentRole, 'workorders', 'approve'\)/);
});

test('prototype keeps API role internal instead of exposing environment or role switchers in the topbar', () => {
  assert.match(source, /currentRole/);
  assert.doesNotMatch(source, /global-search/);
  assert.doesNotMatch(source, /搜索资产、告警、工单、策略、节点/);
  assert.doesNotMatch(source, /className="role-switch"/);
  assert.doesNotMatch(source, /<Dropdown menu=/);
  assert.doesNotMatch(source, /className="top-actions"[\s\S]*?<Select/);
  assert.match(source, /key=\{`\$\{active\}-\$\{currentRole\}`\}/);
  assert.match(source, /addEventListener\('hashchange'/);
  assert.match(apiClientSource, /export type ApiRole/);
  assert.match(apiClientSource, /getCurrentApiRole\(\)/);
  assert.doesNotMatch(apiClientSource, /headers: \{ 'x-oneall-role': 'OpsAdmin' \}/);
});

test('prototype reads permission catalog from backend with local contract fallback', () => {
  assert.match(apiClientSource, /\/api\/v1\/settings\/permissions\/catalog/);
  assert.match(source, /getPermissionCatalog\(\)/);
  assert.match(source, /catalog\?\.permissionMatrix \?\? localPermissionMatrix/);
  assert.match(source, /buildPermissionRows\(matrix\)/);
});

test('prototype separates data sources credentials and notification center pages', () => {
  assert.match(source, /<DataSourceManagementPage \/>/);
  assert.match(source, /<CredentialManagementPage \/>/);
  assert.match(source, /<NotificationCenterPage \/>/);
  assert.match(source, /canReferenceCredential/);
  assert.match(source, /maskCredential/);
  assert.match(source, /supportsNotificationEvent/);
  assert.doesNotMatch(source, /title="数据源与凭据"/);
});
