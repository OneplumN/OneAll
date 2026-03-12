from django.urls import path

from .code_repository_views import (
    CodeDirectoryDetailView,
    CodeDirectoryListCreateView,
    CodeRepositoryDetailView,
    CodeRepositoryListCreateView,
    CodeRepositoryVersionListCreateView,
    CodeRepositoryVersionRollbackView,
    CodeRepositoryExecuteView,
)
from .repository_views import RepositoryRollbackView, RepositoryUploadView
from .script_plugin_views import ScriptPluginDetailView, ScriptPluginExecuteView, ScriptPluginListView
from .tool_views import (
    ToolDefinitionListCreateView,
    ToolExecutionListView,
    ToolExecuteView,
    ToolScriptVersionCreateView,
)
from .ip_regex_views import IPRegexCompileView, IPRegexReverseView

urlpatterns = [
    path("tools/definitions", ToolDefinitionListCreateView.as_view(), name="tools-definitions"),
    path(
        "tools/definitions/<uuid:tool_id>/versions",
        ToolScriptVersionCreateView.as_view(),
        name="tools-definition-versions",
    ),
    path("tools/definitions/<uuid:tool_id>/execute", ToolExecuteView.as_view(), name="tools-definition-execute"),
    path("tools/executions", ToolExecutionListView.as_view(), name="tools-executions"),
    path("tools/repository/upload", RepositoryUploadView.as_view(), name="tools-repository-upload"),
    path("tools/repository/rollback", RepositoryRollbackView.as_view(), name="tools-repository-rollback"),
    path("code/directories", CodeDirectoryListCreateView.as_view(), name="code-directories"),
    path("code/directories/<slug:key>", CodeDirectoryDetailView.as_view(), name="code-directory-detail"),
    path("tools/repositories", CodeRepositoryListCreateView.as_view(), name="code-repository-list"),
    path("tools/repositories/<uuid:repository_id>", CodeRepositoryDetailView.as_view(), name="code-repository-detail"),
    path(
        "tools/repositories/<uuid:repository_id>/versions",
        CodeRepositoryVersionListCreateView.as_view(),
        name="code-repository-versions",
    ),
    path(
        "tools/repositories/<uuid:repository_id>/versions/<uuid:version_id>/rollback",
        CodeRepositoryVersionRollbackView.as_view(),
        name="code-repository-version-rollback",
    ),
    path(
        "tools/repositories/<uuid:repository_id>/execute",
        CodeRepositoryExecuteView.as_view(),
        name="code-repository-execute",
    ),
    path("tools/ip-regex/compile", IPRegexCompileView.as_view(), name="tools-ip-regex-compile"),
    path("tools/ip-regex/expand", IPRegexReverseView.as_view(), name="tools-ip-regex-expand"),
    path("tools/script-plugins", ScriptPluginListView.as_view(), name="tools-script-plugins"),
    path("tools/script-plugins/<slug:slug>", ScriptPluginDetailView.as_view(), name="tools-script-plugins-detail"),
    path("tools/script-plugins/<slug:slug>/execute", ScriptPluginExecuteView.as_view(), name="tools-script-plugins-execute"),
]
