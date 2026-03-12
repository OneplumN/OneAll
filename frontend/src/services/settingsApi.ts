import apiClient from './apiClient';

export interface RolePayload {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface PermissionAction {
  key: string;
  label: string;
  actions: string[];
  scope?: string;
}

export interface PermissionModule {
  key: string;
  label: string;
  children: PermissionAction[];
}

export interface UserRoleRecord {
  id: string;
  username: string;
  display_name: string;
  email: string;
  roles: string[];
  auth_source?: string;
  external_synced_at?: string | null;
  is_superuser?: boolean;
}

export interface LdapSyncStats {
  total: number;
  created: number;
  updated: number;
  skipped: number;
  assigned_roles: number;
}

export interface RoleInput {
  name: string;
  description?: string;
  permissions: string[];
}

export type AlertChannelFieldType = 'text' | 'secret' | 'textarea' | 'switch' | 'number' | 'select';

export interface AlertChannelField {
  key: string;
  label: string;
  type: AlertChannelFieldType;
  placeholder?: string;
  options?: string[];
}

export interface AlertChannelRecord {
  id: string;
  type: string;
  name: string;
  description: string;
  enabled: boolean;
  config: Record<string, any>;
  config_schema: AlertChannelField[];
  last_test_status: string;
  last_test_at?: string | null;
  last_test_message?: string;
}

export interface AlertTemplateRecord {
  id: string;
  channel_type: string;
  channel_label: string;
  variables: Record<string, string>;
  name: string;
  description?: string;
  subject?: string;
  body: string;
  is_default: boolean;
  updated_at: string;
}

export async function fetchPermissionCatalog() {
  const { data } = await apiClient.get<{ modules: PermissionModule[] }>('/settings/permissions/catalog');
  return data.modules;
}

export async function fetchRoles() {
  const { data } = await apiClient.get<RolePayload[]>('/settings/roles/');
  return data;
}

export async function createRole(payload: RoleInput) {
  const { data } = await apiClient.post<RolePayload>('/settings/roles/', payload);
  return data;
}

export async function updateRole(roleId: string, payload: RoleInput) {
  const { data } = await apiClient.put<RolePayload>(`/settings/roles/${roleId}/`, payload);
  return data;
}

export async function deleteRole(roleId: string) {
  await apiClient.delete(`/settings/roles/${roleId}/`);
}

export async function fetchUserRoles() {
  const { data } = await apiClient.get<UserRoleRecord[]>('/settings/users');
  return data;
}

export interface LocalUserCreatePayload {
  username: string;
  display_name?: string;
  email?: string;
  password: string;
  role_id?: string | null;
}

export async function createLocalUser(payload: LocalUserCreatePayload) {
  const { data } = await apiClient.post<UserRoleRecord>('/settings/users', payload);
  return data;
}

export async function updateUserRoles(userId: string, roleIds: string[]) {
  const { data } = await apiClient.put<UserRoleRecord>(`/settings/users/${userId}/roles`, { role_ids: roleIds });
  return data;
}

export async function deleteUser(userId: string) {
  await apiClient.delete(`/settings/users/${userId}`);
}

export async function syncLdapUsers() {
  const { data } = await apiClient.post<{ detail: string; result: LdapSyncStats }>(
    '/settings/users/sync-ldap',
    {}
  );
  return data;
}

export async function fetchAlertChannels() {
  const { data } = await apiClient.get<{ channels: AlertChannelRecord[] }>('/settings/alerts/channels');
  return data.channels;
}

export async function updateAlertChannel(channelType: string, payload: { enabled: boolean; config: Record<string, any> }) {
  const { data } = await apiClient.put<AlertChannelRecord>(`/settings/alerts/channels/${channelType}`, payload);
  return data;
}

export async function testAlertChannel(channelType: string) {
  const { data } = await apiClient.post<{ detail: string; status: string }>(
    `/settings/alerts/channels/${channelType}/test`,
    {}
  );
  return data;
}

export async function fetchAlertTemplates() {
  const { data } = await apiClient.get<AlertTemplateRecord[]>(`/settings/alerts/templates/`);
  return data;
}

export async function createAlertTemplate(payload: Partial<AlertTemplateRecord>) {
  const { data } = await apiClient.post<AlertTemplateRecord>(`/settings/alerts/templates/`, payload);
  return data;
}

export async function updateAlertTemplate(id: string, payload: Partial<AlertTemplateRecord>) {
  const { data } = await apiClient.patch<AlertTemplateRecord>(`/settings/alerts/templates/${id}/`, payload);
  return data;
}

export async function deleteAlertTemplate(id: string) {
  await apiClient.delete(`/settings/alerts/templates/${id}/`);
}
