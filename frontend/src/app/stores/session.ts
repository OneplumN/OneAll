import axios from 'axios';
import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

import apiClient, { applyApiClientAccessToken } from '@/app/api/apiClient';
import {
  getAccessToken as getSharedAccessToken,
  setAccessToken as setSharedAccessToken,
  subscribeAccessToken,
} from '@/app/auth/accessToken';

interface LoginPayload {
  username: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type?: string;
  user?: SessionUser;
  refresh_token?: string;
  expires_in?: number;
}

export interface SessionUser {
  id: string;
  username: string;
  display_name?: string;
  email?: string;
  phone?: string;
  roles: string[];
  permissions: string[];
  auth_source?: string;
  is_admin?: boolean;
}

export const useSessionStore = defineStore('session', () => {
  const accessToken = ref<string | null>(getSharedAccessToken());
  const user = ref<SessionUser | null>(null);
  const loading = ref(false);

  subscribeAccessToken((token) => {
    accessToken.value = token;
    if (!token) {
      user.value = null;
    }
  });

  const isAuthenticated = computed(() => Boolean(accessToken.value));
  const permissionSet = computed(() => new Set(user.value?.permissions ?? []));

  async function login(payload: LoginPayload) {
    loading.value = true;
    try {
      const { data } = await apiClient.post<AuthResponse>('/auth/login', payload);
      setAccessToken(data.access_token);
      if (data.user) {
        user.value = data.user;
      } else {
        await fetchProfile();
      }
    } finally {
      loading.value = false;
    }
  }

  function setAccessToken(token: string | null) {
    setSharedAccessToken(token);
    applyApiClientAccessToken(token);
  }

  async function fetchProfile() {
    if (!accessToken.value) return;
    try {
      const { data } = await apiClient.get<SessionUser>('/auth/profile');
      user.value = data;
    } catch (error: any) {
      const status = axios.isAxiosError(error) ? error.response?.status : undefined;
      if (status === 401 || status === 403) {
        console.warn('Profile request unauthorized, clearing session.', error);
        logout();
      } else {
        console.warn('Failed to fetch profile (network/server). Keeping session.', error);
      }
      throw error;
    }
  }

  function logout() {
    setAccessToken(null);
    user.value = null;
  }

  return {
    user,
    loading,
    accessToken,
    isAuthenticated,
    login,
    logout,
    fetchProfile,
    setAccessToken,
    hasPermission
  };

  function hasPermission(code?: string) {
    if (!code) return true;
    const perms = permissionSet.value;
    if (perms.has(code)) return true;
    const parts = code.split('.');
    if (parts.length === 3 && parts[2] === 'view') {
      const prefix = `${parts[0]}.${parts[1]}.`;
      return Array.from(perms).some((perm) => perm.startsWith(prefix));
    }
    return false;
  }
});
