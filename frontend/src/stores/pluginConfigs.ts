import { defineStore } from 'pinia';
import { listPluginConfigs, type PluginConfigRecord } from '@/services/monitoringApi';

interface State {
  plugins: Record<string, PluginConfigRecord>;
  loading: boolean;
}

export const usePluginConfigStore = defineStore('plugin-configs', {
  state: (): State => ({
    plugins: {},
    loading: false
  }),
  getters: {
    isPluginEnabled: (state) => (type?: string) => {
      if (!type) return true;
      const plugin = state.plugins[type];
      if (!plugin) return true;
      return plugin.enabled !== false;
    }
  },
  actions: {
    async fetchPluginConfigs(force = false) {
      if (this.loading) return;
      if (!force && Object.keys(this.plugins).length) return;
      this.loading = true;
      try {
        const list = await listPluginConfigs();
        const map: Record<string, PluginConfigRecord> = {};
        list.forEach((item) => {
          map[item.type] = item;
        });
        this.plugins = map;
      } catch (error) {
        console.warn('Failed to load plugin configs, skipping.', error);
        this.plugins = {};
      } finally {
        this.loading = false;
      }
    },
    async reload() {
      this.plugins = {};
      await this.fetchPluginConfigs(true);
    }
  }
});
