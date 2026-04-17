import { defineStore } from 'pinia';
import { ref } from 'vue';

import type { AssetModel } from '@/features/assets/api/assetsApi';
import { fetchAssetModels } from '@/features/assets/api/assetsApi';

export const useAssetModelStore = defineStore('assetModels', () => {
  const models = ref<AssetModel[]>([]);
  const loading = ref(false);
  const initialized = ref(false);

  const fetchModels = async () => {
    loading.value = true;
    try {
      const data = await fetchAssetModels();
      models.value = data || [];
    } catch (error) {
      console.error('加载资产模型失败', error);
    } finally {
      loading.value = false;
      initialized.value = true;
    }
    return models.value;
  };

  return {
    models,
    loading,
    initialized,
    fetchModels
  };
});
