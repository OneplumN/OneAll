import { watchEffect } from 'vue';
import { useI18n } from 'vue-i18n';

import { useBrandingStore } from '@/stores/branding';

export function usePageTitle(titleKey: string, params?: Record<string, unknown> | (() => Record<string, unknown>)) {
  const { t } = useI18n();
  const branding = useBrandingStore();

  watchEffect(() => {
    if (typeof document === 'undefined') return;
    const base = branding.platformName || t('common.appName');
    const resolvedParams = typeof params === 'function' ? params() : params;
    const title = resolvedParams ? t(titleKey, resolvedParams) : t(titleKey);
    document.title = `${title} · ${base}`;
  });
}
