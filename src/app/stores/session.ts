import axios from 'axios';
import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

import apiClient from '@/app/api/apiClient';

const USER_STORAGE_KEY = 'oneall_user_profile';

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
  const accessToken = ref<string | null>(localStorage.getItem('oneall_access_token'));
  applyAuthHeader(accessToken.value);

  const user = ref<SessionUser | null>(loadStoredUser());
  const loading = ref(false);

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
    accessToken.value = token;
    if (token) {
      localStorage.setItem('oneall_access_token', token);
    } else {
      localStorage.removeItem('oneall_access_token');
      localStorage.removeItem(USER_STORAGE_KEY);
    }
    applyAuthHeader(token);
  }

  async function fetchProfile() {
    if (!accessToken.value) return;
    try {
      const { data } = await apiClient.get<SessionUser>('/auth/profile');
      user.value = data;
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data));
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
    localStorage.removeItem(USER_STORAGE_KEY);
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

function applyAuthHeader(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

function loadStoredUser(): SessionUser | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<SessionUser>;
    if (!parsed || typeof parsed !== 'object') return null;
    if (!Array.isArray(parsed.permissions) || !Array.isArray(parsed.roles)) return null;
    if (typeof parsed.id !== 'string' || typeof parsed.username !== 'string') return null;
    return parsed as SessionUser;
  } catch (error) {
    console.warn('Failed to parse stored user profile.', error);
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}
