import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import type { RouteLocationNormalizedLoaded, Router } from 'vue-router';

import {
  createRepository,
  deleteRepository,
  listRepositories,
  updateRepository,
  type CreateRepositoryPayload,
  type ScriptRepository,
  type UpdateRepositoryPayload,
} from '@/features/tools/api/codeRepositoryApi';
import { cleanTags, matchDirectoryKey } from '@/features/tools/utils/repositoryPageHelpers';
import type { DirectoryPreset } from '@/features/tools/stores/codeDirectories';

type BrowserBindings = {
  availableDirectories: ComputedRef<DirectoryPreset[]>;
  ensureRepositorySelection: () => void;
  navigateToDirectory: (key: string) => void;
  resolveActiveDirectoryForForm: () => string;
  selectedDirectoryKey: Ref<string>;
};

export function useCodeRepositoryPersistence(options: {
  route: RouteLocationNormalizedLoaded;
  router: Router;
  canCreate: ComputedRef<boolean>;
  canManage: ComputedRef<boolean>;
}) {
  const { route, router, canCreate, canManage } = options;

  const repositories = ref<ScriptRepository[]>([]);
  const loading = reactive({
    repositories: false,
    creating: false,
    updating: false,
  });

  const createFormRef = ref<FormInstance>();
  const selectedRepository = ref<ScriptRepository | null>(null);
  const detailRepository = ref<ScriptRepository | null>(null);
  const showCreateMode = ref(false);

  const createForm = reactive<CreateRepositoryPayload>({
    name: '',
    language: '',
    tags: [],
    description: '',
    content: '',
    directory: '',
  });

  const createRules: FormRules<CreateRepositoryPayload> = {
    name: [{ required: true, message: '请输入脚本名称', trigger: 'blur' }],
    language: [{ required: true, message: '请选择脚本语言', trigger: 'change' }],
    tags: [
      { type: 'array', required: true, message: '至少添加一个标签', trigger: 'change' },
    ],
    directory: [{ required: true, message: '请选择目录', trigger: 'change' }],
    content: [{ required: true, message: '请填写初始脚本内容', trigger: 'blur' }],
  };

  const detailDirty = reactive({
    meta: false,
    code: false,
  });

  let browserBindings: BrowserBindings | null = null;

  const bindBrowser = (bindings: BrowserBindings) => {
    browserBindings = bindings;
  };

  const requireBrowserBindings = () => {
    if (!browserBindings) {
      throw new Error('CodeRepository browser bindings are not initialized');
    }
    return browserBindings;
  };

  const detailMode = computed(() => !!detailRepository.value);
  const createMode = computed(() => showCreateMode.value);

  const resetCreateForm = () => {
    const { resolveActiveDirectoryForForm } = requireBrowserBindings();
    createForm.name = '';
    createForm.language = '';
    createForm.tags = [];
    createForm.description = '';
    createForm.content = '';
    createForm.directory = resolveActiveDirectoryForForm();
  };

  const openRepoFromQuery = () => {
    const repoId = typeof route.query.repoId === 'string' ? route.query.repoId : '';
    if (!repoId) return;
    if (createMode.value) return;
    const target = repositories.value.find((repo) => repo.id === repoId);
    if (target && detailRepository.value?.id !== repoId) {
      void handleView(target);
    }
  };

  const loadRepositories = async () => {
    loading.repositories = true;
    try {
      const data = await listRepositories();
      repositories.value = data.map((repo) => ({ ...repo, tags: cleanTags(repo.tags) }));
    } catch (error) {
      console.error('脚本加载失败', error);
      repositories.value = [];
      ElMessage.error('脚本加载失败，请稍后重试');
    } finally {
      loading.repositories = false;
      const { ensureRepositorySelection } = requireBrowserBindings();
      ensureRepositorySelection();
      openRepoFromQuery();
    }
  };

  const handleView = async (repo: ScriptRepository) => {
    const { selectedDirectoryKey } = requireBrowserBindings();
    selectedRepository.value = repo;
    detailRepository.value = repo;
    detailDirty.meta = false;
    detailDirty.code = false;
    await router.replace({
      name: 'code-repository',
      params: { directoryKey: selectedDirectoryKey.value || '' },
      query: { ...route.query, repoId: repo.id },
    });
  };

  const handleEdit = (repo: ScriptRepository) => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    showCreateMode.value = false;
    void handleView(repo);
  };

  const handleDelete = async (repo: ScriptRepository) => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    try {
      await ElMessageBox.confirm(`确定删除脚本「${repo.name}」？该操作不可恢复。`, '删除确认', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      });
      await deleteRepository(repo.id);
      repositories.value = repositories.value.filter((item) => item.id !== repo.id);
      if (detailRepository.value?.id === repo.id) {
        detailRepository.value = null;
      }
      if (selectedRepository.value?.id === repo.id) {
        selectedRepository.value = null;
      }
      const { ensureRepositorySelection } = requireBrowserBindings();
      ensureRepositorySelection();
      ElMessage.success('脚本已删除');
    } catch (error) {
      if (error !== 'cancel') {
        console.error('Failed to delete repository.', error);
        ElMessage.error('删除脚本失败，请稍后重试');
      }
    }
  };

  const handleSaveAll = async () => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    if (!detailRepository.value) return;
    loading.updating = true;
    try {
      const { availableDirectories } = requireBrowserBindings();
      const payload: UpdateRepositoryPayload = {
        name: detailRepository.value.name,
        language: detailRepository.value.language,
        tags: cleanTags(detailRepository.value.tags),
        description: detailRepository.value.description,
        directory:
          (detailRepository.value as any).directory ||
          matchDirectoryKey(detailRepository.value, availableDirectories.value),
        content: detailRepository.value.content || '',
      };
      const updated = await updateRepository(detailRepository.value.id, payload);
      const sanitized = { ...updated, directory: payload.directory, tags: cleanTags(updated.tags) };
      detailRepository.value = sanitized;
      repositories.value = repositories.value.map((repo) =>
        repo.id === sanitized.id ? sanitized : repo
      );
      ElMessage.success('已保存');
      detailDirty.meta = false;
      detailDirty.code = false;
    } catch (error) {
      console.error('保存失败', error);
      ElMessage.error('保存失败，请稍后重试');
    } finally {
      loading.updating = false;
    }
  };

  const openCreateDialog = () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    const { directoryOptions, resolveActiveDirectoryForForm, selectedDirectoryKey } = (() => {
      const bindings = requireBrowserBindings();
      return {
        directoryOptions: bindings.availableDirectories.value.map((dir) => ({
          key: dir.key,
          title: dir.title,
        })),
        resolveActiveDirectoryForForm: bindings.resolveActiveDirectoryForForm,
        selectedDirectoryKey: bindings.selectedDirectoryKey,
      };
    })();
    if (!directoryOptions.length) {
      ElMessage.warning('请先创建目录');
      return;
    }
    createForm.directory = resolveActiveDirectoryForForm();
    resetCreateForm();
    detailRepository.value = null;
    selectedRepository.value = null;
    showCreateMode.value = true;
    const query = { ...route.query };
    delete (query as any).repoId;
    void router.replace({
      name: 'code-repository',
      params: { directoryKey: selectedDirectoryKey.value || '' },
      query,
    });
  };

  const submitCreate = async () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    if (!createFormRef.value) return;
    await createFormRef.value.validate(async (valid) => {
      if (!valid) return;
      loading.creating = true;
      try {
        const repo = await createRepository({ ...createForm, tags: cleanTags(createForm.tags) });
        const { availableDirectories, navigateToDirectory, selectedDirectoryKey } =
          requireBrowserBindings();
        const sanitized = { ...repo, directory: createForm.directory, tags: cleanTags(repo.tags) };
        repositories.value = [sanitized, ...repositories.value];
        detailRepository.value = sanitized;
        selectedRepository.value = sanitized;
        showCreateMode.value = false;
        detailDirty.meta = false;
        detailDirty.code = false;
        ElMessage.success('脚本已创建');
        resetCreateForm();
        navigateToDirectory(matchDirectoryKey(sanitized, availableDirectories.value));
        await router.replace({
          name: 'code-repository',
          params: { directoryKey: selectedDirectoryKey.value || '' },
          query: { ...route.query, repoId: sanitized.id },
        });
      } catch (error) {
        console.error('Failed to create repository.', error);
        ElMessage.error('创建脚本失败，请稍后重试');
      } finally {
        loading.creating = false;
      }
    });
  };

  const exitDetailMode = () => {
    const { selectedDirectoryKey } = requireBrowserBindings();
    detailRepository.value = null;
    const rest = { ...route.query };
    delete rest.repoId;
    void router.replace({
      name: 'code-repository',
      params: { directoryKey: selectedDirectoryKey.value || '' },
      query: rest,
    });
  };

  const markDetailDirty = () => {
    detailDirty.meta = true;
  };

  const handleCreateInline = async () => {
    await submitCreate();
  };

  const exitCreateMode = () => {
    const { selectedDirectoryKey } = requireBrowserBindings();
    const hasInput =
      createForm.name ||
      createForm.language ||
      (createForm.tags && createForm.tags.length) ||
      createForm.description ||
      createForm.content;
    if (hasInput || detailDirty.meta || detailDirty.code) {
      ElMessageBox.confirm('当前新建内容尚未保存，确认返回列表？', '确认退出', {
        type: 'warning',
        confirmButtonText: '确认',
        cancelButtonText: '取消',
      })
        .then(() => {
          showCreateMode.value = false;
          resetCreateForm();
          detailDirty.meta = false;
          detailDirty.code = false;
          void router.replace({
            name: 'code-repository',
            params: { directoryKey: selectedDirectoryKey.value || '' },
            query: { ...route.query, repoId: undefined },
          });
        })
        .catch(() => {});
      return;
    }

    showCreateMode.value = false;
    resetCreateForm();
    detailDirty.meta = false;
    detailDirty.code = false;
    void router.replace({
      name: 'code-repository',
      params: { directoryKey: selectedDirectoryKey.value || '' },
      query: { ...route.query, repoId: undefined },
    });
  };

  return {
    bindBrowser,
    createForm,
    createFormRef,
    createMode,
    createRules,
    detailDirty,
    detailMode,
    detailRepository,
    exitCreateMode,
    exitDetailMode,
    handleCreateInline,
    handleDelete,
    handleEdit,
    handleSaveAll,
    handleView,
    loadRepositories,
    loading,
    markDetailDirty,
    openCreateDialog,
    openRepoFromQuery,
    repositories,
    selectedRepository,
    showCreateMode,
  };
}
