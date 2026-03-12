<template>
  <div class="knowledge-view">
    <div class="repository-header">
      <div class="repository-header__info">
        <span class="header__title">知识库</span>
        <span class="header__separator">/</span>
        <span class="header__subtitle">{{ currentDirectoryTitle }}</span>
        <span class="header__separator">/</span>
        <span class="header__subtitle">{{ article?.title || '文章详情' }}</span>
      </div>
      <div class="repository-header__actions">
        <el-button class="toolbar-button" @click="goBack">返回知识库</el-button>
        <el-button v-if="canCloseWindow" class="toolbar-button" @click="closeWindow">关闭窗口</el-button>
        <el-button v-if="tocItems.length" class="toolbar-button" @click="tocDrawerVisible = true">目录</el-button>
        <el-button class="toolbar-button" :disabled="!article" @click="openVersionsDialog">版本记录</el-button>
        <el-button
          class="toolbar-button toolbar-button--primary"
          type="primary"
          :disabled="!article || !canCreateArticle"
          @click="article && goToUpload()"
        >
          上传新版本
        </el-button>
      </div>
    </div>

    <div
      v-if="article"
      class="knowledge-detail-page"
      v-loading="loadingArticle"
      element-loading-background="rgba(255,255,255,0.4)"
    >
      <div class="article-head glass-card">
        <div class="article-head__title">{{ article.title }}</div>
        <el-descriptions :column="4" size="small" class="article-head__meta">
          <el-descriptions-item label="目录">
            {{ categoryLabel(article.category, article.category_label) }}
          </el-descriptions-item>
          <el-descriptions-item label="访问范围">
            {{ scopeLabel(article.visibility_scope) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新人">
            {{ article.last_editor || '系统' }}
          </el-descriptions-item>
          <el-descriptions-item label="最近更新">
            {{ formatTime(article.last_edited_at) }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="detail-tags" v-if="article.tags?.length">
          <div class="detail-tags__label">标签</div>
          <el-space wrap size="6">
            <el-tag v-for="tag in article.tags" :key="tag" size="small" round>
              {{ tag }}
            </el-tag>
          </el-space>
        </div>
      </div>

      <div class="detail-layout">
        <div class="detail-left glass-card">
          <article ref="articleRef" class="article-body" v-html="article.content" />
        </div>
      </div>
    </div>

    <div v-else class="empty-view glass-card">
      <p>正在加载文章...</p>
    </div>

    <el-drawer
      v-model="tocDrawerVisible"
      title="文章目录"
      direction="rtl"
      size="360px"
      append-to-body
    >
      <div class="toc-list">
        <div
          v-for="item in tocItems"
          :key="item.id"
          :class="['toc-item', `toc-item--d${item.depth}`]"
          @click="scrollToHeading(item.id)"
        >
          {{ item.text }}
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="versionsDialogVisible" title="版本记录" width="720px" append-to-body>
      <el-table
        :data="pagedArticleVersions"
        v-loading="versionsLoading"
        height="420"
        empty-text="暂无版本记录"
      >
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="editor" label="更新人" width="160">
          <template #default="{ row }">{{ row.editor || '系统' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="更新时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="240">
          <template #default="{ row }">{{ row.summary || '未填写摘要' }}</template>
        </el-table-column>
      </el-table>
      <div class="dialog-pagination">
        <el-pagination
          v-model:current-page="versionsPage"
          v-model:page-size="versionsPageSize"
          layout="total, prev, pager, next, sizes"
          :page-sizes="versionsPageSizeOptions"
          :total="articleVersions.length"
          :disabled="versionsLoading"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  getArticle,
  listArticleVersions,
  type KnowledgeArticle,
  type KnowledgeArticleVersion
} from '@/services/knowledgeApi';
import { useSessionStore } from '@/stores/session';

const route = useRoute();
const router = useRouter();
const sessionStore = useSessionStore();

const canCreateArticle = computed(() => sessionStore.hasPermission('knowledge.articles.create'));
const canCloseWindow = computed(() => {
  if (typeof window === 'undefined') return false;
  return Boolean((window as any).opener);
});

const article = ref<KnowledgeArticle | null>(null);
const loadingArticle = ref(false);
const articleVersions = ref<KnowledgeArticleVersion[]>([]);
const versionsDialogVisible = ref(false);
const versionsLoading = ref(false);
const versionsPage = ref(1);
const versionsPageSizeOptions = [10, 20, 50];
const versionsPageSize = ref(10);

const tocDrawerVisible = ref(false);
const tocItems = ref<Array<{ id: string; text: string; depth: number }>>([]);
const articleRef = ref<HTMLElement | null>(null);

const loadArticleDetail = async (slug: string) => {
  loadingArticle.value = true;
  try {
    article.value = await getArticle(slug);
    await nextTick();
    buildToc();
  } catch (error) {
    console.error('加载文章失败', error);
    ElMessage.error('文章不存在或已删除');
    router.push('/knowledge');
  } finally {
    loadingArticle.value = false;
  }
};

const openVersionsDialog = async () => {
  versionsDialogVisible.value = true;
  versionsPage.value = 1;
  if (!article.value) return;
  try {
    versionsLoading.value = true;
    articleVersions.value = await listArticleVersions(article.value.slug || article.value.id);
  } catch (error) {
    console.warn('加载版本失败', error);
    articleVersions.value = [];
  } finally {
    versionsLoading.value = false;
  }
};

const goBack = () => {
  router.push('/knowledge');
};

const closeWindow = () => {
  if (typeof window === 'undefined') return;
  window.close();
};

const goToUpload = () => {
  if (!article.value) return;
  router.push({ path: '/knowledge', query: { upload: 'update', slug: article.value.slug || article.value.id } });
};

const formatTime = (value?: string, mode: 'full' | 'short' = 'full') => {
  if (!value) return '未记录';
  return mode === 'short' ? dayjs(value).format('MM-DD HH:mm') : dayjs(value).format('YYYY-MM-DD HH:mm');
};
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

const categoryLabel = (key?: string, fallback?: string) => {
  if (!key) return fallback || '未分类';
  return fallback || key;
};

const currentDirectoryTitle = computed(() => {
  if (!article.value) return '全部';
  return categoryLabel(article.value.category, article.value.category_label);
});

const pagedArticleVersions = computed(() => {
  const start = (versionsPage.value - 1) * versionsPageSize.value;
  return articleVersions.value.slice(start, start + versionsPageSize.value);
});

onMounted(async () => {
  const slug = route.params.slug as string;
  await loadArticleDetail(slug);
});

watch(
  () => route.params.slug,
  (slug) => {
    if (!slug) return;
    void loadArticleDetail(String(slug));
  }
);

const headingSelector = 'h1, h2, h3, h4';
const buildToc = () => {
  const root = articleRef.value;
  if (!root) return;
  const nodes = Array.from(root.querySelectorAll(headingSelector));
  tocItems.value = nodes.map((node, index) => {
    const depth = Number(node.tagName.replace('H', ''));
    const id = node.id || `article-heading-${index}`;
    node.id = id;
    return {
      id,
      depth,
      text: node.textContent?.trim() || `标题 ${index + 1}`
    };
  });
};

const scrollToHeading = (id: string) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  tocDrawerVisible.value = false;
};
</script>

<style scoped>
.knowledge-view {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 16px 16px;
  scrollbar-gutter: stable;
  background: #fff;
}

.glass-card {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--oa-border-light);
  box-shadow: var(--oa-shadow-sm);
}

.repository-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--oa-border-light);
  background: #fff;
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

.toolbar-button {
  border-radius: 6px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

.toolbar-button--primary {
  font-weight: 600;
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

.dialog-pagination {
  margin-top: 12px;
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

.toc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toc-item {
  cursor: pointer;
  padding: 8px 10px;
  border-radius: 8px;
  color: var(--oa-text-secondary);
  transition: background-color 0.15s ease, color 0.15s ease;
  line-height: 1.4;
}

.toc-item:hover {
  background: rgba(64, 158, 255, 0.08);
  color: var(--oa-text-primary);
}

.toc-item--d2 {
  padding-left: 18px;
}

.toc-item--d3 {
  padding-left: 26px;
}

.toc-item--d4 {
  padding-left: 34px;
}
</style>
