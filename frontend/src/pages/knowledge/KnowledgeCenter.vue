<template>
	  <div :class="['knowledge-shell', { 'knowledge-shell--detail': detailMode }]">
	    <section class="repository-panel">
	      <div class="repository-body">
	        <aside class="repository-aside" :style="{ width: sidebarWidth }">
	          <div class="layout__aside-scroll">
	            <el-menu
	              v-if="directories.length"
	              class="layout__menu layout__menu--local"
	              :default-active="selectedDirectory"
	              :collapse="sidebarCollapsed"
	              :collapse-transition="false"
	              @select="handleDirectorySelect"
	            >
	              <el-tooltip
	                v-for="dir in directories"
	                :key="dir.key"
	                class="nav-entry__tooltip"
	                effect="dark"
	                placement="right"
	                :content="dir.title"
	                :disabled="!sidebarCollapsed"
	                popper-class="layout__nav-tooltip-popper"
	              >
	                <el-menu-item :index="dir.key" class="nav-entry">
	                  <div v-if="sidebarCollapsed" class="nav-entry__badge">{{ badgeFromTitle(dir.title) }}</div>
	                  <div v-else class="nav-entry__icon">
	                    <component :is="Folder" />
	                  </div>
	                  <span class="nav-entry__label">{{ dir.title }}</span>
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

			        <div class="repository-main">
		          <div v-if="detailMode" class="repository-main__detail">
		            <div class="repository-header">
		              <div class="repository-header__info">
		                <span class="header__title">知识库</span>
		                <span class="header__separator">/</span>
		                <span class="header__subtitle">{{ currentDirectoryTitle }}</span>
		                <span class="header__separator">/</span>
		                <span class="header__subtitle">{{ activeArticle?.title || '文章详情' }}</span>
		              </div>
			              <div class="repository-header__actions">
			                <el-button class="toolbar-button" @click="exitDetailMode">返回列表</el-button>
			                <el-button
			                  class="toolbar-button"
			                  :disabled="!activeArticle"
			                  @click="activeArticle && goToView(activeArticle)"
			                >
			                  新窗口阅读
			                </el-button>
			                <el-button
			                  class="toolbar-button"
			                  :disabled="!activeArticle"
			                  @click="openVersionsDialog"
			                >
			                  版本记录
			                </el-button>
			                <el-button
			                  class="toolbar-button toolbar-button--primary"
			                  type="primary"
			                  :disabled="!activeArticle || !canCreateArticle"
			                  @click="activeArticle && goToEdit(activeArticle)"
		                >
		                  上传新版本
		                </el-button>
		              </div>
		            </div>

			            <div
			              v-if="activeArticle"
			              class="knowledge-detail-page"
			              v-loading="loadingArticle"
			              element-loading-background="rgba(255,255,255,0.4)"
			            >
			              <div class="article-head glass-card">
			                <div class="article-head__title">{{ activeArticle.title }}</div>
			                <el-descriptions :column="4" size="small" class="article-head__meta">
			                  <el-descriptions-item label="目录">
			                    {{ categoryLabel(activeArticle.category, activeArticle.category_label) }}
			                  </el-descriptions-item>
			                  <el-descriptions-item label="访问范围">
			                    {{ scopeLabel(activeArticle.visibility_scope) }}
			                  </el-descriptions-item>
			                  <el-descriptions-item label="更新人">
			                    {{ activeArticle.last_editor || '系统' }}
			                  </el-descriptions-item>
			                  <el-descriptions-item label="最近更新">
			                    {{ formatTime(activeArticle.last_edited_at) }}
			                  </el-descriptions-item>
			                </el-descriptions>
			                <div class="detail-tags" v-if="activeArticle.tags?.length">
			                  <div class="detail-tags__label">标签</div>
			                  <el-space wrap size="6">
			                    <el-tag v-for="tag in activeArticle.tags" :key="tag" size="small" round>
			                      {{ tag }}
			                    </el-tag>
			                  </el-space>
			                </div>
			              </div>

			              <div class="detail-layout">
			                <div class="detail-left glass-card">
			                  <article class="article-body" v-html="activeArticle.content" />
			                </div>
			              </div>
			            </div>

		            <div v-else class="empty-view glass-card">
		              <p>正在加载文章...</p>
		            </div>
		          </div>

		          <div v-else class="repository-main__list">
		            <div class="repository-header">
		              <div class="repository-header__info">
	                <span class="header__title">知识库</span>
	                <span class="header__separator">/</span>
	                <span class="header__subtitle">{{ currentDirectoryTitle }}</span>
	              </div>
	              <div class="repository-header__actions">
	                <el-button
	                  v-if="canManageArticle"
	                  class="toolbar-button toolbar-button--primary"
	                  type="primary"
	                  @click="openDirectoryManager"
	                >
	                  管理目录
	                </el-button>
	                <div class="refresh-card" @click="refresh">
	                  <el-icon class="refresh-icon" :class="{ spinning: loading.articles }"><Refresh /></el-icon>
	                  <span>刷新</span>
	                </div>
	              </div>
	            </div>

	            <div class="repository-filters">
	              <div class="filters-left">
	                <el-button
	                  class="toolbar-button toolbar-button--primary"
	                  type="primary"
	                  :disabled="!canCreateArticle"
	                  @click="goToCreate"
	                >
	                  上传文章
	                </el-button>
	              </div>
	              <div class="filters-right">
	                <el-select v-model="visibilityFilter" class="pill-input narrow-select">
	                  <el-option label="全部访问范围" value="all" />
	                  <el-option label="公开" value="public" />
	                  <el-option label="内部" value="internal" />
	                  <el-option label="受限" value="restricted" />
	                </el-select>
	                <el-select
	                  v-model="tagFilter"
	                  multiple
	                  collapse-tags
	                  clearable
	                  placeholder="筛选标签"
	                  class="pill-input tag-select"
	                  :max-collapse-tags="2"
	                >
	                  <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
	                </el-select>
	                <el-input
	                  v-model="searchKeyword"
	                  placeholder="搜索标题 / 标签 / 内容"
	                  clearable
	                  class="search-input pill-input search-input--compact"
	                >
	                  <template #prefix>
	                    <el-icon><Search /></el-icon>
	                  </template>
	                </el-input>
	              </div>
	            </div>

		            <div class="repository-table">
		              <div class="repository-table__card">
		                <el-table
		                  height="100%"
		                  :data="pagedArticles"
		                  v-loading="loading.articles"
		                  stripe
		                  empty-text="暂无文章"
		                  :header-cell-style="tableHeaderStyle"
		                  :cell-style="tableCellStyle"
		                  @row-click="openDetail"
		                >
	                  <template #empty>
	                    <div class="table-empty">
	                      <p>该目录暂无文章</p>
	                    </div>
	                  </template>
		            <el-table-column label="标题" min-width="220" show-overflow-tooltip>
		              <template #default="{ row }">
		                <span class="repository-name" @click.stop="openDetail(row)">{{ row.title }}</span>
		              </template>
		            </el-table-column>
		            <el-table-column label="目录" width="120" show-overflow-tooltip>
		              <template #default="{ row }">
		                {{ categoryLabel(row.category, row.category_label) }}
		              </template>
		            </el-table-column>
		            <el-table-column label="标签" min-width="120">
		              <template #default="{ row }">
		                <el-space wrap size="4">
		                  <el-tag v-for="tag in row.tags" :key="tag" size="small" round>{{ tag }}</el-tag>
		                </el-space>
		              </template>
		            </el-table-column>
		            <el-table-column label="范围" width="84">
		              <template #default="{ row }">
		                {{ scopeLabel(row.visibility_scope) }}
		              </template>
		            </el-table-column>
	            <el-table-column label="最近更新" width="160">
	              <template #default="{ row }">
	                {{ formatTime(row.last_edited_at, 'short') }}
	              </template>
	            </el-table-column>
	            <el-table-column label="更新人" width="120" show-overflow-tooltip>
	              <template #default="{ row }">
	                {{ row.last_editor || '系统' }}
	              </template>
	            </el-table-column>
		            <el-table-column label="操作" width="240">
		              <template #default="{ row }">
		                <el-space size="small">
		                  <el-button text size="small" @click.stop="openDetail(row)">查看</el-button>
		                  <el-button text size="small" :disabled="!canCreateArticle" @click.stop="goToEdit(row)">上传新版本</el-button>
	                  <el-button text type="danger" size="small" :disabled="!canManageArticle" @click.stop="handleDeleteArticle(row)">删除</el-button>
	                </el-space>
	              </template>
	            </el-table-column>
	                </el-table>
	              </div>
	            </div>
	
	            <div class="repository-table__footer">
	              <div class="footer-left">
	                <div class="repository-stats">共 {{ filteredArticles.length }} 篇</div>
	                <el-pagination
	                  class="repository-pagination__sizes"
	                  :disabled="loading.articles"
	                  v-model:current-page="currentPage"
	                  v-model:page-size="pageSize"
	                  :total="filteredArticles.length"
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
	                  :disabled="loading.articles"
	                  v-model:current-page="currentPage"
	                  :page-size="pageSize"
	                  :total="filteredArticles.length"
	                  layout="prev, pager, next"
	                  background
	                  @current-change="handlePageChange"
	                />
	              </div>
	            </div>
	          </div>
	        </div>
	      </div>
	    </section>

    <el-dialog
      v-model="uploadDialogVisible"
      :title="uploadDialogTitle"
      width="600px"
      class="dialog-shell"
    >
      <el-form label-width="100px">
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="请输入文章标题" />
        </el-form-item>
        <el-form-item label="所属目录" required>
          <el-select v-model="uploadForm.category" placeholder="选择目录" filterable>
            <el-option
              v-for="dir in directoryOptions"
              :key="dir.value"
              :label="dir.label"
              :value="dir.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标签" required>
          <el-select
            v-model="uploadForm.tags"
            multiple
            allow-create
            filterable
            collapse-tags
            placeholder="可输入并回车新增标签"
          >
            <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="访问范围" required>
          <el-radio-group v-model="uploadForm.visibility_scope">
            <el-radio label="public">公开</el-radio>
            <el-radio label="internal">内部</el-radio>
            <el-radio label="restricted">受限</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="文档文件" required>
          <input
            ref="fileInputRef"
            type="file"
            class="file-input"
            @change="handleFileChange"
            accept=".md,.markdown,.txt,.html,.htm,.docx"
          />
          <p class="muted">支持 docx / md / txt / html，上传后自动转换为在线内容。</p>
          <p v-if="uploadErrors.file" class="error-text">{{ uploadErrors.file }}</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading.uploading" @click="submitUpload">
          {{ uploadMode === 'create' ? '上传' : '上传新版本' }}
        </el-button>
      </template>
	    </el-dialog>

	    <el-dialog
	      v-model="versionsDialogVisible"
	      title="版本记录"
	      width="860px"
	      class="dialog-shell"
	      destroy-on-close
	    >
	      <el-table
	        :data="pagedArticleVersions"
	        v-loading="versionsLoading"
	        size="small"
	        empty-text="暂无版本记录"
	      >
	        <el-table-column prop="version" label="版本" width="90" />
	        <el-table-column label="时间" width="180">
	          <template #default="{ row }">
	            {{ formatTime(row.created_at) }}
	          </template>
	        </el-table-column>
	        <el-table-column prop="editor" label="更新人" width="140" />
	        <el-table-column prop="summary" label="摘要" min-width="220" show-overflow-tooltip />
	      </el-table>
	      <template #footer>
	        <div class="dialog-pagination">
	          <el-pagination
	            v-model:current-page="versionsPage"
	            v-model:page-size="versionsPageSize"
	            :total="articleVersions.length"
	            :page-sizes="versionsPageSizeOptions"
	            layout="total, sizes, prev, pager, next"
	            background
	          />
	        </div>
	      </template>
	    </el-dialog>
	
		    <el-dialog
		      v-model="directoryDialogVisible"
		      title="管理目录"
	      width="720px"
	      class="dialog-shell"
	      destroy-on-close
	    >
	      <el-form :model="categoryForm" label-width="100px" class="category-editor">
	        <el-form-item label="目录名称" required>
	          <el-input v-model="categoryForm.title" placeholder="例如：最佳实践" />
	        </el-form-item>
	        <el-form-item label="唯一标识">
	          <el-input v-model="categoryForm.key" placeholder="留空自动生成" :disabled="!!categoryForm.editingKey" />
	        </el-form-item>
	        <el-form-item label="描述">
	          <el-input v-model="categoryForm.description" type="textarea" :rows="2" placeholder="简要描述该目录" />
	        </el-form-item>
	        <el-form-item>
	          <div class="directory-manager__actions">
	            <div class="left-actions">
	              <el-button @click="resetCategoryForm">重置</el-button>
	            </div>
	            <div class="right-actions">
	              <el-button @click="directoryDialogVisible = false">取消</el-button>
	              <el-button
	                type="primary"
	                :loading="loading.categorySaving"
	                :disabled="!canManageArticle"
	                @click="submitCategory"
	              >
	                {{ categoryForm.editingKey ? '保存修改' : '新增目录' }}
	              </el-button>
	            </div>
	          </div>
	        </el-form-item>
	      </el-form>
	
	      <el-table
	        :data="categories"
	        size="small"
	        class="directory-table"
	        style="margin-top: 12px"
	        v-loading="loading.categories"
	      >
	        <el-table-column prop="title" label="目录名称" min-width="240" />
	        <el-table-column prop="article_count" label="文章数" width="110" align="center" />
	        <el-table-column label="操作" width="180" align="center">
	          <template #default="{ row }">
	            <el-space size="small">
	              <el-button
	                text
	                size="small"
	                :disabled="row.builtin || !canManageArticle"
	                @click="handleEditCategory(row)"
	              >编辑</el-button>
	              <el-button
	                text
	                type="danger"
	                size="small"
	                :disabled="row.builtin || !canManageArticle"
	                @click="handleDeleteCategory(row)"
	              >删除</el-button>
	            </el-space>
	          </template>
	        </el-table-column>
	      </el-table>
	    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Expand, Fold, Refresh, Folder } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';

	import {
	  deleteArticle,
	  searchArticles,
	  listCategories,
	  createCategory,
	  updateCategory,
	  deleteCategory,
	  createArticleFromUpload,
	  updateArticleFromUpload,
  getArticle,
  listArticleVersions,
  type KnowledgeArticle,
  type KnowledgeArticleVersion,
  type KnowledgeCategory,
  type KnowledgeCategoryPayload
} from '@/services/knowledgeApi';
import { usePageTitle } from '@/composables/usePageTitle';
import { useSessionStore } from '@/stores/session';
import { useAppStore } from '@/stores/app';

const router = useRouter();
const route = useRoute();
const { t } = useI18n();
usePageTitle('knowledge.title');

const sessionStore = useSessionStore();
const appStore = useAppStore();
const canCreateArticle = computed(() => sessionStore.hasPermission('knowledge.articles.create'));
const canManageArticle = computed(() => sessionStore.hasPermission('knowledge.articles.manage'));

const requireCreatePermission = () => {
  if (!canCreateArticle.value) {
    ElMessage.warning('暂无新增权限');
    return false;
  }
  return true;
};

const requireManagePermission = () => {
  if (!canManageArticle.value) {
    ElMessage.warning('暂无管理权限');
    return false;
  }
  return true;
};

const articles = ref<KnowledgeArticle[]>([]);
const categories = ref<KnowledgeCategory[]>([]);
const articleVersions = ref<KnowledgeArticleVersion[]>([]);
const activeArticle = ref<KnowledgeArticle | null>(null);
const activeArticleSlug = ref<string | null>(null);
const loadingArticle = ref(false);

const detailMode = computed(() => !!activeArticleSlug.value);
const ARTICLE_QUERY_KEY = 'article';

const setRouteArticle = (slug: string | null, mode: 'push' | 'replace' = 'push') => {
  const nextQuery = { ...route.query } as Record<string, any>;
  if (slug) {
    nextQuery[ARTICLE_QUERY_KEY] = slug;
  } else {
    delete nextQuery[ARTICLE_QUERY_KEY];
  }
  const navTarget = { path: route.path, query: nextQuery };
  return mode === 'replace' ? router.replace(navTarget) : router.push(navTarget);
};

const loading = reactive({
  articles: false,
  categories: false,
  categorySaving: false,
  uploading: false
});

const searchKeyword = ref('');
const visibilityFilter = ref<'all' | 'public' | 'internal' | 'restricted'>('all');
const tagFilter = ref<string[]>([]);
const selectedDirectory = ref<'all' | string>('all');

const currentPage = ref(1);
const pageSizeOptions = [10, 20, 50];
const pageSize = ref<number>(20);

const sidebarCollapsed = ref(false);
const sidebarWidth = computed(() => (sidebarCollapsed.value ? '72px' : '240px'));

	const directoryDialogVisible = ref(false);
	const uploadDialogVisible = ref(false);
	const versionsDialogVisible = ref(false);
	const versionsLoading = ref(false);
	const versionsPage = ref(1);
	const versionsPageSizeOptions = [10, 20, 50];
	const versionsPageSize = ref(10);
	const uploadMode = ref<'create' | 'update'>('create');
	const uploadTarget = ref<KnowledgeArticle | null>(null);
const uploadForm = reactive({
  title: '',
  category: '',
  tags: [] as string[],
  visibility_scope: 'internal' as 'public' | 'internal' | 'restricted',
  file: null as File | null
});
const uploadErrors = reactive({
  file: ''
});

const badgeFromTitle = (title: string) => {
  if (!title) return '·';
  const words = title.split(/\s+/).filter(Boolean);
  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }
  return words
    .map((word) => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
};
const fileInputRef = ref<HTMLInputElement | null>(null);

const categoryForm = reactive<KnowledgeCategoryPayload & { description?: string; editingKey: string | null }>({
  key: '',
  title: '',
  description: '',
  editingKey: null
});

const fallbackArticles: KnowledgeArticle[] = [
  {
    id: 'kb-1',
    title: '数据库连接告警处理指引',
    slug: 'kb-1',
    category: 'best-practice',
    category_label: '故障处理',
    tags: ['数据库', '告警', '排障'],
    visibility_scope: 'internal',
    last_editor: 'Zhang Wei',
    last_edited_at: new Date().toISOString(),
    attachments: [],
    content:
      '<p>当数据库连接出现告警时，请按以下步骤执行：</p><ol><li>确认报警来源与影响范围</li><li>检查连接池与慢查询日志</li><li>如需扩大排查，可执行工具库中的《配置基线对比》</li></ol>'
  },
  {
    id: 'kb-2',
    title: 'Nginx 日志分析脚本说明',
    slug: 'kb-2',
    category: 'best-practice',
    category_label: '最佳实践',
    tags: ['日志', '脚本', 'web'],
    visibility_scope: 'public',
    last_editor: 'Li Na',
    last_edited_at: new Date().toISOString(),
    attachments: [],
    content:
      '<p>该脚本用于分析 Nginx 日志中的异常请求，建议在访问量突增或出现 5xx 时使用。脚本默认保存最近 30 分钟内的统计结果。</p>'
  }
];

const categoryMap = computed<Record<string, KnowledgeCategory>>(() => {
  const map: Record<string, KnowledgeCategory> = {};
  categories.value.forEach((cat) => {
    map[cat.key] = cat;
  });
  return map;
});

const directories = computed(() => {
  if (!categories.value.length) {
    const map = new Map<string, { key: string; title: string; count: number }>();
    articles.value.forEach((article) => {
      const key = article.category || 'uncategorized';
      const title = article.category_label || key || '未分类';
      const entry = map.get(key);
      if (entry) {
        entry.count += 1;
      } else {
        map.set(key, { key, title, count: 1 });
      }
    });
    const list = Array.from(map.values()).sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'));
    return [{ key: 'all', title: '全部', count: articles.value.length }, ...list];
  }

  const counts = articles.value.reduce<Record<string, number>>((acc, article) => {
    const key = article.category || 'uncategorized';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const list = categories.value.map((cat) => ({
    key: cat.key,
    title: cat.title,
    count: counts[cat.key] || 0
  }));

  if (counts.uncategorized && !categories.value.some((cat) => cat.key === 'uncategorized')) {
    list.push({
      key: 'uncategorized',
      title: '未分类',
      count: counts.uncategorized
    });
  }

  return [{ key: 'all', title: '全部', count: articles.value.length }, ...list];
});

const directoryOptions = computed(() =>
  directories.value
    .filter((dir) => dir.key !== 'all')
    .map((dir) => ({
      label: dir.title,
      value: dir.key
    }))
);

const availableTags = computed(() => {
  const tagSet = new Set<string>();
  articles.value.forEach((article) => {
    article.tags?.forEach((tag) => tagSet.add(tag));
  });
  return Array.from(tagSet.values());
});

const uploadDialogTitle = computed(() =>
  uploadMode.value === 'create' ? '上传知识文章' : '上传新版本'
);

const baseFilteredArticles = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  return articles.value.filter((article) => {
    const matchVisibility =
      visibilityFilter.value === 'all' || article.visibility_scope === visibilityFilter.value;
    const matchTags =
      tagFilter.value.length === 0 || tagFilter.value.every((tag) => article.tags.includes(tag));
    const matchKeyword =
      !keyword ||
      article.title.toLowerCase().includes(keyword) ||
      article.tags.some((tag) => tag.toLowerCase().includes(keyword)) ||
      (article.content || '').toLowerCase().includes(keyword);
    return matchVisibility && matchTags && matchKeyword;
  });
});

const filteredArticles = computed(() => {
  if (selectedDirectory.value === 'all') {
    return baseFilteredArticles.value;
  }
  return baseFilteredArticles.value.filter(
    (article) => (article.category || 'uncategorized') === selectedDirectory.value
  );
});

const pagedArticles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredArticles.value.slice(start, start + pageSize.value);
});

const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
};

const handleDirectorySelect = (key: string) => {
  if (detailMode.value) {
    exitDetailMode();
  }
  selectDirectory(key as 'all' | string);
};

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '6px 8px'
});

type DownloadFormat = 'word' | 'markdown';

const sanitizeFileName = (title: string) => title.replace(/[\\/:*?"<>|]/g, '_');

const htmlToMarkdown = (html: string) => {
  const temp = document.createElement('div');
  temp.innerHTML = html;

  const walk = (node: Node, depth = 0): string => {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent?.replace(/\s+/g, ' ').trim() || '';
    }
    if (!(node instanceof HTMLElement)) return '';
    const tag = node.tagName.toUpperCase();
    const content = Array.from(node.childNodes)
      .map((child) => walk(child, depth))
      .filter(Boolean)
      .join(' ')
      .trim();
    if (!content) return '';
    switch (tag) {
      case 'H1':
        return `# ${content}\n\n`;
      case 'H2':
        return `## ${content}\n\n`;
      case 'H3':
        return `### ${content}\n\n`;
      case 'H4':
        return `#### ${content}\n\n`;
      case 'H5':
        return `##### ${content}\n\n`;
      case 'H6':
        return `###### ${content}\n\n`;
      case 'P':
      case 'DIV':
      case 'SECTION':
        return `${content}\n\n`;
      case 'BR':
        return '\n';
      case 'UL':
        return (
          Array.from(node.children)
            .map((li) => `- ${walk(li, depth + 1).trim()}\n`)
            .join('') + '\n'
        );
      case 'OL':
        return (
          Array.from(node.children)
            .map((li, index) => `${index + 1}. ${walk(li, depth + 1).trim()}\n`)
            .join('') + '\n'
        );
      case 'LI':
        return `${content}\n`;
      case 'PRE':
        return `\`\`\`\n${node.textContent || content}\n\`\`\`\n\n`;
      case 'CODE':
        return `\`${content}\``;
      case 'STRONG':
      case 'B':
        return `**${content}**`;
      case 'EM':
      case 'I':
        return `*${content}*`;
      case 'A':
        return `[${content}](${node.getAttribute('href') || '#'})`;
      default:
        return `${content} `;
    }
  };

  return walk(temp).replace(/\n{3,}/g, '\n\n').trim();
};

const downloadArticleContent = async (article: KnowledgeArticle, format: DownloadFormat = 'word') => {
  try {
    let detail = article;
    if (!detail.content) {
      const slug = article.slug || article.id;
      if (!slug) {
        ElMessage.warning('文章缺少标识，无法下载');
        return;
      }
      detail = await getArticle(slug);
    }
    if (!detail.content) {
      ElMessage.warning('文章内容为空，无法下载');
      return;
    }
    let blob: Blob;
    let extension: string;
    if (format === 'word') {
      const doc = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><title>${detail.title}</title></head><body>${detail.content}</body></html>`;
      blob = new Blob([doc], { type: 'application/msword' });
      extension = 'doc';
    } else {
      const markdown = htmlToMarkdown(detail.content);
      blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
      extension = 'md';
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${sanitizeFileName(detail.title || 'article')}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    ElMessage.success('文章下载开始');
  } catch (error) {
    console.error('下载文章失败', error);
    ElMessage.error('下载失败，请稍后再试');
  }
};

const selectDirectory = (key: 'all' | string) => {
  selectedDirectory.value = key;
  ensureActiveArticle();
};

const categoryLabel = (key?: string, fallback?: string) => {
  if (!key) return fallback || '未分类';
  const match = categoryMap.value[key];
  return match?.title || fallback || key;
};

const currentDirectoryTitle = computed(() => {
  if (selectedDirectory.value === 'all') return '全部';
  return categoryLabel(selectedDirectory.value);
});

const scopeLabel = (value: KnowledgeArticle['visibility_scope']) => {
  switch (value) {
    case 'public':
      return '公开';
    case 'restricted':
      return '受限';
    default:
      return '内部';
  }
};

const formatTime = (value?: string, mode: 'full' | 'short' = 'full') => {
  if (!value) return '未记录';
  return mode === 'short' ? dayjs(value).format('MM-DD HH:mm') : dayjs(value).format('YYYY-MM-DD HH:mm');
};

const goToView = (article: KnowledgeArticle) => {
  const target = article.slug || article.id;
  if (!target) {
    ElMessage.warning('文章缺少标识，无法查看');
    return;
  }
  const routeRef = router.resolve({ path: `/knowledge/view/${target}` });
  window.open(routeRef.href, '_blank');
};

const openUploadDialog = (mode: 'create' | 'update', article?: KnowledgeArticle) => {
  if (!requireCreatePermission()) return;
  uploadMode.value = mode;
  uploadTarget.value = article || null;
  uploadForm.title = article?.title || '';
  uploadForm.category =
    article?.category ||
    (selectedDirectory.value !== 'all' ? selectedDirectory.value : directoryOptions.value[0]?.value || '');
  uploadForm.tags = article ? [...article.tags] : [];
  uploadForm.visibility_scope = article?.visibility_scope || 'internal';
  uploadForm.file = null;
  uploadErrors.file = '';
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
  uploadDialogVisible.value = true;
};

const goToCreate = () => openUploadDialog('create');
	const goToEdit = (article: KnowledgeArticle) => openUploadDialog('update', article);
	const openDirectoryManager = () => {
	  if (!requireManagePermission()) return;
	  directoryDialogVisible.value = true;
	};

	const pagedArticleVersions = computed(() => {
	  const start = (versionsPage.value - 1) * versionsPageSize.value;
	  return articleVersions.value.slice(start, start + versionsPageSize.value);
	});

		const openVersionsDialog = async () => {
		  versionsDialogVisible.value = true;
		  versionsPage.value = 1;
		  if (!activeArticleSlug.value) return;
		  versionsLoading.value = true;
		  try {
		    articleVersions.value = await listArticleVersions(activeArticleSlug.value);
		  } catch (error) {
		    console.warn('版本记录加载失败', error);
	    articleVersions.value = [];
	  } finally {
	    versionsLoading.value = false;
	  }
	};

	const loadArticleDetail = async (slug: string) => {
	  loadingArticle.value = true;
	  try {
	    activeArticle.value = await getArticle(slug);
	    articleVersions.value = [];
	  } catch (error) {
	    console.error('加载文章失败', error);
	    const fallback = articles.value.find((item) => (item.slug || item.id) === slug) || null;
	    activeArticle.value = fallback;
    articleVersions.value = [];
    if (!fallback) {
      ElMessage.error('文章已不存在');
    }
  } finally {
    loadingArticle.value = false;
  }
};

	const openDetail = (article: KnowledgeArticle) => {
	  const slug = article.slug || article.id;
	  if (!slug) {
	    ElMessage.warning('文章缺少标识，无法打开');
	    return;
	  }
	  void setRouteArticle(slug, 'push');
	};

		const exitDetailMode = () => {
		  activeArticleSlug.value = null;
		  activeArticle.value = null;
		  articleVersions.value = [];
		  versionsDialogVisible.value = false;
		  void setRouteArticle(null, 'replace');
		};

	const ensureActiveArticle = () => {
	  if (route.query[ARTICLE_QUERY_KEY]) return;
	  const list = filteredArticles.value;
	  if (!list.length) {
	    activeArticleSlug.value = null;
	    activeArticle.value = null;
    articleVersions.value = [];
    return;
  }
  if (
    activeArticleSlug.value &&
    list.some((article) => (article.slug || article.id) === activeArticleSlug.value)
  ) {
    return;
  }
  activeArticleSlug.value = null;
  activeArticle.value = null;
  articleVersions.value = [];
};

const loadArticles = async () => {
  loading.articles = true;
  try {
    articles.value = await searchArticles({
      keyword: searchKeyword.value.trim() || undefined
    });
  } catch (error) {
    console.warn('知识库文章加载失败，使用示例数据。', error);
    ElMessage.warning(t('common.loadingFallback'));
    articles.value = fallbackArticles;
  } finally {
    loading.articles = false;
    ensureActiveArticle();
  }
};

const loadCategories = async () => {
  loading.categories = true;
  try {
    categories.value = await listCategories();
  } catch (error) {
    console.warn('目录加载失败，将使用文章自动分类。', error);
    categories.value = [];
  } finally {
    loading.categories = false;
    const validKeys = directories.value.map((dir) => dir.key);
    if (!validKeys.includes(selectedDirectory.value)) {
      selectedDirectory.value = 'all';
    }
  }
};

const refresh = () => {
  void Promise.all([loadArticles(), loadCategories()]);
};

const handleDeleteArticle = async (article: KnowledgeArticle) => {
  if (!requireManagePermission()) return;
  try {
    await ElMessageBox.confirm(`确定删除文章「${article.title}」？该操作不可恢复。`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    });
    if (article.slug) {
      await deleteArticle(article.slug);
    }
    articles.value = articles.value.filter((item) => item.id !== article.id);
    ElMessage.success('文章已删除');
    await loadCategories();
    ensureActiveArticle();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文章失败', error);
      ElMessage.error('删除失败，请稍后重试');
    }
  }
};

const handleFileChange = (event: Event) => {
  if (!requireCreatePermission()) return;
  const target = event.target as HTMLInputElement;
  const [file] = target.files || [];
  uploadForm.file = file || null;
  uploadErrors.file = '';
};

const resetUploadForm = () => {
  uploadForm.title = '';
  uploadForm.category =
    selectedDirectory.value !== 'all'
      ? selectedDirectory.value
      : directoryOptions.value[0]?.value || '';
  uploadForm.tags = [];
  uploadForm.visibility_scope = 'internal';
  uploadForm.file = null;
  uploadErrors.file = '';
  uploadTarget.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

const submitUpload = async () => {
  if (!requireCreatePermission()) return;
  if (!uploadForm.title.trim()) {
    ElMessage.warning('请输入标题');
    return;
  }
  if (!uploadForm.category) {
    ElMessage.warning('请选择目录');
    return;
  }
  if (!uploadForm.tags.length) {
    ElMessage.warning('请至少添加一个标签');
    return;
  }
  if (!uploadForm.file) {
    uploadErrors.file = '请上传文件';
    return;
  }
  const formData = new FormData();
  formData.append('title', uploadForm.title.trim());
  formData.append('category', uploadForm.category);
  uploadForm.tags.forEach((tag) => formData.append('tags', tag));
  formData.append('visibility_scope', uploadForm.visibility_scope);
  formData.append('source_file', uploadForm.file);

  loading.uploading = true;
	  try {
	    if (uploadMode.value === 'create') {
	      await createArticleFromUpload(formData);
	      ElMessage.success('文章已上传');
	    } else if (uploadTarget.value) {
	      const slug = uploadTarget.value.slug || uploadTarget.value.id;
	      await updateArticleFromUpload(slug, formData);
	      ElMessage.success('文章已更新');
	      // 更新成功后刷新当前详情并清理版本缓存，确保版本记录可见
	      if (activeArticleSlug.value === slug) {
	        await loadArticleDetail(slug);
	      } else {
	        articleVersions.value = [];
	      }
	      versionsDialogVisible.value = false;
	    }
	    uploadDialogVisible.value = false;
	    resetUploadForm();
	    await Promise.all([loadArticles(), loadCategories()]);
	  } catch (error) {
    console.error('上传失败', error);
    ElMessage.error('上传失败，请稍后重试');
  } finally {
    loading.uploading = false;
  }
};

const resetCategoryForm = () => {
  categoryForm.key = '';
  categoryForm.title = '';
  categoryForm.description = '';
  categoryForm.editingKey = null;
};

const submitCategory = async () => {
  if (!requireManagePermission()) return;
  if (!categoryForm.title.trim()) {
    ElMessage.warning('请输入目录名称');
    return;
  }
  loading.categorySaving = true;
  try {
    if (categoryForm.editingKey) {
      await updateCategory(categoryForm.editingKey, {
        title: categoryForm.title,
        description: categoryForm.description
      });
    } else {
      await createCategory({
        key: categoryForm.key?.trim() || undefined,
        title: categoryForm.title,
        description: categoryForm.description
      });
    }
    await loadCategories();
    resetCategoryForm();
    ElMessage.success('目录已保存');
  } catch (error) {
    console.error('目录保存失败', error);
    ElMessage.error('目录保存失败，请稍后重试');
  } finally {
    loading.categorySaving = false;
  }
};

const handleEditCategory = (category: KnowledgeCategory) => {
  if (!requireManagePermission()) return;
  categoryForm.editingKey = category.key;
  categoryForm.key = category.key;
  categoryForm.title = category.title;
  categoryForm.description = category.description || '';
};

const handleDeleteCategory = async (category: KnowledgeCategory) => {
  if (!requireManagePermission()) return;
  if (category.builtin) {
    ElMessage.warning('内置目录不可删除');
    return;
  }
  try {
    await ElMessageBox.confirm(`确定删除目录「${category.title}」？关联文章将移动到默认目录。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    });
    await deleteCategory(category.key);
    await loadCategories();
    ElMessage.success('目录已删除');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除目录失败', error);
      ElMessage.error('删除失败，请稍后再试');
    }
  }
};

		const handleRouteIntent = async () => {
		  const intent = route.query.upload as string | undefined;
		  const slug = route.query.slug as string | undefined;
		  if (!intent) return;
  if (intent === 'create') {
    openUploadDialog('create');
  } else if (intent === 'update' && slug) {
    try {
      const target = await getArticle(slug);
      openUploadDialog('update', target);
    } catch (error) {
      console.warn('跳转加载文章失败', error);
      ElMessage.error('文章已不存在');
    }
  }
  const nextQuery = { ...route.query } as Record<string, any>;
  delete nextQuery.upload;
  delete nextQuery.slug;
	  router.replace({ path: route.path, query: nextQuery });
	};

	const handleRouteArticle = async () => {
	  const slug = route.query[ARTICLE_QUERY_KEY] as string | undefined;
	  if (!slug) {
	    if (activeArticleSlug.value) {
	      activeArticleSlug.value = null;
	      activeArticle.value = null;
	      articleVersions.value = [];
	      versionsDialogVisible.value = false;
	    }
	    return;
	  }

	  if (activeArticleSlug.value === slug && activeArticle.value) return;
	  activeArticleSlug.value = slug;

	  const fromList = articles.value.find((item) => (item.slug || item.id) === slug);
	  if (fromList) {
	    selectedDirectory.value = fromList.category || 'uncategorized';
	  }

	  await loadArticleDetail(slug);
	  if (!activeArticle.value) {
	    activeArticleSlug.value = null;
	    articleVersions.value = [];
	    versionsDialogVisible.value = false;
	    void setRouteArticle(null, 'replace');
	    return;
	  }

	  selectedDirectory.value = activeArticle.value.category || 'uncategorized';
	};

watch(directoryDialogVisible, (visible) => {
  if (!visible) {
    resetCategoryForm();
  }
});

watch(uploadDialogVisible, (visible) => {
  if (!visible) {
    resetUploadForm();
  }
});

watch(baseFilteredArticles, () => {
  currentPage.value = 1;
  ensureActiveArticle();
});

watch(selectedDirectory, () => {
  currentPage.value = 1;
  ensureActiveArticle();
});

watch(filteredArticles, () => {
  const maxPage = Math.max(1, Math.ceil(filteredArticles.value.length / pageSize.value));
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage;
  }
});

	watch(
	  () => ({ ...route.query }),
	  () => {
	    void handleRouteIntent();
	    void handleRouteArticle();
	  },
	  { immediate: true }
	);

watch(
  () => categories.value.map((cat) => cat.key),
  (keys) => {
    if (selectedDirectory.value !== 'all' && !keys.includes(selectedDirectory.value)) {
      selectedDirectory.value = 'all';
    }
  }
);

onMounted(() => {
  loadCategories();
  loadArticles();
});

watch(
  () => detailMode.value,
  (isDetail) => {
    // 列表：不出现外层滚动条（表格 body 内滚）；详情：由主内容区滚动（左侧目录 sticky 固定）
    appStore.setMainScrollLocked(!isDetail);
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  appStore.setMainScrollLocked(false);
});
</script>

<style scoped>
.knowledge-shell {
  height: 100%;
  background: var(--oa-bg-panel);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.knowledge-shell--detail {
  height: auto;
  min-height: 100%;
  overflow: visible;
}

.glass-card {
  background: var(--oa-bg-panel);
  border-radius: 8px;
  border: 1px solid var(--oa-border-light);
  box-shadow: var(--oa-shadow-sm);
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

.knowledge-shell--detail .repository-panel {
  height: auto;
  overflow: visible;
}

.repository-body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.knowledge-shell--detail .repository-body {
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
  min-width: 0;
  background: var(--oa-bg-panel);
  padding: 0 16px 0px;
  overflow: hidden;
}

.knowledge-shell--detail .repository-main {
  overflow: visible;
}

.repository-main__list {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.repository-main__detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-detail-page {
  padding-top: 16px;
}

.article-head {
  padding: 16px;
  margin-bottom: 16px;
}

.article-head__title {
  font-size: 18px;
  font-weight: 700;
  color: var(--oa-text-primary);
  margin-bottom: 10px;
}

.article-head__meta :deep(.el-descriptions__label) {
  color: var(--oa-text-secondary);
}

.dialog-pagination {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  align-items: start;
}

.detail-left {
  padding: 16px;
}

.detail-tags {
  margin-top: 12px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.detail-tags__label {
  font-size: 12px;
  color: var(--oa-text-secondary);
  flex: 0 0 auto;
  white-space: nowrap;
}

.tree-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.tree-panel__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 12px 16px;
}

.viewer-panel {
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
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
  flex-wrap: nowrap;
  min-width: 0;
}

.search-input {
  flex: 1;
  min-width: 0;
}

.search-input--compact {
  max-width: 320px;
}

.narrow-select {
  width: 180px;
}

.tag-select {
  width: 220px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.repository-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--oa-bg-panel);
  overflow: hidden;
  padding: 0 16px 12px;
  min-width: 0;
}

.repository-table__card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: none;
  min-width: 0;
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
  padding: 6px 8px;
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

	.repository-pagination__sizes :deep(.el-input__wrapper) {
	  padding: 0 10px;
	}

	.directory-table :deep(.el-table__cell) {
	  padding: 10px 14px;
	}

.table-empty {
  padding: 2rem;
  color: #94a3b8;
  font-size: 14px;
}

.article-view {
  padding: 1.4rem 1.6rem 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  overflow: visible;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: flex-start;
}

.panel-eyebrow {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: #94a3b8;
  margin: 0;
  text-transform: uppercase;
}

.muted {
  color: #94a3b8;
  font-size: 13px;
}

.panel-actions {
  display: flex;
  gap: 0.4rem;
}

.circle-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(15, 23, 42, 0.06);
  color: #0f172a;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.circle-btn.primary {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  color: #fff;
  box-shadow: 0 12px 24px rgba(59, 130, 246, 0.25);
}

.circle-btn.ghost {
  background: rgba(14, 165, 233, 0.12);
  color: #0ea5e9;
}

.circle-btn:hover {
  transform: translateY(-1px);
}

.filter-stack {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.filter-row {
  display: flex;
  gap: 0.6rem;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: var(--oa-filter-control-bg);
  box-shadow: none;
}

.pill-input :deep(.el-input__inner),
.pill-input :deep(.el-select__selected-item) {
  font-size: 13px;
}

.directory-tree {
  max-height: calc(100vh - 320px);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.directory-tree.is-collapsed {
  padding-right: 0;
}

.directory-tree.is-collapsed .tree-node {
  justify-content: center;
}

.knowledge-tree {
  background: transparent;
}

.knowledge-tree :deep(.el-tree-node__content) {
  height: auto;
  padding: 0.2rem 0.4rem 0.2rem 0;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 0.5rem;
}

.tree-node.directory-node {
  font-weight: 600;
  color: #0f172a;
}

.node-count {
  font-size: 12px;
  color: #94a3b8;
}

.tree-node.article-node {
  font-weight: 500;
  color: #0f172a;
  gap: 0.4rem;
}

.directory-tree.is-collapsed .tree-node.article-node .article-title {
  display: none;
}

.article-title {
  border: none;
  background: none;
  padding: 0;
  font-size: 14px;
  color: inherit;
  cursor: pointer;
  text-align: left;
  flex: 1;
}

.ellipsis-btn {
  border: none;
  background: rgba(148, 163, 184, 0.2);
  color: #475569;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.ellipsis-btn:hover {
  background: rgba(14, 165, 233, 0.2);
  color: #0ea5e9;
}

.ghost.mini {
  border: none;
  background: rgba(148, 163, 184, 0.2);
  color: #0f172a;
  padding: 0.2rem 0.65rem;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.ghost.mini:hover {
  background: rgba(14, 165, 233, 0.18);
}

.tree-article-menu {
  border-radius: 12px;
}

.empty-hint {
  border: 1px dashed #d7deed;
  border-radius: 14px;
  padding: 0.8rem;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.empty-hint.small {
  border: none;
  padding: 0.4rem;
  text-align: left;
  font-size: 12px;
  color: #a0aec0;
}

.article-hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.hero-actions {
  display: flex;
  gap: 0.6rem;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.75rem;
  margin-top: 0.4rem;
}

.meta-chip {
  font-size: 13px;
  color: #475569;
  background: rgba(148, 163, 184, 0.18);
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  line-height: 1.5;
}

.meta-chip strong {
  font-weight: 600;
  color: #0f172a;
}

.btn {
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1.4rem;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.btn.primary {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  color: #fff;
  box-shadow: 0 12px 26px rgba(14, 165, 233, 0.25);
}

.btn.ghost {
  background: rgba(15, 23, 42, 0.06);
  color: #0f172a;
}

.btn.sm {
  padding: 0.35rem 1rem;
  font-size: 13px;
}

.article-body {
  border: none;
  padding: 0;
  background: transparent;
  color: var(--oa-text-primary);
  line-height: 1.7;
  min-height: 280px;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.article-body :deep(h1),
.article-body :deep(h2),
.article-body :deep(h3) {
  margin: 1rem 0 0.4rem;
}

.article-body :deep(p) {
  margin: 0.4rem 0;
}

.article-body :deep(img),
.article-body :deep(video),
.article-body :deep(iframe) {
  max-width: 100%;
  height: auto;
}

.article-body :deep(pre) {
  max-width: 100%;
  overflow: auto;
}

.article-body :deep(table) {
  display: block;
  max-width: 100%;
  overflow-x: auto;
}

.empty-view {
  min-height: 520px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0.6rem;
  color: #64748b;
}

.file-input {
  width: 100%;
  padding: 0.35rem 0;
}

.error-text {
  color: #dc2626;
  font-size: 12px;
  margin-top: 0.25rem;
}

.category-editor {
  margin-bottom: 8px;
}

.directory-manager__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.left-actions,
.right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.right-actions {
  margin-left: auto;
}

.dialog-shell :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.15);
  border: 1px solid rgba(228, 233, 245, 0.9);
}

.dialog-shell :deep(.el-dialog__header) {
  padding: 1.2rem 1.5rem 0.6rem;
  border-bottom: 1px solid #edf1f7;
  margin-right: 0;
}

.dialog-shell :deep(.el-dialog__body) {
  background: #f8fafc;
  padding: 1.2rem 1.5rem;
}

.dialog-shell :deep(.el-dialog__footer) {
  padding: 0.85rem 1.5rem 1.2rem;
  border-top: 1px solid #edf1f7;
}

.dialog-shell :deep(.el-button) {
  border-radius: 999px;
  font-weight: 600;
  padding: 0.4rem 1.3rem;
}

.dialog-shell :deep(.el-button--primary) {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  border: none;
  box-shadow: 0 10px 22px rgba(14, 165, 233, 0.28);
}

.dialog-shell :deep(.el-button:not(.el-button--primary)) {
  background: rgba(15, 23, 42, 0.05);
  border: none;
  color: #0f172a;
}

.dialog-shell :deep(.el-input__wrapper),
.dialog-shell :deep(.el-select__wrapper) {
  border-radius: 14px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.25);
}

.dialog-shell :deep(.el-textarea__inner) {
  border-radius: 16px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.3);
  padding: 0.85rem;
}

@media (max-width: 1280px) {
  .knowledge-shell {
    grid-template-columns: 1fr;
  }

  .directory-tree {
    max-height: none;
  }
}
</style>
