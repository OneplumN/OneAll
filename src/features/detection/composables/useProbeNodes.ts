import { computed, ref, type Ref } from 'vue';

import apiClient from '@/app/api/apiClient';

export type ProbeNode = {
  id: string;
  name: string;
  network_type: 'internal' | 'external' | string;
};

export function useProbeNodes(selectedNodeIds?: Ref<string[]>) {
  const nodes = ref<ProbeNode[]>([]);
  const loading = ref(false);
  const nodeMap = computed(() => new Map(nodes.value.map((node) => [node.id, node])));

  async function loadNodes() {
    loading.value = true;
    try {
      const { data } = await apiClient.get<ProbeNode[]>('/probes/nodes/');
      nodes.value = data;
      if (selectedNodeIds) {
        const available = new Set(data.map((node) => node.id));
        selectedNodeIds.value = selectedNodeIds.value.filter((id) => available.has(id));
      }
    } finally {
      loading.value = false;
    }
  }

  return { nodes, loading, nodeMap, loadNodes };
}

