<template>
  <div :class="['code-repository', { 'code-repository--detail': detailMode || createMode }]">
    <section class="repository-panel">
      <div class="repository-body">
        <aside
          class="repository-aside"
          :style="{ width: sidebarWidth }"
        >
          <div class="layout__aside-scroll">
            <el-menu
              v-if="directoryGroups.length"
              class="layout__menu layout__menu--local"
              :default-active="selectedDirectoryKey"
              :collapse="sidebarCollapsed"
              :collapse-transition="false"
              @select="handleDirectorySelect"
            >
              <el-tooltip
                v-for="group in directoryGroups"
                :key="group.key"
                class="nav-entry__tooltip"
                effect="dark"
                placement="right"
                :content="group.title"
                :disabled="!sidebarCollapsed"
                popper-class="layout__nav-tooltip-popper"
              >
                <el-menu-item
                  :index="group.key"
                  class="nav-entry"
                >
                  <div class="nav-entry__icon">
                    <component :is="resolveDirectoryIcon(group.key)" />
                  </div>
                  <span class="nav-entry__label">{{ group.title }}</span>
                </el-menu-item>
              </el-tooltip>
            </el-menu>
            <div v-else class="sidebar-placeholder">
              <p>暂无目录，请联系管理员配置</p>
            </div>
          </div>
          <div class="aside__footer layout__aside-footer">
            <el-button
              class="layout__toggle"
              text
              @click="sidebarCollapsed = !sidebarCollapsed"
            >
              <el-icon>
                <component :is="sidebarCollapsed ? Expand : Fold" />
              </el-icon>
            </el-button>
          </div>
        </aside>

        <div class="repository-main" v-if="!detailMode && !createMode">
          <div class="repository-header">
            <div class="repository-header__info">
              <span class="header__title">{{ primaryNavTitle }}</span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">{{ currentDirectoryName }}</span>
              <template v-if="detailRepository">
                <span class="header__separator">/</span>
                <span class="header__subtitle">{{ detailRepository.name }}</span>
              </template>
            </div>
            <div class="repository-header__actions">
              <el-dropdown
                trigger="click"
                class="directory-actions"
                @command="handleDirectoryCommand"
              >
                <span class="dropdown-trigger">
                  <el-icon><Setting /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="manageDirectories">管理目录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <div class="refresh-card" @click="loadRepositories">
                <el-icon class="refresh-icon" :class="{ spinning: loading.repositories }"><Refresh /></el-icon>
                <span>刷新</span>
              </div>
            </div>
          </div>
          <div class="repository-filters">
            <div class="filters-left">
              <el-button
                class="toolbar-button toolbar-button--primary"
                type="primary"
                :disabled="!canCreate || !directoryOptions.length"
                @click="openCreateDialog"
              >
                新建脚本
              </el-button>
            </div>
            <div class="filters-right">
              <el-select v-model="languageFilter" class="pill-input narrow-select">
                <el-option label="全部语言" value="all" />
                <el-option
                  v-for="option in LANGUAGE_OPTIONS"
                  :key="option"
                  :label="option"
                  :value="option.toLowerCase()"
                />
              </el-select>
              <el-input
                v-model="repoKeyword"
                placeholder="搜索脚本名称 / 标签"
                clearable
                class="search-input pill-input search-input--compact"
              >
                <template #prefix>
                  <i class="el-icon-search"></i>
                </template>
              </el-input>
            </div>
          </div>

          <div class="repository-table">
            <div class="repository-table__card">
	              <el-table
	                height="100%"
	                :data="paginatedRepos"
	                v-loading="loading.repositories"
	                stripe
	                :header-cell-style="tableHeaderStyle"
	                :cell-style="tableCellStyle"
	                :row-class-name="rowClassName"
	                @sort-change="handleSortChange"
	              >
                <template #empty>
                  <div class="table-empty">
                    <p>该目录暂无脚本</p>
                  </div>
                </template>
                <el-table-column prop="name" label="脚本名称" min-width="160" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="repository-name" @click.stop="handleView(row)">{{ row.name }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="language" label="语言" width="90" />
                <el-table-column label="标签" min-width="140" show-overflow-tooltip>
                  <template #default="{ row }">
                    <el-space>
                      <el-tag v-for="tag in row.tags" :key="tag" size="small" round>{{ tag }}</el-tag>
                    </el-space>
                  </template>
                </el-table-column>
                <el-table-column label="最新版本" width="110" min-width="110" show-overflow-tooltip>
                  <template #default="{ row }">
                    {{ row.latest_version || '未发布' }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="updated_at"
                  label="更新时间"
                  width="160"
                  show-overflow-tooltip
                  sortable="custom"
                >
                  <template #default="{ row }">
                    {{ formatTime(row.updated_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="160">
                  <template #default="{ row }">
                    <el-space size="small">
                      <el-button text size="small" :disabled="!canManage" @click.stop="handleEdit(row)">编辑</el-button>
                      <el-button text type="danger" size="small" :disabled="!canManage" @click.stop="handleDelete(row)">删除</el-button>
                    </el-space>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
          <div class="repository-table__footer">
            <div class="footer-left">
              <div class="repository-stats">共 {{ filteredCurrentRepos.length }} 条</div>
              <el-pagination
                class="repository-pagination__sizes"
                :total="filteredCurrentRepos.length"
                :current-page="currentPage"
                :page-size="pageSize"
                :page-sizes="pageSizeOptions"
                layout="sizes"
                background
                @size-change="handlePageSizeChange"
                @current-change="handlePageChange"
              />
            </div>
            <div class="footer-right">
              <el-pagination
                class="repository-pagination__pager"
                :total="filteredCurrentRepos.length"
                :current-page="currentPage"
                :page-size="pageSize"
                layout="prev, pager, next"
                background
                @current-change="handlePageChange"
              />
            </div>
          </div>
        </div>

        <div class="repository-main" v-else-if="createMode">
          <div class="repository-header">
            <div class="repository-header__info">
              <span class="header__title">{{ primaryNavTitle }}</span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">{{ currentDirectoryName }}</span>
              <span class="header__separator">/</span>
              <span class="header__subtitle">新建脚本</span>
            </div>
            <div class="repository-header__actions">
              <el-button class="toolbar-button" @click="exitCreateMode">返回列表</el-button>
              <el-button
                class="toolbar-button toolbar-button--primary"
                type="primary"
                :disabled="!canCreate"
                :loading="loading.creating"
                @click="handleCreateInline"
              >
                保存
              </el-button>
            </div>
          </div>
          <div class="repository-detail-page">
            <div class="detail-layout">
              <div class="detail-left" :class="{ fullscreen: detailCodeFullscreen }">
                <div class="detail-card__header detail-left__header">
                  <h4 class="section-title">脚本代码</h4>
                  <div class="detail-actions">
                    <el-button text @click="toggleDetailFullscreen">
                      {{ detailCodeFullscreen ? '退出全屏' : '全屏' }}
                    </el-button>
                  </div>
                </div>
                <div class="detail-code-wrapper">
                  <CodeEditor
                    v-model="createForm.content"
                    :language="createForm.language"
                    :placeholder="codePlaceholder(createForm.language)"
                    height="100%"
                    :show-fullscreen-button="false"
                  />
                </div>
              </div>
              <div class="detail-right">
                <div class="detail-card">
                  <div class="detail-card__header">
                    <h4>基本信息</h4>
                  </div>
                  <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="80px" class="detail-form">
                    <el-form-item label="名称" prop="name">
                      <el-input v-model="createForm.name" placeholder="脚本名称或业务标识" />
                    </el-form-item>
                    <el-form-item label="语言" prop="language">
                      <el-select v-model="createForm.language" placeholder="选择语言">
                        <el-option
                          v-for="option in LANGUAGE_OPTIONS"
                          :key="option"
                          :label="option"
                          :value="option"
                        />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="目录" prop="directory">
                      <el-select v-model="createForm.directory" placeholder="选择目录">
                        <el-option
                          v-for="dir in directoryOptions"
                          :key="dir.key"
                          :label="dir.title"
                          :value="dir.key"
                        />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="标签" prop="tags">
                      <el-select
                        v-model="createForm.tags"
                        multiple
                        allow-create
                        filterable
                        placeholder="添加标签用于目录分类"
                      />
                    </el-form-item>
                    <el-form-item label="描述">
                      <el-input
                        v-model="createForm.description"
                        type="textarea"
                        :rows="3"
                        placeholder="描述脚本用途、依赖和注意事项"
                      />
                    </el-form-item>
                    <el-form-item label="变更">
                      <el-input
                        v-model="createForm.change_log"
                        type="textarea"
                        :rows="3"
                        placeholder="说明变更原因或脚本来源"
                      />
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="repository-main" v-else>
            <div class="repository-header">
              <div class="repository-header__info">
                <span class="header__title">{{ primaryNavTitle }}</span>
                <span class="header__separator">/</span>
                <span class="header__subtitle clickable" @click="navigateToDirectory(selectedDirectoryKey || '')">
                  {{ currentDirectoryName }}
                </span>
                <span class="header__separator">/</span>
                <span class="header__subtitle">{{ detailRepository?.name || '脚本详情' }}</span>
              </div>
            <div class="repository-header__actions">
              <el-button class="toolbar-button" @click="exitDetailMode">返回列表</el-button>
              <el-button
                class="toolbar-button toolbar-button--primary"
                type="primary"
                :disabled="!canManage || !canCreate || !detailRepository"
                :loading="loading.updating"
                @click="handleSaveAndRecord"
              >
                保存并记录版本
              </el-button>
            </div>
          </div>
          <div class="repository-detail-page" v-if="detailRepository">
            <div class="detail-layout">
                <div class="detail-left" :class="{ fullscreen: detailCodeFullscreen }">
                    <div class="detail-card__header detail-left__header">
                      <h4 class="section-title">脚本代码</h4>
                      <div class="detail-actions">
                        <el-button text @click="toggleDetailFullscreen">
                          {{ detailCodeFullscreen ? '退出全屏' : '全屏' }}
                        </el-button>
                      </div>
                    </div>
                  <div class="detail-code-wrapper">
                    <CodeEditor
                      v-model="detailRepository.content"
                      :language="detailRepository.language"
                      placeholder="暂无代码"
                      height="100%"
                      :show-fullscreen-button="false"
                    />
                  </div>
                </div>
              <div class="detail-right">
                <div class="detail-card">
                  <div class="detail-card__header">
                    <h4>基本信息</h4>
                  </div>
                  <el-form label-width="80px" class="detail-form">
                    <el-form-item label="名称">
                      <el-input v-model="detailRepository.name" @change="markDetailDirty" />
                    </el-form-item>
                    <el-form-item label="语言">
                      <el-select v-model="detailRepository.language" @change="markDetailDirty">
                        <el-option
                          v-for="option in LANGUAGE_OPTIONS"
                          :key="option"
                          :label="option"
                          :value="option"
                        />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="目录">
                      <el-select v-model="detailRepository.directory" @change="markDetailDirty">
                        <el-option
                          v-for="dir in directoryOptions"
                          :key="dir.key"
                          :label="dir.title"
                          :value="dir.key"
                        />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="标签">
                      <el-select
                        v-model="detailRepository.tags"
                        multiple
                        allow-create
                        filterable
                        @change="markDetailDirty"
                      />
                    </el-form-item>
                    <el-form-item label="描述">
                      <el-input v-model="detailRepository.description" type="textarea" :rows="3" @change="markDetailDirty" />
                    </el-form-item>
                  </el-form>
                </div>

                <div class="detail-card">
                  <div class="detail-card__header">
                    <h4>版本迭代</h4>
                    <el-tag v-if="detailRepository.latest_version" type="info" size="small">
                      当前：{{ detailRepository.latest_version }}
                    </el-tag>
                  </div>
                  <el-timeline v-if="versions.length">
                    <el-timeline-item
                      v-for="version in versions"
                      :key="version.id"
                      :timestamp="formatTime(version.created_at)"
                    >
                      <div class="timeline-item">
                        <strong>{{ version.version }}</strong>
                        <span class="muted">作者：{{ version.created_by || '未知' }}</span>
                        <p>{{ version.summary || version.change_log || '未填写说明' }}</p>
                        <button class="text-btn" type="button" :disabled="!canManage" @click="handleRollback(version)">回滚到此版本</button>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                  <el-empty v-else description="暂无版本记录" />
                </div>

                <div class="detail-card danger">
                  <div class="detail-card__header">
                    <h4>危险操作</h4>
                  </div>
                  <el-button type="danger" plain :disabled="!canManage" @click="handleDelete(detailRepository)">
                    删除脚本
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="未选择脚本" />
        </div>
      </div>
    </section>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑脚本"
      width="640px"
      class="dialog-shell"
      @closed="editFormRef?.resetFields()"
    >
      <el-form :model="editForm" label-width="120px" ref="editFormRef">
        <el-form-item label="仓库名称" prop="name">
          <el-input v-model="editForm.name" placeholder="脚本名称或业务标识" />
        </el-form-item>
        <el-form-item label="脚本语言" prop="language">
          <el-select v-model="editForm.language" placeholder="选择语言">
            <el-option
              v-for="option in LANGUAGE_OPTIONS"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类标签">
          <el-select
            v-model="editForm.tags"
            multiple
            allow-create
            filterable
            placeholder="添加标签"
          />
        </el-form-item>
        <el-form-item label="所属目录">
          <el-select v-model="editForm.directory" placeholder="选择目录">
            <el-option
              v-for="dir in directoryOptions"
              :key="dir.key"
              :label="dir.title"
              :value="dir.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="仓库说明">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="描述脚本用途、依赖和注意事项"
          />
        </el-form-item>
        <el-form-item label="脚本代码" label-position="top">
          <CodeEditor
            v-model="editForm.content"
            :language="editForm.language"
            placeholder="在此粘贴或编辑脚本内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading.updating" @click="submitEdit">保存修改</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="uploadDrawerVisible"
      :title="`记录版本 - ${selectedRepository?.name || ''}`"
      width="520px"
      class="dialog-shell"
      center
      @closed="resetUploadForm"
    >
      <el-form :model="uploadForm" label-width="120px" :rules="uploadRules" ref="uploadFormRef">
        <el-form-item label="版本号" prop="version">
          <el-input v-model="uploadForm.version" placeholder="例如 v1.1.0" />
        </el-form-item>
        <el-form-item label="变更说明">
          <el-input v-model="uploadForm.change_log" type="textarea" :rows="3" placeholder="描述本次改动" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading.uploading" @click="submitUpload">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="directoryManagerVisible"
      title="管理目录"
      width="720px"
      class="dialog-shell"
      destroy-on-close
    >
      <el-form :model="directoryForm" label-width="100px" :rules="directoryFormRules" ref="directoryFormRef">
        <el-form-item label="目录名称" prop="title">
          <el-input v-model="directoryForm.title" placeholder="请输入目录名称" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="directoryForm.keywordsInput"
            placeholder="用逗号分隔的关键词，例如: 资产, CMDB"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="directory-manager__actions">
          <div class="left-actions">
            <el-button @click="resetDirectoryForm">重置</el-button>
          </div>
          <div class="right-actions">
            <el-button @click="directoryManagerVisible = false">取消</el-button>
            <el-button type="primary" :loading="loading.directoryManaging" @click="submitDirectorySave">
              {{ editingDirectoryKey ? '保存修改' : '新增目录' }}
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="availableDirectories" size="small" style="margin-top: 12px">
        <el-table-column prop="title" label="名称" min-width="160" />
        <el-table-column label="关键词" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-space wrap>
              <el-tag v-for="kw in row.keywords" :key="kw" size="small">{{ kw }}</el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-space size="small">
              <el-button text size="small" :disabled="!canManage" @click="startEditDirectory(row)">编辑</el-button>
              <el-button
                text
                type="danger"
                size="small"
                :disabled="!canManage || row.builtin"
                @click="handleDeleteDirectory(row)"
              >
                删除
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import bash from 'highlight.js/lib/languages/bash';
import powershell from 'highlight.js/lib/languages/powershell';
import go from 'highlight.js/lib/languages/go';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import java from 'highlight.js/lib/languages/java';
import xml from 'highlight.js/lib/languages/xml';
import yamlLang from 'highlight.js/lib/languages/yaml';
import json from 'highlight.js/lib/languages/json';
import sql from 'highlight.js/lib/languages/sql';
	import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type Component } from 'vue';
import {
  Expand,
  Fold,
  Monitor,
  Collection,
  DataAnalysis,
  Tools,
  Reading,
  Document,
  Setting,
  Refresh
} from '@element-plus/icons-vue';

import {
  createRepository,
  deleteRepository,
  listRepositories,
  listVersions,
  rollbackVersion,
  updateRepository,
  uploadVersion,
  type CreateRepositoryPayload,
  type ScriptRepository,
  type ScriptVersion,
  type UpdateRepositoryPayload,
  type UploadVersionPayload,
  createCodeDirectory,
  updateCodeDirectory,
  deleteCodeDirectory
} from '@/services/codeRepositoryApi';
import CodeEditor from '@/components/CodeEditor.vue';
import { usePageTitle } from '@/composables/usePageTitle';
	import '@/styles/highlight-theme.css';
	import { useSessionStore } from '@/stores/session';
	import { useCodeDirectoryStore, type DirectoryPreset } from '@/stores/codeDirectories';
	import { useAppStore } from '@/stores/app';
	import { useRoute, useRouter } from 'vue-router';

hljs.registerLanguage('python', python);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('shell', bash);
hljs.registerLanguage('powershell', powershell);
hljs.registerLanguage('go', go);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('java', java);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('yaml', yamlLang);
hljs.registerLanguage('json', json);
hljs.registerLanguage('sql', sql);

	usePageTitle('代码管理');

	const route = useRoute();
	const router = useRouter();
	const sessionStore = useSessionStore();
	const codeDirectoryStore = useCodeDirectoryStore();
	const appStore = useAppStore();
const canCreate = computed(() => sessionStore.hasPermission('tools.repository.create'));
const canManage = computed(() => sessionStore.hasPermission('tools.repository.manage'));
const primaryNavTitle = computed(() => {
  const matched = route.matched?.[0];
  return (matched?.meta?.title as string) || (route.meta?.title as string) || '代码管理';
});
const parseKeywords = (value: string) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const handleDirectoryCommand = (command: string) => {
  if (command === 'manageDirectories') {
    openDirectoryManager();
  }
};

interface DirectoryGroup extends DirectoryPreset {
  repos: ScriptRepository[];
}

const LANGUAGE_OPTIONS = [
  'Python',
  'Shell',
  'PowerShell',
  'Go',
  'JavaScript',
  'TypeScript',
  'Java',
  'C#',
  'C++',
  'Rust',
  'SQL',
  'XML',
  'YAML',
  'JSON',
  'Bash'
];

const LANGUAGE_HIGHLIGHT_MAP: Record<string, string> = {
  python: 'python',
  shell: 'bash',
  bash: 'bash',
  powershell: 'powershell',
  go: 'go',
  javascript: 'javascript',
  typescript: 'typescript',
  ts: 'typescript',
  js: 'javascript',
  java: 'java',
  xml: 'xml',
  yaml: 'yaml',
  yml: 'yaml',
  json: 'json',
  sql: 'sql'
};

const UNUSED_TAGS = ['用户自定义目录'];
const cleanTags = (tags?: string[]) => {
  const normalized = (tags || [])
    .map((tag) => tag?.trim())
    .filter((tag) => tag && !UNUSED_TAGS.includes(tag));
  return Array.from(new Set(normalized));
};

const repositories = ref<ScriptRepository[]>([]);
const versions = ref<ScriptVersion[]>([]);
const directories = computed(() => codeDirectoryStore.directories);
const BLOCKED_DIRECTORY_TITLES = ['用户自定义目录'];
const filteredDirectories = computed(() =>
  directories.value.filter((dir) => !BLOCKED_DIRECTORY_TITLES.includes((dir.title || '').trim()))
);
const availableDirectories = computed(() =>
  filteredDirectories.value.length ? filteredDirectories.value : directories.value
);
const DIRECTORY_ICON_MAP: Record<string, Component> = {
  probe: Monitor,
  assets: Collection,
  monitoring: DataAnalysis,
  tools: Tools,
  general: Reading
};

const loading = reactive({
  repositories: false,
  creating: false,
  updating: false,
  uploading: false,
  versions: false,
  directoryManaging: false
});

const editDialogVisible = ref(false);
const uploadDrawerVisible = ref(false);
const directoryManagerVisible = ref(false);
const sidebarCollapsed = ref(false);
const sidebarWidth = computed(() => (sidebarCollapsed.value ? '72px' : '240px'));

const createFormRef = ref<FormInstance>();
const editFormRef = ref<FormInstance>();
const uploadFormRef = ref<FormInstance>();
const directoryFormRef = ref<FormInstance>();

const selectedDirectoryKey = ref<string>('');
const selectedRepository = ref<ScriptRepository | null>(null);
const detailRepository = ref<ScriptRepository | null>(null);
const showCreateMode = ref(false);
const repoKeyword = ref('');
const languageFilter = ref<string>('all');

const createForm = reactive<CreateRepositoryPayload>({
  name: '',
  language: '',
  tags: [],
  description: '',
  content: '',
  change_log: '',
  directory: ''
});

const editForm = reactive<UpdateRepositoryPayload & { id?: string }>({
  name: '',
  language: '',
  tags: [],
  description: '',
  directory: '',
  content: ''
});

const uploadForm = reactive<UploadVersionPayload>({
  version: '',
  content: '',
  change_log: ''
});

const directoryForm = reactive<{ title: string; keywordsInput: string }>({
  title: '',
  keywordsInput: ''
});
const editingDirectoryKey = ref<string | null>(null);

const directoryFormRules: FormRules = {
  title: [{ required: true, message: '请输入目录名称', trigger: 'blur' }]
};

const createRules: FormRules<CreateRepositoryPayload> = {
  name: [{ required: true, message: '请输入仓库名称', trigger: 'blur' }],
  language: [{ required: true, message: '请选择脚本语言', trigger: 'change' }],
  tags: [
    { type: 'array', required: true, message: '至少添加一个标签', trigger: 'change' }
  ],
  directory: [{ required: true, message: '请选择目录', trigger: 'change' }],
  content: [{ required: true, message: '请填写初始脚本内容', trigger: 'blur' }]
};

const uploadRules: FormRules<UploadVersionPayload> = {
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }]
};

const matchDirectoryKey = (repo: ScriptRepository) => {
  const explicit = (repo as any).directory;
  if (explicit) return explicit as string;
  const text = [
    repo.name,
    repo.language,
    ...(repo.tags || [])
  ]
    .join(' ')
    .toLowerCase();
  const preset = availableDirectories.value.find((item) =>
    item.keywords.some((keyword) => text.includes(keyword.toLowerCase()))
  );
  return preset?.key || availableDirectories.value[0]?.key || '';
};

const directoryMap = computed<Record<string, DirectoryPreset>>(() => {
  const map: Record<string, DirectoryPreset> = {};
  availableDirectories.value.forEach((dir) => {
    map[dir.key] = dir;
  });
  return map;
});

const directoryGroups = computed<DirectoryGroup[]>(() => {
  return availableDirectories.value.map((preset) => ({
    ...preset,
    repos: repositories.value.filter((repo) => matchDirectoryKey(repo) === preset.key)
  }));
});

const badgeFromTitle = (title: string) => {
  if (!title) return '#';
  const alphanumeric = title.match(/[A-Za-z0-9]/);
  if (alphanumeric && alphanumeric[0]) {
    return alphanumeric[0].toUpperCase();
  }
  return title.charAt(0);
};

const resolveDirectoryIcon = (key: string): Component => {
  return DIRECTORY_ICON_MAP[key] || Document;
};

const currentDirectory = computed<DirectoryGroup | null>(() => {
  const groups = directoryGroups.value;
  if (!groups.length || !selectedDirectoryKey.value) return null;
  return groups.find((group) => group.key === selectedDirectoryKey.value) ?? null;
});

const currentDirectoryName = computed(() => {
  if (!currentDirectory.value) return '脚本目录';
  const title = currentDirectory.value.title;
  return title.includes('用户自定义目录') ? '脚本目录' : title;
});

const currentRepos = computed(() => currentDirectory.value?.repos ?? []);
const filteredCurrentRepos = computed(() => {
  const keyword = repoKeyword.value.trim().toLowerCase();
  const langFilter = languageFilter.value;
  return currentRepos.value
    .filter((repo) => {
      if (langFilter === 'all') return true;
      return (repo.language || '').toLowerCase() === langFilter;
    })
    .filter((repo) => {
      if (!keyword) return true;
      return (
        repo.name.toLowerCase().includes(keyword) ||
        (repo.description || '').toLowerCase().includes(keyword) ||
        repo.tags.some((tag) => tag.toLowerCase().includes(keyword))
      );
    });
});

const pageSizeOptions = [10, 20, 50];
const pageSize = ref(20);
const currentPage = ref(1);
const sortState = reactive<{ prop: string; order: 'ascending' | 'descending' | null }>({
  prop: 'updated_at',
  order: 'descending'
});

const sortedRepos = computed(() => {
  const list = [...filteredCurrentRepos.value];
  if (!sortState.prop || !sortState.order) return list;
  return list.sort((a: any, b: any) => {
    const prop = sortState.prop as keyof ScriptRepository;
    const va = a[prop];
    const vb = b[prop];
    if (va === vb) return 0;
    if (va === undefined || va === null) return 1;
    if (vb === undefined || vb === null) return -1;
    const result = va > vb ? 1 : -1;
    return sortState.order === 'ascending' ? result : -result;
  });
});
const paginatedRepos = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return sortedRepos.value.slice(start, start + pageSize.value);
});
const detailMode = computed(() => !!detailRepository.value);
const createMode = computed(() => showCreateMode.value);
watch(
  () => ({ detail: detailMode.value, create: createMode.value }),
  ({ detail, create }) => {
    // 列表：不出现外层滚动条（表格 body 内滚）；详情/新建：由主内容区滚动（左侧目录 sticky 固定）
    appStore.setMainScrollLocked(!detail && !create);
  },
  { immediate: true, deep: true }
);
onBeforeUnmount(() => {
  appStore.setMainScrollLocked(false);
});
const detailDirty = reactive({
  meta: false,
  code: false
});
const codePlaceholder = (lang?: string) => {
  const key = (lang || '').toLowerCase();
  if (key === 'python') return "#!/usr/bin/env python3\nprint('Hello OneAll')";
  if (key === 'shell' || key === 'bash') return '#!/bin/bash\n# 在此编写 Shell 脚本';
  if (key === 'powershell') return '# PowerShell script';
  if (key === 'go') return 'package main\n\nfunc main() {\n    // TODO\n}';
  if (key === 'javascript' || key === 'typescript') return '// JS/TS 脚本入口';
  return '在此粘贴或编写脚本代码';
};
const openRepoFromQuery = () => {
  const repoId = typeof route.query.repoId === 'string' ? route.query.repoId : '';
  if (!repoId) return;
  if (createMode.value) return;
  const target = repositories.value.find((repo) => repo.id === repoId);
  if (target && detailRepository.value?.id !== repoId) {
    handleView(target);
  }
};
const handleSaveAll = async () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!detailRepository.value) return;
  loading.updating = true;
  try {
    const payload: UpdateRepositoryPayload = {
      name: detailRepository.value.name,
      language: detailRepository.value.language,
      tags: cleanTags(detailRepository.value.tags),
      description: detailRepository.value.description,
      directory: (detailRepository.value as any).directory || matchDirectoryKey(detailRepository.value),
      content: detailRepository.value.content || ''
    };
    const updated = await updateRepository(detailRepository.value.id, payload);
    const sanitized = { ...updated, directory: payload.directory, tags: cleanTags(updated.tags) };
    detailRepository.value = sanitized;
    repositories.value = repositories.value.map((repo) =>
      repo.id === sanitized.id ? sanitized : repo
    );
    ElMessage.success('已保存');
    detailDirty.meta = false;
    detailDirty.code = false;
  } catch (error) {
    console.error('保存失败', error);
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    loading.updating = false;
  }
};

const handleSaveAndRecord = async () => {
  if (!detailRepository.value) return;
  openUploadDrawer(detailRepository.value);
};
const detailCodeFullscreen = ref(false);

const directoryOptions = computed(() =>
  availableDirectories.value.map((dir) => ({ key: dir.key, title: dir.title }))
);

const loadRepositories = async () => {
  loading.repositories = true;
  try {
    const data = await listRepositories();
    repositories.value = data.map((repo) => ({ ...repo, tags: cleanTags(repo.tags) }));
  } catch (error) {
    console.error('脚本加载失败', error);
    repositories.value = [];
    ElMessage.error('脚本加载失败，请稍后重试');
  } finally {
    loading.repositories = false;
    ensureRepositorySelection();
    openRepoFromQuery();
  }
};

const loadVersions = async (repositoryId: string) => {
  loading.versions = true;
  try {
    versions.value = await listVersions(repositoryId);
  } catch (error) {
    console.error('版本记录加载失败', error);
    versions.value = [];
    ElMessage.error('版本记录加载失败，请稍后重试');
  } finally {
    loading.versions = false;
  }
};

const ensureRepositorySelection = () => {
  const repos = currentRepos.value;
  if (!repos.length) {
    selectedRepository.value = null;
    versions.value = [];
    return;
  }
  if (!selectedRepository.value || !repos.some((repo) => repo.id === selectedRepository.value?.id)) {
    selectedRepository.value = repos[0];
  }
};

const handleView = async (repo: ScriptRepository) => {
  selectedRepository.value = repo;
  detailRepository.value = repo;
  versions.value = [];
  await loadVersions(repo.id);
  detailDirty.meta = false;
  detailDirty.code = false;
  router.replace({
    name: 'code-repository',
    params: { directoryKey: selectedDirectoryKey.value || '' },
    query: { ...route.query, repoId: repo.id }
  });
};

const handleEdit = (repo: ScriptRepository) => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  showCreateMode.value = false;
  handleView(repo);
};

const submitEdit = async () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!editFormRef.value || !editForm.id) return;
  const repoId = editForm.id;
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.updating = true;
    try {
      const payload: UpdateRepositoryPayload = {
        name: editForm.name,
        language: editForm.language,
        tags: cleanTags(editForm.tags),
        description: editForm.description,
        directory: editForm.directory,
        content: editForm.content
      };
      const updated = await updateRepository(repoId, payload);
      const sanitized = { ...updated, directory: payload.directory, tags: cleanTags(updated.tags) };
      repositories.value = repositories.value.map((repo) => (repo.id === sanitized.id ? sanitized : repo));
      const detail = detailRepository.value;
      if (detail && detail.id === sanitized.id) {
        detailRepository.value = sanitized;
      }
      ElMessage.success('脚本信息已更新');
      editDialogVisible.value = false;
      ensureRepositorySelection();
    } catch (error) {
      console.error('Failed to update repository.', error);
      ElMessage.error('更新脚本失败，请稍后重试');
    } finally {
      loading.updating = false;
    }
  });
};

const handleDelete = async (repo: ScriptRepository) => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除脚本「${repo.name}」？该操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    });
    await deleteRepository(repo.id);
    repositories.value = repositories.value.filter((item) => item.id !== repo.id);
    if (detailRepository.value?.id === repo.id) {
      detailRepository.value = null;
      versions.value = [];
    }
    if (selectedRepository.value?.id === repo.id) {
      selectedRepository.value = null;
    }
    ensureRepositorySelection();
    ElMessage.success('脚本已删除');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete repository.', error);
      ElMessage.error('删除脚本失败，请稍后重试');
    }
  }
};

const openCreateDialog = () => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  if (!directoryOptions.value.length) {
    ElMessage.warning('请先创建目录');
    return;
  }
  createForm.directory = resolveActiveDirectoryForForm();
  resetCreateForm();
  detailRepository.value = null;
  selectedRepository.value = null;
  versions.value = [];
  detailCodeFullscreen.value = false;
  showCreateMode.value = true;
  const query = { ...route.query };
  delete (query as any).repoId;
  router.replace({ name: 'code-repository', params: { directoryKey: selectedDirectoryKey.value || '' }, query });
};

const resetCreateForm = () => {
  createForm.name = '';
  createForm.language = '';
  createForm.tags = [];
  createForm.description = '';
  createForm.content = '';
  createForm.change_log = '';
  createForm.directory = resolveActiveDirectoryForForm();
};

const submitCreate = async () => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  if (!createFormRef.value) return;
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.creating = true;
    try {
      const repo = await createRepository({ ...createForm, tags: cleanTags(createForm.tags) });
      const sanitized = { ...repo, directory: createForm.directory, tags: cleanTags(repo.tags) };
      repositories.value = [sanitized, ...repositories.value];
      detailRepository.value = sanitized;
      selectedRepository.value = sanitized;
      showCreateMode.value = false;
      detailDirty.meta = false;
      detailDirty.code = false;
      ElMessage.success('仓库已创建');
      resetCreateForm();
      navigateToDirectory(matchDirectoryKey(sanitized));
      await loadVersions(sanitized.id);
      router.replace({
        name: 'code-repository',
        params: { directoryKey: selectedDirectoryKey.value || '' },
        query: { ...route.query, repoId: sanitized.id }
      });
    } catch (error) {
      console.error('Failed to create repository.', error);
      ElMessage.error('创建脚本失败，请稍后重试');
    } finally {
      loading.creating = false;
    }
  });
};

const openUploadDrawer = (repo: ScriptRepository) => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  resetUploadForm();
  selectedRepository.value = repo;
  uploadDrawerVisible.value = true;
};

const resetUploadForm = () => {
  uploadForm.version = '';
  uploadForm.content = '';
  uploadForm.change_log = '';
};

const submitUpload = async () => {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  if (!uploadFormRef.value || !selectedRepository.value || !detailRepository.value) return;
  await uploadFormRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.uploading = true;
    try {
      // 先保存当前代码和信息
      await handleSaveAll();
      // 自动使用当前详情代码作为版本内容
      uploadForm.content = detailRepository.value?.content || '';
      const targetRepo = selectedRepository.value;
      const version = await uploadVersion(targetRepo!.id, uploadForm);
      versions.value = [version, ...versions.value];
      ElMessage.success('版本已记录');
      uploadDrawerVisible.value = false;
      resetUploadForm();
      if (detailRepository.value?.id === targetRepo!.id) {
        await loadVersions(targetRepo!.id);
      }
    } catch (error) {
      console.error('Failed to upload version.', error);
      ElMessage.error('记录版本失败，请稍后重试');
    } finally {
      loading.uploading = false;
    }
  });
};

const handleRollback = async (version: ScriptVersion) => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!selectedRepository.value) return;
  try {
    await rollbackVersion(selectedRepository.value.id, version.id);
    ElMessage.success(`已回滚到 ${version.version}`);
  } catch (error) {
    console.error('Failed to rollback version.', error);
    ElMessage.error('回滚失败，请稍后重试');
  }
};

const exitDetailMode = () => {
  detailRepository.value = null;
  versions.value = [];
  detailCodeFullscreen.value = false;
  const { repoId, ...rest } = route.query;
  router.replace({
    name: 'code-repository',
    params: { directoryKey: selectedDirectoryKey.value || '' },
    query: rest
  });
};

const markDetailDirty = () => {
  detailDirty.meta = true;
};

const saveDetailMeta = async () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!detailRepository.value) return;
  loading.updating = true;
  try {
    const payload: UpdateRepositoryPayload = {
      name: detailRepository.value.name,
      language: detailRepository.value.language,
      tags: cleanTags(detailRepository.value.tags),
      description: detailRepository.value.description,
      directory: (detailRepository.value as any).directory || matchDirectoryKey(detailRepository.value)
    };
    const updated = await updateRepository(detailRepository.value.id, payload);
    const sanitized = { ...updated, directory: payload.directory, tags: cleanTags(updated.tags) };
    detailRepository.value = sanitized;
    repositories.value = repositories.value.map((repo) =>
      repo.id === sanitized.id ? sanitized : repo
    );
    ElMessage.success('信息已保存');
    detailDirty.meta = false;
  } catch (error) {
    console.error('保存信息失败', error);
    ElMessage.error('保存信息失败，请稍后重试');
  } finally {
    loading.updating = false;
  }
};

const saveDetailCode = async () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!detailRepository.value) return;
  loading.updating = true;
  try {
    const payload: UpdateRepositoryPayload = {
      name: detailRepository.value.name,
      language: detailRepository.value.language,
      tags: cleanTags(detailRepository.value.tags),
      description: detailRepository.value.description,
      directory: (detailRepository.value as any).directory || matchDirectoryKey(detailRepository.value),
      content: detailRepository.value.content || ''
    };
    const updated = await updateRepository(detailRepository.value.id, payload);
    const sanitized = { ...updated, directory: payload.directory, tags: cleanTags(updated.tags) };
    detailRepository.value = sanitized;
    repositories.value = repositories.value.map((repo) =>
      repo.id === sanitized.id ? sanitized : repo
    );
    ElMessage.success('代码已保存');
    detailDirty.code = false;
  } catch (error) {
    console.error('保存代码失败', error);
    ElMessage.error('保存代码失败，请稍后重试');
  } finally {
    loading.updating = false;
  }
};

const toggleDetailFullscreen = () => {
  detailCodeFullscreen.value = !detailCodeFullscreen.value;
};

const handleCreateInline = async () => {
  await submitCreate();
};

const exitCreateMode = () => {
  const hasInput =
    createForm.name ||
    createForm.language ||
    (createForm.tags && createForm.tags.length) ||
    createForm.description ||
    createForm.content;
  if (hasInput || detailDirty.meta || detailDirty.code) {
    ElMessageBox.confirm('当前新建内容尚未保存，确认返回列表？', '确认退出', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
      .then(() => {
        showCreateMode.value = false;
        resetCreateForm();
        detailDirty.meta = false;
        detailDirty.code = false;
        router.replace({
          name: 'code-repository',
          params: { directoryKey: selectedDirectoryKey.value || '' },
          query: { ...route.query, repoId: undefined }
        });
      })
      .catch(() => {});
  } else {
    showCreateMode.value = false;
    resetCreateForm();
    detailDirty.meta = false;
    detailDirty.code = false;
    router.replace({
      name: 'code-repository',
      params: { directoryKey: selectedDirectoryKey.value || '' },
      query: { ...route.query, repoId: undefined }
    });
  }
};

const formatTime = (value?: string) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '未记录');

const latestCodeSnippet = computed(() => {
  if (!detailRepository.value) return '';
  const latestVersion = versions.value[0];
  if (latestVersion?.content) return latestVersion.content;
  return detailRepository.value.content || '';
});

const highlightedCode = computed(() => {
  const code = latestCodeSnippet.value;
  if (!code) return '';
  const langKey = (detailRepository.value?.language || '').toLowerCase();
  const mapped = LANGUAGE_HIGHLIGHT_MAP[langKey];
  if (mapped && hljs.getLanguage(mapped)) {
    return hljs.highlight(code, { language: mapped }).value;
  }
  return hljs.highlightAuto(code).value;
});

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '8px 10px'
});

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  sortState.prop = prop;
  sortState.order = order;
};

const rowClassName = ({ row }: { row: ScriptRepository }) => {
  if (row.id === selectedRepository.value?.id) {
    return 'is-selected-row';
  }
  return '';
};

const directoryTitle = (repo: ScriptRepository | null | undefined) => {
  if (!repo) return '未分类';
  const key = (repo as any).directory || matchDirectoryKey(repo);
  return directoryMap.value[key]?.title || '未分类';
};

const syncDirectorySelection = () => {
  if (!availableDirectories.value.length) {
    selectedDirectoryKey.value = '';
    return;
  }
  const param = typeof route.params.directoryKey === 'string' ? route.params.directoryKey : '';
  if (param && directoryMap.value[param]) {
    selectedDirectoryKey.value = param;
    return;
  }
  const fallbackKey = availableDirectories.value[0]?.key || '';
  selectedDirectoryKey.value = fallbackKey;
  if (param !== fallbackKey) {
    router.replace({ name: 'code-repository', params: { directoryKey: fallbackKey } });
  }
};

const resolveActiveDirectoryForForm = () => {
  if (selectedDirectoryKey.value) {
    return selectedDirectoryKey.value;
  }
  return directoryOptions.value[0]?.key || '';
};

const resetDirectoryForm = () => {
  directoryForm.title = '';
  directoryForm.keywordsInput = '';
  editingDirectoryKey.value = null;
};

const openDirectoryManager = () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  resetDirectoryForm();
  directoryManagerVisible.value = true;
};

const startEditDirectory = (dir: DirectoryPreset) => {
  directoryManagerVisible.value = true;
  editingDirectoryKey.value = dir.key;
  directoryForm.title = dir.title || '';
  directoryForm.keywordsInput = (dir.keywords || []).join(', ');
};

const submitDirectorySave = async () => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!directoryFormRef.value) return;
  await directoryFormRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.directoryManaging = true;
    const payload = {
      title: directoryForm.title,
      keywords: parseKeywords(directoryForm.keywordsInput)
    };
    try {
      if (editingDirectoryKey.value) {
        await updateCodeDirectory(editingDirectoryKey.value, payload);
        ElMessage.success('目录已更新');
      } else {
        await createCodeDirectory(payload);
        ElMessage.success('目录已创建');
      }
      await codeDirectoryStore.fetchDirectories();
      directoryManagerVisible.value = false;
      resetDirectoryForm();
      syncDirectorySelection();
    } catch (error) {
      console.error('目录保存失败', error);
      ElMessage.error('目录保存失败，请稍后重试');
    } finally {
      loading.directoryManaging = false;
    }
  });
};

const handleDeleteDirectory = async (dir: DirectoryPreset) => {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (dir.builtin) {
    ElMessage.warning('内置目录不可删除');
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除目录「${dir.title}」？该操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    });
    loading.directoryManaging = true;
    await deleteCodeDirectory(dir.key);
    await codeDirectoryStore.fetchDirectories();
    syncDirectorySelection();
    ElMessage.success('目录已删除');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除目录失败', error);
      ElMessage.error('删除目录失败，请稍后重试');
    }
  } finally {
    loading.directoryManaging = false;
  }
};

const navigateToDirectory = (key: string) => {
  if (!key) return;
  // 退出详情态，清理当前选中
  detailRepository.value = null;
  selectedRepository.value = null;
  versions.value = [];
  detailCodeFullscreen.value = false;
  selectedDirectoryKey.value = key;
  const currentParam = typeof route.params.directoryKey === 'string' ? route.params.directoryKey : '';
  const query = { ...route.query };
  delete (query as any).repoId;
  if (currentParam !== key) {
    router.push({ name: 'code-repository', params: { directoryKey: key }, query });
  } else if (selectedDirectoryKey.value !== key) {
    selectedDirectoryKey.value = key;
    router.replace({ name: 'code-repository', params: { directoryKey: key }, query });
  } else {
    router.replace({ name: 'code-repository', params: { directoryKey: key }, query });
  }
};

const handleDirectorySelect = (key: string) => {
  navigateToDirectory(key);
};

watch(
  () => repositories.value.map((repo) => repo.id).join(','),
  () => {
    ensureRepositorySelection();
    openRepoFromQuery();
  }
);

watch(
  () => filteredCurrentRepos.value.length,
  () => {
    currentPage.value = 1;
  }
);

watch(
  () => selectedDirectoryKey.value,
  () => {
    const repos = currentRepos.value;
    selectedRepository.value = repos[0] ?? null;
    if (detailRepository.value && matchDirectoryKey(detailRepository.value) !== selectedDirectoryKey.value) {
      detailRepository.value = null;
      versions.value = [];
    }
  }
);

watch(
  () => [availableDirectories.value.map((dir) => dir.key).join(','), route.params.directoryKey],
  () => {
    syncDirectorySelection();
    ensureRepositorySelection();
    openRepoFromQuery();
  },
  { immediate: true }
);

watch(
  () => repositories.value,
  (list) => {
    if (selectedRepository.value) {
      const updated = list.find((repo) => repo.id === selectedRepository.value?.id);
      if (updated) {
        selectedRepository.value = updated;
      }
    }
    if (detailRepository.value) {
      const updatedDetail = list.find((repo) => repo.id === detailRepository.value?.id);
      if (updatedDetail) {
        detailRepository.value = updatedDetail;
      }
    }
  },
  { deep: false }
);

onMounted(async () => {
  if (!directories.value.length) {
    await codeDirectoryStore.fetchDirectories();
  }
  loadRepositories();
});
</script>

<style scoped>
.btn {
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1.4rem;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.primary {
  background: linear-gradient(135deg, var(--oa-color-primary), var(--oa-color-primary-light));
  color: var(--oa-text-on-primary);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.22);
}

.btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.ghost {
  background: var(--oa-bg-muted);
  color: var(--oa-text-primary);
}

.btn.ghost:hover {
  background: var(--oa-bg-hover);
}

.btn.sm {
  padding: 0.35rem 1rem;
  font-size: 13px;
}

.code-repository {
  height: 100%;
  background: var(--oa-bg-panel);
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.code-repository--detail {
  height: auto;
  min-height: 100%;
  overflow: visible;
}

.repository-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-left: 1px solid var(--oa-border-color);
  background: var(--oa-bg-panel);
  flex: 1;
  overflow: hidden;
}

.code-repository--detail .repository-panel {
  height: auto;
  overflow: visible;
}

.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.repository-header__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
}

.header__title {
  font-weight: 600;
  color: var(--oa-text-primary);
}

.header__separator {
  color: var(--oa-text-muted);
  font-size: 13px;
}

.header__subtitle {
  color: var(--oa-text-secondary);
}

.clickable {
  cursor: pointer;
  color: var(--oa-color-primary);
}

.repository-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.refresh-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  background: var(--oa-bg-panel);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  box-shadow: var(--oa-shadow-sm);
}

.refresh-card:hover {
  border-color: var(--oa-color-primary-light);
  box-shadow: 0 10px 18px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.toolbar-button {
  border-radius: 6px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

.toolbar-button--primary {
  box-shadow: none;
}

.repository-body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.code-repository--detail .repository-body {
  overflow: visible;
}

.repository-aside {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-surface);
  border-right: 1px solid var(--oa-border-light);
  transition: width 0.2s ease;
  min-height: 0;
  position: sticky;
  top: 0;
  height: calc(100vh - 64px);
  max-height: calc(100vh - 64px);
}

.layout__aside-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 0;
}

.sidebar-placeholder {
  padding: 16px;
  text-align: center;
  color: var(--oa-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  justify-content: center;
}

.repository-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--oa-bg-panel);
  padding: 0 16px 0;
  overflow: hidden;
}

.code-repository--detail .repository-main {
  overflow: visible;
}

.repository-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: var(--oa-bg-panel);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 320px;
}

.narrow-select {
  width: 180px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px var(--oa-border-color);
}

.directory-manager__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.repository-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-panel);
  overflow: hidden;
  padding: 0 16px 12px;
}

.repository-table__card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
  min-height: 0;
}

.repository-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.repository-table__card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.repository-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.repository-name {
  color: var(--oa-color-primary);
  cursor: pointer;
}

.repository-name:hover {
  text-decoration: underline;
}

.repository-table__footer {
  padding: 0px 16px 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  color: var(--oa-text-secondary);
  border-top: none;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-right {
  margin-left: auto;
}

.repository-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.repository-pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.repository-pagination__sizes :deep(.el-input__wrapper) {
  padding: 0 10px;
}

.text-btn {
  border: none;
  background: transparent;
  color: var(--oa-color-primary);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}

.text-btn:hover {
  text-decoration: underline;
}

.table-empty {
  padding: 2rem;
  color: var(--oa-text-muted);
  font-size: 14px;
}

.muted {
  color: var(--oa-text-muted);
  font-size: 13px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.detail-header h3 {
  margin: 0;
  font-size: 20px;
  color: var(--oa-text-primary);
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0.25rem 0 0.5rem;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  color: var(--oa-text-muted);
  margin-top: 0.5rem;
  font-size: 13px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.repository-detail-page {
  margin: 16px 24px 32px;
  padding: 0;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1.6fr 0.8fr;
  gap: 20px;
  align-items: stretch;
}

.detail-left {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-color);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-left__header {
  justify-content: space-between;
  align-items: center;
}

.detail-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-card {
  background: var(--oa-bg-panel);
  border: 1px solid var(--oa-border-color);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.detail-card.danger {
  border-color: rgba(220, 38, 38, 0.25);
  background: rgba(220, 38, 38, 0.06);
}

.detail-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-form :deep(.el-input__wrapper),
.detail-form :deep(.el-textarea__inner),
.detail-form :deep(.el-select__wrapper) {
  width: 100%;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.detail-left.fullscreen {
  position: fixed;
  inset: 64px 24px 24px 24px;
  z-index: 3000;
  height: auto;
  max-height: none;
  overflow: auto;
}

.detail-left.fullscreen .detail-code-editor {
  min-height: calc(100vh - 200px);
}

.detail-code-wrapper {
  flex: 1;
  height: calc(100vh - 220px);
  min-height: calc(100vh - 220px);
}

.detail-code-wrapper :deep(.code-editor),
.detail-code-wrapper :deep(.monaco-editor),
.detail-code-wrapper :deep(.cm-editor),
.detail-code-wrapper :deep(.CodeMirror) {
  height: 100% !important;
}

.code-display {
  background: #1e1e1e;
  color: #f0f0f0;
  padding: 1rem;
  border-radius: 10px;
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 320px;
  overflow: auto;
}

:deep(.code-textarea .el-textarea__inner),
.code-textarea :deep(.el-textarea__inner) {
  font-family: 'Fira Code', 'SFMono-Regular', Consolas, monospace;
}

:deep(.is-selected-row) {
  background: rgba(14, 165, 233, 0.08) !important;
}

@media (max-width: 1200px) {
  .repository-filters {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input,
  .narrow-select {
    width: 100%;
  }
}

.dialog-shell :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.15);
}

.dialog-shell :deep(.el-dialog__body) {
  background: var(--oa-bg-muted);
  padding: 1.2rem 1.5rem;
}

.dialog-shell :deep(.el-dialog__header) {
  padding: 1.2rem 1.5rem 0.5rem;
  border-bottom: 1px solid var(--oa-border-light);
  margin-right: 0;
}

.dialog-shell :deep(.el-dialog__footer) {
  border-top: 1px solid var(--oa-border-light);
  padding: 0.75rem 1.5rem;
}

.drawer-shell :deep(.el-drawer__container) {
  padding: 1.5rem;
}

.drawer-shell :deep(.el-drawer) {
  border-radius: 24px 0 0 24px;
  box-shadow: -10px 0 40px rgba(15, 23, 42, 0.12);
}

.drawer-shell :deep(.el-drawer__body) {
  background: var(--oa-bg-panel);
  padding: 1.25rem;
}

</style>
