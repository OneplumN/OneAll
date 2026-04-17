import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import apiClient from '@/app/api/apiClient';

type BrandingPayload = {
  platform_name?: string;
  platform_logo?: string;
  theme?: string;
};

const STORAGE_KEY_NAME = 'oneall_platform_name';
const STORAGE_KEY_LOGO = 'oneall_platform_logo';
const STORAGE_KEY_THEME = 'oneall_platform_theme';

export const useBrandingStore = defineStore('branding', () => {
  const platformName = ref(localStorage.getItem(STORAGE_KEY_NAME) || '多维运维平台');
  const platformLogo = ref(localStorage.getItem(STORAGE_KEY_LOGO) || '');
  const theme = ref(localStorage.getItem(STORAGE_KEY_THEME) || 'light');
  const loaded = ref(false);

  const hasLogo = computed(() => Boolean(platformLogo.value));

  const applyBranding = (payload: BrandingPayload) => {
    if (payload.platform_name !== undefined && payload.platform_name !== null) {
      platformName.value = String(payload.platform_name) || platformName.value;
      localStorage.setItem(STORAGE_KEY_NAME, platformName.value);
    }
    if (payload.platform_logo !== undefined && payload.platform_logo !== null) {
      platformLogo.value = String(payload.platform_logo || '');
      localStorage.setItem(STORAGE_KEY_LOGO, platformLogo.value);
    }
    if (payload.theme !== undefined && payload.theme !== null) {
      theme.value = String(payload.theme || theme.value);
      localStorage.setItem(STORAGE_KEY_THEME, theme.value);
    }
  };

  const fetchBranding = async () => {
    try {
      const { data } = await apiClient.get<BrandingPayload>('/public/branding');
      applyBranding(data);
      loaded.value = true;
    } catch {
      // 无后端或未开放接口时，保持本地缓存/默认值
    }
  };

  return {
    platformName,
    platformLogo,
    theme,
    loaded,
    hasLogo,
    applyBranding,
    fetchBranding,
  };
});
