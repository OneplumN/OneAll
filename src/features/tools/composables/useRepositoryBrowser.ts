import { computed, reactive, ref, watch, type Component, type Ref } from 'vue';
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router';
import {
  Collection,
  DataAnalysis,
  Document,
  Monitor,
  Reading,
  Tools,
} from '@element-plus/icons-vue';

import type { ScriptRepository } from '@/features/tools/api/codeRepositoryApi';
import type { DirectoryPreset } from '@/features/tools/stores/codeDirectories';
import {
  type DirectoryGroup,
  BLOCKED_DIRECTORY_TITLES,
  formatRepositoryTime,
  matchDirectoryKey,
} from '@/features/tools/utils/repositoryPageHelpers';

const DIRECTORY_ICON_MAP: Record<string, Component> = {
  probe: Monitor,
  assets: Collection,
  monitoring: DataAnalysis,
  tools: Tools,
  general: Reading,
};

export function useRepositoryBrowser(options: {
  route: RouteLocationNormalizedLoaded;
  router: Router;
  directories: Ref<DirectoryPreset[]>;
  repositories: Ref<ScriptRepository[]>;
  selectedRepository: Ref<ScriptRepository | null>;
  detailRepository: Ref<ScriptRepository | null>;
}) {
  const {
    route,
    router,
    directories,
    repositories,
    selectedRepository,
    detailRepository,
  } = options;

  const selectedDirectoryKey = ref<string>('');
  const sidebarCollapsed = ref(false);
  const sidebarWidth = computed(() => (sidebarCollapsed.value ? '72px' : '240px'));
  const repoKeyword = ref('');
  const languageFilter = ref<string>('all');
  const pageSizeOptions = [10, 20, 50];
  const pageSize = ref(20);
  const currentPage = ref(1);
  const sortState = reactive<{ prop: string; order: 'ascending' | 'descending' | null }>({
    prop: 'updated_at',
    order: 'descending',
  });

  const filteredDirectories = computed(() =>
    directories.value.filter(
      (dir) => !BLOCKED_DIRECTORY_TITLES.includes((dir.title || '').trim())
    )
  );
  const availableDirectories = computed(() =>
    filteredDirectories.value.length ? filteredDirectories.value : directories.value
  );

  const directoryMap = computed<Record<string, DirectoryPreset>>(() => {
    const map: Record<string, DirectoryPreset> = {};
    availableDirectories.value.forEach((dir) => {
      map[dir.key] = dir;
    });
    return map;
  });

  const directoryGroups = computed<DirectoryGroup[]>(() =>
    availableDirectories.value.map((preset) => ({
      ...preset,
      repos: repositories.value.filter(
        (repo) => matchDirectoryKey(repo, availableDirectories.value) === preset.key
      ),
    }))
  );

  const currentDirectory = computed<DirectoryGroup | null>(() => {
    const groups = directoryGroups.value;
    if (!groups.length || !selectedDirectoryKey.value) return null;
    return groups.find((group) => group.key === selectedDirectoryKey.value) ?? null;
  });

  const currentDirectoryName = computed(() => {
    if (!currentDirectory.value) return '脚本目录';
    const title = currentDirectory.value.title;
    return title.includes('用户自定义目录') ? '脚本目录' : title;
  });

  const currentRepos = computed(() => currentDirectory.value?.repos ?? []);
  const filteredCurrentRepos = computed(() => {
    const keyword = repoKeyword.value.trim().toLowerCase();
    const langFilter = languageFilter.value;
    return currentRepos.value
      .filter((repo: ScriptRepository) => {
        if (langFilter === 'all') return true;
        return (repo.language || '').toLowerCase() === langFilter;
      })
      .filter((repo: ScriptRepository) => {
        if (!keyword) return true;
        return (
          repo.name.toLowerCase().includes(keyword) ||
          (repo.description || '').toLowerCase().includes(keyword) ||
          repo.tags.some((tag: string) => tag.toLowerCase().includes(keyword))
        );
      });
  });

  const sortedRepos = computed(() => {
    const list = [...filteredCurrentRepos.value];
    if (!sortState.prop || !sortState.order) return list;
    return list.sort((a: any, b: any) => {
      const prop = sortState.prop as keyof ScriptRepository;
      const va = a[prop];
      const vb = b[prop];
      if (va === vb) return 0;
      if (va === undefined || va === null) return 1;
      if (vb === undefined || vb === null) return -1;
      const result = va > vb ? 1 : -1;
      return sortState.order === 'ascending' ? result : -result;
    });
  });

  const paginatedRepos = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return sortedRepos.value.slice(start, start + pageSize.value);
  });

  const directoryOptions = computed(() =>
    availableDirectories.value.map((dir) => ({ key: dir.key, title: dir.title }))
  );

  const resolveDirectoryIcon = (key: string): Component =>
    DIRECTORY_ICON_MAP[key] || Document;

  const ensureRepositorySelection = () => {
    const repos = currentRepos.value;
    if (!repos.length) {
      selectedRepository.value = null;
      return;
    }
    if (
      !selectedRepository.value ||
      !repos.some((repo: ScriptRepository) => repo.id === selectedRepository.value?.id)
    ) {
      selectedRepository.value = repos[0];
    }
  };

  const syncDirectorySelection = () => {
    if (!availableDirectories.value.length) {
      selectedDirectoryKey.value = '';
      return;
    }
    const param =
      typeof route.params.directoryKey === 'string' ? route.params.directoryKey : '';
    if (param && directoryMap.value[param]) {
      selectedDirectoryKey.value = param;
      return;
    }
    const fallbackKey = availableDirectories.value[0]?.key || '';
    selectedDirectoryKey.value = fallbackKey;
    if (param !== fallbackKey) {
      router.replace({ name: 'code-repository', params: { directoryKey: fallbackKey } });
    }
  };

  const navigateToDirectory = (key: string) => {
    if (!key) return;
    detailRepository.value = null;
    selectedRepository.value = null;
    selectedDirectoryKey.value = key;
    const currentParam =
      typeof route.params.directoryKey === 'string' ? route.params.directoryKey : '';
    const query = { ...route.query };
    delete (query as any).repoId;
    if (currentParam !== key) {
      router.push({ name: 'code-repository', params: { directoryKey: key }, query });
    } else if (selectedDirectoryKey.value !== key) {
      selectedDirectoryKey.value = key;
      router.replace({ name: 'code-repository', params: { directoryKey: key }, query });
    } else {
      router.replace({ name: 'code-repository', params: { directoryKey: key }, query });
    }
  };

  const handleDirectorySelect = (key: string) => {
    navigateToDirectory(key);
  };

  const resolveActiveDirectoryForForm = () => {
    if (selectedDirectoryKey.value) {
      return selectedDirectoryKey.value;
    }
    return directoryOptions.value[0]?.key || '';
  };

  const handlePageChange = (page: number) => {
    currentPage.value = page;
  };

  const handlePageSizeChange = (size: number) => {
    pageSize.value = size;
    currentPage.value = 1;
  };

  const handleSortChange = ({
    prop,
    order,
  }: {
    prop: string;
    order: 'ascending' | 'descending' | null;
  }) => {
    sortState.prop = prop;
    sortState.order = order;
  };

  const rowClassName = ({ row }: { row: ScriptRepository }) => {
    if (row.id === selectedRepository.value?.id) {
      return 'is-selected-row';
    }
    return '';
  };

  const formatTime = formatRepositoryTime;

  watch(
    () => filteredCurrentRepos.value.length,
    () => {
      currentPage.value = 1;
    }
  );

  watch(
    () => selectedDirectoryKey.value,
    () => {
      const repos = currentRepos.value;
      selectedRepository.value = repos[0] ?? null;
      if (
        detailRepository.value &&
        matchDirectoryKey(detailRepository.value, availableDirectories.value) !==
          selectedDirectoryKey.value
      ) {
        detailRepository.value = null;
      }
    }
  );

  watch(
    () => [availableDirectories.value.map((dir) => dir.key).join(','), route.params.directoryKey],
    () => {
      syncDirectorySelection();
      ensureRepositorySelection();
    },
    { immediate: true }
  );

  return {
    availableDirectories,
    currentPage,
    currentDirectory,
    currentDirectoryName,
    currentRepos,
    directoryGroups,
    directoryMap,
    directoryOptions,
    filteredCurrentRepos,
    formatTime,
    handleDirectorySelect,
    handlePageChange,
    handlePageSizeChange,
    handleSortChange,
    languageFilter,
    pageSize,
    pageSizeOptions,
    paginatedRepos,
    repoKeyword,
    resolveActiveDirectoryForForm,
    resolveDirectoryIcon,
    rowClassName,
    selectedDirectoryKey,
    sidebarCollapsed,
    sidebarWidth,
    sortState,
    syncDirectorySelection,
    ensureRepositorySelection,
    navigateToDirectory,
  };
}
