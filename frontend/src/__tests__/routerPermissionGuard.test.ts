import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { createMemoryHistory, createRouter } from 'vue-router';

import { installAuthGuard } from '@/router/guards';
import { useSessionStore } from '@/app/stores/session';

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: { template: '<div />' } },
      { path: '/403', name: 'forbidden', component: { template: '<div />' } },
      {
        path: '/secure',
        name: 'secure',
        component: { template: '<div />' },
        meta: {
          requiresAuth: true,
          permission: 'settings.roles.view',
          modulePermission: 'settings.module.access',
        },
      },
    ],
  });
}

describe('router permission guard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects authenticated users without route permission to 403', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const router = createTestRouter();
    installAuthGuard(router, pinia);

    const session = useSessionStore(pinia);
    session.setAccessToken('token');
    session.user = {
      id: 'u-1',
      username: 'tester',
      roles: [],
      permissions: ['settings.module.access'],
      auth_source: 'local',
      is_admin: false,
    };

    await router.push('/secure');
    expect(router.currentRoute.value.name).toBe('forbidden');
  });

  it('allows authenticated users with route permission', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const router = createTestRouter();
    installAuthGuard(router, pinia);

    const session = useSessionStore(pinia);
    session.setAccessToken('token');
    session.user = {
      id: 'u-2',
      username: 'admin',
      roles: [],
      permissions: ['settings.module.access', 'settings.roles.view'],
      auth_source: 'local',
      is_admin: true,
    };

    await router.push('/secure');
    expect(router.currentRoute.value.name).toBe('secure');
  });
});
