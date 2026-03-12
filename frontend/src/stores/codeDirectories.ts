import { defineStore } from 'pinia';
import { ref } from 'vue';

import { listCodeDirectories } from '@/services/codeRepositoryApi';

export interface DirectoryPreset {
  key: string;
  title: string;
  description?: string;
  keywords: string[];
  builtin?: boolean;
}

export const DIRECTORY_PRESETS: DirectoryPreset[] = [
  {
    key: 'probe',
    title: '探针脚本',
    description: '负责节点巡检、链路拨测等探针相关脚本。',
    keywords: ['探针', '巡检', 'probe'],
    builtin: true
  },
  {
    key: 'assets',
    title: '资产同步',
    description: '同步 CMDB、IPMP、Zabbix 等资产的脚本。',
    keywords: ['资产', 'cmdb', 'ipmp', 'zabbix'],
    builtin: true
  },
  {
    key: 'monitoring',
    title: '监控与报表',
    description: '用于监控数据采集、指标聚合与报表输出。',
    keywords: ['监控', 'prometheus', 'report', '报表'],
    builtin: true
  },
  {
    key: 'tools',
    title: '工具库',
    description: '故障排障、日志分析等工具类脚本。',
    keywords: ['工具', '日志', '分析', 'tool'],
    builtin: true
  },
  {
    key: 'general',
    title: '通用脚本',
    description: '暂未分类的脚本集合。',
    keywords: [],
    builtin: true
  }
];

export const normalizeDirectories = (list: Array<Partial<DirectoryPreset>>): DirectoryPreset[] =>
  list
    .map((dir) => ({
      key: dir.key || '',
      title: dir.title || '',
      description: dir.description || '',
      keywords: Array.isArray(dir.keywords) ? dir.keywords : [],
      builtin: dir.builtin ?? DIRECTORY_PRESETS.some((preset) => preset.key === dir.key)
    }))
    .filter((dir) => dir.key && dir.title);

export const useCodeDirectoryStore = defineStore('codeDirectories', () => {
  const directories = ref<DirectoryPreset[]>([]);
  const loading = ref(false);
  const initialized = ref(false);

  const ensureDefaults = () => {
    if (!directories.value.length) {
      directories.value = normalizeDirectories(DIRECTORY_PRESETS);
    }
  };

  const fetchDirectories = async () => {
    loading.value = true;
    try {
      const data = await listCodeDirectories();
      directories.value = normalizeDirectories(data);
    } catch (error) {
      console.error('加载脚本目录失败', error);
    } finally {
      loading.value = false;
      initialized.value = true;
      ensureDefaults();
    }
    return directories.value;
  };

  const setDirectories = (list: DirectoryPreset[]) => {
    directories.value = normalizeDirectories(list);
  };

  return {
    directories,
    loading,
    initialized,
    fetchDirectories,
    setDirectories
  };
});
