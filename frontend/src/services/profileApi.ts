import apiClient from '@/services/apiClient';

export type ProfileRecord = {
  id: string;
  username: string;
  display_name?: string;
  email?: string;
  phone?: string;
  roles: string[];
  permissions: string[];
  auth_source?: string;
};

export async function fetchMyProfile() {
  const { data } = await apiClient.get<ProfileRecord>('/auth/profile');
  return data;
}

export type UpdateMyProfilePayload = Partial<Pick<ProfileRecord, 'display_name' | 'email' | 'phone'>>;

export async function updateMyProfile(payload: UpdateMyProfilePayload) {
  const { data } = await apiClient.patch<ProfileRecord>('/auth/profile', payload);
  return data;
}

export async function changeMyPassword(payload: {
  current_password: string;
  new_password: string;
  confirm_new_password?: string;
}) {
  const { data } = await apiClient.post<{ detail: string }>('/auth/change-password', payload);
  return data;
}
