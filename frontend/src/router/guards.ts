import type { Pinia } from 'pinia';
import type { Router } from 'vue-router';

import { useSessionStore } from '@/app/stores/session';
import { usePluginConfigStore } from '@/features/settings/stores/pluginConfigs';

export function installAuthGuard(router: Router, pinia: Pinia) {
  router.beforeEach(async (to) => {
    const session = useSessionStore(pinia);
    if (to.meta.requiresAuth && !session.isAuthenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath }
      };
    }

    if (to.meta.requiresAuth && session.isAuthenticated && !session.user) {
      try {
        await session.fetchProfile();
      } catch {
        return true;
      }
    }

    const modulePermission = to.meta.modulePermission as string | undefined;
    const routePermission = to.meta.permission as string | undefined;
    if ((modulePermission && !session.hasPermission(modulePermission)) || (routePermission && !session.hasPermission(routePermission))) {
      return { name: 'forbidden' };
    }

    const pluginType = to.meta.pluginType as string | undefined;
    const pluginStrict = Boolean(to.meta.pluginStrict);
    if (pluginType && pluginStrict) {
      const pluginStore = usePluginConfigStore(pinia);
      await pluginStore.fetchPluginConfigs();
      const plugin = pluginStore.plugins[pluginType];
      if (!plugin || plugin.enabled === false) {
        const fallback = (to.meta.fallbackPath as string) || '/';
        return { path: fallback };
      }
    }
    return true;
  });
}
