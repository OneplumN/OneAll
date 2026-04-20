import dayjs from 'dayjs';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { computed, onMounted, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { usePageTitle } from '@/composables/usePageTitle';
import { useSessionStore } from '@/app/stores/session';
import {
  createTool,
  executeTool,
  listTools,
  type CreateToolPayload,
  type ToolDefinition,
  type ToolExecutionResult,
} from '@/features/tools/api/toolsApi';

export function useToolLibraryPage() {
  const sessionStore = useSessionStore();
  const canCreate = computed(() => sessionStore.hasPermission('tools.library.create'));
  const canManage = computed(() => sessionStore.hasPermission('tools.library.manage'));
  const canExecute = computed(() => sessionStore.hasPermission('tools.library.execute'));

  const tools = ref<ToolDefinition[]>([]);
  const loading = reactive({
    table: false,
    creating: false,
    executing: false,
  });

  const filters = reactive({
    keyword: '',
    category: '',
    tag: '',
  });

  const createDialogVisible = ref(false);
  const detailsDrawerVisible = ref(false);
  const executionDrawerVisible = ref(false);
  const selectedTool = ref<ToolDefinition | null>(null);
  const executingTool = ref<ToolDefinition | null>(null);
  const executionResult = ref<ToolExecutionResult | null>(null);

  const createForm = reactive<CreateToolPayload>({
    name: '',
    category: '',
    tags: [],
    description: '',
    script_id: '',
  });

  const createFormRef = ref<FormInstance>();

  const createRules: FormRules<CreateToolPayload> = {
    name: [{ required: true, message: '请输入工具名称', trigger: 'blur' }],
    category: [{ required: true, message: '请选择类别', trigger: 'blur' }],
    tags: [
      {
        type: 'array',
        required: true,
        message: '至少添加一个标签',
        trigger: 'change',
      },
    ],
  };

  const categoryOptions = computed(() => {
    const items = new Set<string>();
    tools.value.forEach((tool) => {
      if (tool.category) items.add(tool.category);
    });
    return Array.from(items);
  });

  const tagOptions = computed(() => {
    const items = new Set<string>();
    tools.value.forEach((tool) => {
      tool.tags?.forEach((tag) => items.add(tag));
    });
    return Array.from(items);
  });

  const filteredTools = computed(() =>
    tools.value.filter((tool) => {
      const matchKeyword =
        !filters.keyword ||
        tool.name.toLowerCase().includes(filters.keyword.toLowerCase()) ||
        (tool.description || '').toLowerCase().includes(filters.keyword.toLowerCase());

      const matchCategory = !filters.category || tool.category === filters.category;
      const matchTag = !filters.tag || tool.tags?.includes(filters.tag);

      return matchKeyword && matchCategory && matchTag;
    })
  );

  const { t } = useI18n();
  usePageTitle('tools.libraryTitle');

  const loadTools = async () => {
    loading.table = true;
    try {
      tools.value = await listTools();
    } catch (error) {
      console.warn('Failed to load tools.', error);
      ElMessage.error('加载工具列表失败，请稍后重试');
    } finally {
      loading.table = false;
    }
  };

  const openCreateDialog = () => {
    if (!canCreate.value) {
      ElMessage.warning('暂无新增权限');
      return;
    }
    createDialogVisible.value = true;
  };

  const resetCreateForm = () => {
    createForm.name = '';
    createForm.category = '';
    createForm.tags = [];
    createForm.description = '';
    createForm.script_id = '';
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
        const tool = await createTool(createForm);
        tools.value = [tool, ...tools.value];
        ElMessage.success(t('tools.toolCreated'));
        createDialogVisible.value = false;
        resetCreateForm();
      } catch (error) {
        console.warn('Failed to create tool.', error);
        ElMessage.error('创建失败，请检查信息或稍后重试');
      } finally {
        loading.creating = false;
      }
    });
  };

  const openDetails = (tool: ToolDefinition) => {
    selectedTool.value = tool;
    detailsDrawerVisible.value = true;
  };

  const handleExecute = async (tool: ToolDefinition) => {
    if (!canExecute.value) {
      ElMessage.warning('暂无执行权限');
      return;
    }
    executingTool.value = tool;
    executionDrawerVisible.value = true;
    loading.executing = true;
    executionResult.value = null;
    try {
      const result = await executeTool(tool.id, {});
      executionResult.value = result;
      ElMessage.success(t('tools.toolExecuteTriggered'));
    } catch (error) {
      console.warn('Failed to execute tool.', error);
      ElMessage.error('触发执行失败，请稍后重试');
    } finally {
      loading.executing = false;
    }
  };

  const formatTime = (value?: string) => {
    if (!value) return '未记录';
    return dayjs(value).format('YYYY-MM-DD HH:mm');
  };

  onMounted(() => {
    void loadTools();
  });

  return {
    canCreate,
    canExecute,
    canManage,
    categoryOptions,
    createDialogVisible,
    createForm,
    createFormRef,
    createRules,
    detailsDrawerVisible,
    executingTool,
    executionDrawerVisible,
    executionResult,
    filteredTools,
    filters,
    formatTime,
    handleExecute,
    loadTools,
    loading,
    openCreateDialog,
    openDetails,
    selectedTool,
    submitCreate,
    t,
    tagOptions,
  };
}
