import apiClient from './apiClient';
import type { ToolExecutionResult } from './toolsApi';

export interface ScriptVersion {
  id: string;
  version: string;
  summary: string;
  created_at: string;
  created_by?: string;
  change_log?: string;
  content?: string;
}

export interface ScriptRepository {
  id: string;
  name: string;
  language: string;
  tags: string[];
  description?: string;
  latest_version?: string;
  updated_at?: string;
  directory?: string;
  content?: string;
}

export interface RepositoryExecutionPayload {
  parameters?: Record<string, unknown>;
}

export interface CreateRepositoryPayload {
  name: string;
  language: string;
  tags: string[];
  description?: string;
  content: string;
  change_log?: string;
  directory?: string;
}

export interface UploadVersionPayload {
  version: string;
  content: string;
  change_log?: string;
}

export interface UpdateRepositoryPayload {
  name?: string;
  language?: string;
  tags?: string[];
  description?: string;
  directory?: string;
  content?: string;
}

export interface CodeDirectory {
  key: string;
  title: string;
  description?: string;
  keywords: string[];
  builtin?: boolean;
}

export interface CodeDirectoryPayload {
  title: string;
  description?: string;
  keywords: string[];
}

export async function listRepositories() {
  const { data } = await apiClient.get<ScriptRepository[]>('/tools/repositories');
  return data;
}

export async function getRepository(repositoryId: string) {
  const { data } = await apiClient.get<ScriptRepository>(`/tools/repositories/${repositoryId}`);
  return data;
}

export async function listVersions(repositoryId: string) {
  const { data } = await apiClient.get<ScriptVersion[]>(`/tools/repositories/${repositoryId}/versions`);
  return data;
}

export async function createRepository(payload: CreateRepositoryPayload) {
  const { data } = await apiClient.post<ScriptRepository>('/tools/repositories', payload);
  return data;
}

export async function uploadVersion(repositoryId: string, payload: UploadVersionPayload) {
  const { data } = await apiClient.post<ScriptVersion>(
    `/tools/repositories/${repositoryId}/versions`,
    payload
  );
  return data;
}

export async function rollbackVersion(repositoryId: string, versionId: string) {
  await apiClient.post(`/tools/repositories/${repositoryId}/versions/${versionId}/rollback`, {});
}

export async function updateRepository(repositoryId: string, payload: UpdateRepositoryPayload) {
  const { data } = await apiClient.put<ScriptRepository>(`/tools/repositories/${repositoryId}`, payload);
  return data;
}

export async function deleteRepository(repositoryId: string) {
  await apiClient.delete(`/tools/repositories/${repositoryId}`);
}

export async function listCodeDirectories() {
  const { data } = await apiClient.get<CodeDirectory[]>('/code/directories');
  return data;
}

export async function createCodeDirectory(payload: CodeDirectoryPayload) {
  const { data } = await apiClient.post<CodeDirectory>('/code/directories', payload);
  return data;
}

export async function updateCodeDirectory(key: string, payload: CodeDirectoryPayload) {
  const { data } = await apiClient.put<CodeDirectory>(`/code/directories/${key}`, payload);
  return data;
}

export async function deleteCodeDirectory(key: string) {
  await apiClient.delete(`/code/directories/${key}`);
}

export async function executeRepositoryScript(repositoryId: string, payload?: RepositoryExecutionPayload) {
  const { data } = await apiClient.post<ToolExecutionResult>(
    `/tools/repositories/${repositoryId}/execute`,
    payload || {}
  );
  return data;
}
