import { defineStore } from 'pinia';

import { listScriptPlugins, type ScriptPluginRecord } from '@/services/toolsApi';

interface State {
  plugins: Record<string, ScriptPluginRecord>;
  loading: boolean;
}

export const useScriptPluginStore = defineStore('script-plugins', {
  state: (): State => ({
    plugins: {},
    loading: false
  }),
  getters: {
    isPluginEnabled: (state) => (slug?: string) => {
      if (!slug) return true;
      const plugin = state.plugins[slug];
      if (!plugin) return true;
      return plugin.is_enabled !== false;
    }
  },
  actions: {
    async fetchScriptPlugins(force = false) {
      if (this.loading) return;
      if (!force && Object.keys(this.plugins).length) return;
      this.loading = true;
      try {
        const list = await listScriptPlugins();
        const map: Record<string, ScriptPluginRecord> = {};
        list.forEach((item) => {
          map[item.slug] = item;
        });
        this.plugins = map;
      } catch (error) {
        console.warn('Failed to load script plugins.', error);
        this.plugins = {};
      } finally {
        this.loading = false;
      }
    },
    async reload() {
      this.plugins = {};
      await this.fetchScriptPlugins(true);
    }
  }
});
