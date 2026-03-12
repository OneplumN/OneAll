import apiClient from './apiClient';

export interface KnowledgeAttachment {
  name: string;
  url: string;
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  slug?: string;
  category: string;
  category_label?: string;
  tags: string[];
  content: string;
  attachments?: KnowledgeAttachment[];
  visibility_scope: 'public' | 'internal' | 'restricted';
  last_edited_at?: string;
  last_editor?: string;
  metadata?: Record<string, any>;
}

export interface KnowledgeSearchQuery {
  keyword?: string;
  category?: string;
  tags?: string[];
  scope?: string;
}

export interface CreateArticlePayload {
  title: string;
  category: string;
  tags: string[];
  visibility_scope: 'public' | 'internal' | 'restricted';
  content: string;
  attachments?: KnowledgeAttachment[];
}

export interface KnowledgeCategory {
  key: string;
  title: string;
  description?: string;
  builtin?: boolean;
  display_order?: number;
  article_count?: number;
}

export interface KnowledgeCategoryPayload {
  key?: string;
  title: string;
  description?: string;
  display_order?: number;
}

export interface KnowledgeArticleVersion {
  id: string;
  version: number;
  title: string;
  category: string;
  visibility_scope: string;
  tags: string[];
  content: string;
  summary: string;
  created_at: string;
  editor?: string | null;
}

export async function searchArticles(query: KnowledgeSearchQuery) {
  const { data } = await apiClient.get<KnowledgeArticle[]>('/knowledge/articles', {
    params: query
  });
  return data;
}

export async function getArticle(slug: string) {
  const { data } = await apiClient.get<KnowledgeArticle>(`/knowledge/articles/${slug}`);
  return data;
}

export async function deleteArticle(slug: string) {
  await apiClient.delete(`/knowledge/articles/${slug}`);
}

export async function listArticleVersions(slug: string) {
  const { data } = await apiClient.get<KnowledgeArticleVersion[]>(`/knowledge/articles/${slug}/versions`);
  return data;
}

export async function listCategories() {
  const { data } = await apiClient.get<KnowledgeCategory[]>('/knowledge/categories');
  return data;
}

export async function createCategory(payload: KnowledgeCategoryPayload) {
  const { data } = await apiClient.post<KnowledgeCategory>('/knowledge/categories', payload);
  return data;
}

export async function updateCategory(key: string, payload: KnowledgeCategoryPayload) {
  const { data } = await apiClient.put<KnowledgeCategory>(`/knowledge/categories/${key}`, payload);
  return data;
}

export async function deleteCategory(key: string) {
  await apiClient.delete(`/knowledge/categories/${key}`);
}

export async function reorderCategories(keys: string[]) {
  const { data } = await apiClient.post<KnowledgeCategory[]>('/knowledge/categories/order', { keys });
  return data;
}

export async function createArticleFromUpload(form: FormData) {
  const { data } = await apiClient.post<KnowledgeArticle>('/knowledge/articles', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

export async function updateArticleFromUpload(slug: string, form: FormData) {
  const { data } = await apiClient.put<KnowledgeArticle>(`/knowledge/articles/${slug}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}
