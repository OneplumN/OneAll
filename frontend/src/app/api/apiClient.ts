import axios from 'axios';

import { getAccessToken, setAccessToken as setSharedAccessToken } from '@/app/auth/accessToken';

let redirectingToLogin = false;

function isLocalHostname(host?: string) {
  if (!host) return true;
  return ['localhost', '127.0.0.1', '::1'].includes(host);
}

function isLocalUrl(url: string) {
  try {
    const parsed = new URL(url);
    return isLocalHostname(parsed.hostname);
  } catch (error) {
    return false;
  }
}

function resolveBaseURL() {
  const envUrl = import.meta.env.VITE_API_BASE_URL?.trim();

  if (envUrl) {
    if (typeof window === 'undefined') {
      return envUrl;
    }

    const host = window.location.hostname;
    if (!isLocalUrl(envUrl) || isLocalHostname(host)) {
      return envUrl;
    }
    // env 指向本地但当前访问来自远程主机，回退到自动推导
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    const safeProtocol = protocol === 'https:' ? 'https:' : 'http:';
    const host = hostname && hostname !== '0.0.0.0' ? hostname : '127.0.0.1';
    return `${safeProtocol}//${host}:8000/api`;
  }

  return 'http://127.0.0.1:8000/api';
}

const apiClient = axios.create({
  baseURL: resolveBaseURL(),
  timeout: 15000
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function applyApiClientAccessToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }
  delete apiClient.defaults.headers.common.Authorization;
}

function redirectToLogin() {
  if (typeof window === 'undefined') return;
  if (redirectingToLogin) return;
  redirectingToLogin = true;

  const current = window.location.pathname + window.location.search + window.location.hash;
  const redirect = encodeURIComponent(current || '/');
  window.location.replace(`/login?redirect=${redirect}`);
}

function isAuthErrorDetail(detail?: unknown) {
  if (typeof detail !== 'string') return false;
  // 覆盖 DRF 默认中文/英文，以及部分环境的简化文案
  return (
    detail.includes('身份认证') ||
    detail.includes('认证') ||
    detail.includes('未提供') ||
    detail.toLowerCase().includes('not authenticated') ||
    detail.toLowerCase().includes('authentication') ||
    detail.toLowerCase().includes('invalid token') ||
    detail === '权限不足'
  );
}

apiClient.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const detail = (error.response?.data as any)?.detail;
      const url = String(error.config?.url || '');

      // 避免对登录/个人信息接口循环跳转
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/profile') || url.includes('/auth/me');
      if (!isAuthEndpoint && (status === 401 || (status === 403 && isAuthErrorDetail(detail)))) {
        setSharedAccessToken(null);
        applyApiClientAccessToken(null);
        redirectToLogin();
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
