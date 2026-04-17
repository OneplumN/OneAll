import { reactive, ref, type Ref } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';

import {
  createCodeDirectory,
  deleteCodeDirectory,
  updateCodeDirectory,
} from '@/features/tools/api/codeRepositoryApi';
import type { DirectoryPreset } from '@/features/tools/stores/codeDirectories';
import { parseKeywords } from '@/features/tools/utils/repositoryPageHelpers';

export function useDirectoryManager(options: {
  canManage: Ref<boolean>;
  codeDirectoryStore: { fetchDirectories: () => Promise<unknown> };
  syncDirectorySelection: () => void;
}) {
  const { canManage, codeDirectoryStore, syncDirectorySelection } = options;

  const directoryManagerVisible = ref(false);
  const directoryFormRef = ref<FormInstance>();
  const directoryForm = reactive<{ title: string; keywordsInput: string }>({
    title: '',
    keywordsInput: '',
  });
  const editingDirectoryKey = ref<string | null>(null);
  const directoryManaging = ref(false);

  const directoryFormRules: FormRules = {
    title: [{ required: true, message: '请输入目录名称', trigger: 'blur' }],
  };

  const resetDirectoryForm = () => {
    directoryForm.title = '';
    directoryForm.keywordsInput = '';
    editingDirectoryKey.value = null;
  };

  const openDirectoryManager = () => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    resetDirectoryForm();
    directoryManagerVisible.value = true;
  };

  const startEditDirectory = (dir: DirectoryPreset) => {
    directoryManagerVisible.value = true;
    editingDirectoryKey.value = dir.key;
    directoryForm.title = dir.title || '';
    directoryForm.keywordsInput = (dir.keywords || []).join(', ');
  };

  const submitDirectorySave = async () => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    if (!directoryFormRef.value) return;
    await directoryFormRef.value.validate(async (valid) => {
      if (!valid) return;
      directoryManaging.value = true;
      const payload = {
        title: directoryForm.title,
        keywords: parseKeywords(directoryForm.keywordsInput),
      };
      try {
        if (editingDirectoryKey.value) {
          await updateCodeDirectory(editingDirectoryKey.value, payload);
          ElMessage.success('目录已更新');
        } else {
          await createCodeDirectory(payload);
          ElMessage.success('目录已创建');
        }
        await codeDirectoryStore.fetchDirectories();
        directoryManagerVisible.value = false;
        resetDirectoryForm();
        syncDirectorySelection();
      } catch (error) {
        console.error('目录保存失败', error);
        ElMessage.error('目录保存失败，请稍后重试');
      } finally {
        directoryManaging.value = false;
      }
    });
  };

  const handleDeleteDirectory = async (dir: DirectoryPreset) => {
    if (!canManage.value) {
      ElMessage.warning('暂无管理权限');
      return;
    }
    if (dir.builtin) {
      ElMessage.warning('内置目录不可删除');
      return;
    }
    try {
      await ElMessageBox.confirm(
        `确定删除目录「${dir.title}」？该操作不可恢复。`,
        '删除确认',
        {
          type: 'warning',
          confirmButtonText: '删除',
          cancelButtonText: '取消',
        }
      );
      directoryManaging.value = true;
      await deleteCodeDirectory(dir.key);
      await codeDirectoryStore.fetchDirectories();
      syncDirectorySelection();
      ElMessage.success('目录已删除');
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除目录失败', error);
        ElMessage.error('目录保存失败，请稍后重试');
      }
    } finally {
      directoryManaging.value = false;
    }
  };

  return {
    directoryManagerVisible,
    directoryForm,
    directoryFormRef,
    directoryFormRules,
    directoryManaging,
    editingDirectoryKey,
    handleDeleteDirectory,
    openDirectoryManager,
    resetDirectoryForm,
    startEditDirectory,
    submitDirectorySave,
  };
}
