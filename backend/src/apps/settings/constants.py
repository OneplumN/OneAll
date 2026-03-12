AVAILABLE_PERMISSIONS = [
    {
        "key": "monitoring",
        "label": "监控",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "overview", "label": "概览", "actions": ["view"]},
            {"key": "todo", "label": "待办事项", "actions": ["view", "manage"]},
        ],
    },
    {
        "key": "detection",
        "label": "拨测",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "oneoff", "label": "一次性拨测", "actions": ["view", "create", "manage"]},
            {"key": "schedules", "label": "拨测监控申请", "actions": ["view", "create", "manage"]},
        ],
    },
    {
        "key": "probes",
        "label": "探针管理",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "nodes", "label": "节点", "actions": ["view", "create", "manage"]},
            {"key": "proxies", "label": "探针代理", "actions": ["view", "create", "manage"]},
        ],
    },
    {
        "key": "assets",
        "label": "资产中心",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "records", "label": "资产列表", "actions": ["view", "sync", "export"]},
        ],
    },
    {
        "key": "analytics",
        "label": "统计报表",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "reports", "label": "报表", "actions": ["view", "export", "schedule"]},
        ],
    },
    {
        "key": "tools",
        "label": "工具与代码库",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "library", "label": "工具库", "actions": ["view", "create", "manage"]},
            {"key": "repository", "label": "代码库", "actions": ["view", "create", "manage"]},
        ],
    },
    {
        "key": "knowledge",
        "label": "知识库",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "articles", "label": "文章", "actions": ["view", "create", "manage"]},
        ],
    },
    {
        "key": "alerts",
        "label": "告警",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "channels", "label": "通道配置", "actions": ["view", "update", "test"]},
            {"key": "templates", "label": "通知模板", "actions": ["view", "create", "update", "delete"]},
        ],
    },
    {
        "key": "integrations",
        "label": "集成中心",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "hub", "label": "插件中心", "actions": ["view", "toggle", "configure"]},
        ],
    },
    {
        "key": "settings",
        "label": "系统设置",
        "children": [
            {"key": "module", "label": "模块入口", "actions": ["access"]},
            {"key": "system", "label": "全局设置", "actions": ["view", "manage"]},
            {"key": "users", "label": "用户管理", "actions": ["view", "create", "manage"]},
            {"key": "roles", "label": "角色管理", "actions": ["view", "create", "manage"]},
            {"key": "audit_log", "label": "操作日志", "actions": ["view", "manage"]},
        ],
    },
]
