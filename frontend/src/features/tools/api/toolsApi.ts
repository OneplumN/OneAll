import apiClient from '@/app/api/apiClient';

export interface ToolDefinition {
  id: string;
  name: string;
  category: string;
  tags: string[];
  description?: string;
  connector_version?: string;
  updated_at?: string;
}

export interface CreateToolPayload {
  name: string;
  category: string;
  tags: string[];
  description?: string;
  script_id?: string;
}

export interface ExecuteToolPayload {
  parameters?: Record<string, unknown>;
  run_policy?: string;
}

export interface ToolExecutionResult {
  run_id: string;
  status: string;
  output?: string;
  started_at?: string;
  finished_at?: string;
  metadata?: Record<string, any>;
}

export interface ToolExecutionRecord extends ToolExecutionResult {
  id: string;
  tool?: ToolDefinition;
  error_message?: string;
  created_at?: string;
  script_version?: { id: string; version: string };
}

export interface IpRegexCompileResponse {
  regex: string;
  matched_count: number;
  invalid_ips: string[];
}

export interface IpRegexExpandResponse {
  ips: string[];
  count: number;
  limit: number;
}

export async function listTools(query?: Record<string, unknown>) {
  const { data } = await apiClient.get<ToolDefinition[]>('/tools/definitions', {
    params: query
  });
  return data;
}

export async function createTool(payload: CreateToolPayload) {
  const { data } = await apiClient.post<ToolDefinition>('/tools/definitions', payload);
  return data;
}

export async function executeTool(toolId: string, payload: ExecuteToolPayload) {
  const { data } = await apiClient.post<ToolExecutionResult>(`/tools/definitions/${toolId}/execute`, payload);
  return data;
}

export async function listToolExecutions(query?: Record<string, unknown>) {
  const { data } = await apiClient.get<ToolExecutionRecord[]>('/tools/executions', {
    params: query
  });
  return data;
}

export async function compileIpRegex(ips: string[]) {
  const { data } = await apiClient.post<IpRegexCompileResponse>('/tools/ip-regex/compile', { ips });
  return data;
}

export async function expandRegexToIps(pattern: string, limit?: number) {
  const payload: Record<string, unknown> = { pattern };
  if (limit) {
    payload.limit = limit;
  }
  const { data } = await apiClient.post<IpRegexExpandResponse>('/tools/ip-regex/expand', payload);
  return data;
}

export interface ScriptPluginRecord {
  id: string;
  slug: string;
  name: string;
  description?: string;
  summary?: string;
  group: string;
  route?: string;
  component?: string;
  builtin: boolean;
  is_enabled: boolean;
  runtime_script?: string;
  metadata?: Record<string, any>;
}

export async function listScriptPlugins() {
  const { data } = await apiClient.get<ScriptPluginRecord[]>('/tools/script-plugins');
  return data;
}

export async function getScriptPlugin(slug: string) {
  const { data } = await apiClient.get<ScriptPluginRecord>(`/tools/script-plugins/${slug}`);
  return data;
}

export async function updateScriptPlugin(
  slug: string,
  payload: Partial<Pick<ScriptPluginRecord, 'is_enabled' | 'route' | 'component' | 'summary'>> & { metadata?: Record<string, unknown> }
) {
  const { data } = await apiClient.patch<ScriptPluginRecord>(`/tools/script-plugins/${slug}`, payload);
  return data;
}

export async function executeScriptPlugin(slug: string, payload?: Record<string, unknown>) {
  const { data } = await apiClient.post<ToolExecutionResult>(`/tools/script-plugins/${slug}/execute`, {
    parameters: payload || {}
  });
  return data;
}
