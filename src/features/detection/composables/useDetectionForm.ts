/**
 * 检测表单通用逻辑
 */
import { computed, reactive, ref } from 'vue';
import { validateUrl, validateDomain } from '../mappers/detectionUtils';

export interface UseDetectionFormOptions {
  initialTarget?: string;
  initialProtocol?: string;
  requireProtocol?: boolean;
  validateTarget?: (target: string, requireProtocol?: boolean) => { valid: boolean; message?: string };
}

export function useDetectionForm(options: UseDetectionFormOptions = {}) {
  const {
    initialTarget = '',
    initialProtocol = 'HTTPS',
    requireProtocol = true,
    validateTarget = requireProtocol ? validateUrl : validateDomain
  } = options;

  // 表单数据
  const form = reactive({
    target: initialTarget,
    protocol: initialProtocol
  });

  // 提交状态
  const submitting = ref(false);
  const submissionError = ref<string | null>(null);

  // 验证逻辑
  const targetValidation = computed(() => {
    if (!form.target.trim()) {
      return { valid: false, message: '请输入目标地址' };
    }
    return validateTarget(form.target, requireProtocol);
  });

  const isTargetValid = computed(() => targetValidation.value.valid);
  const targetErrorMessage = computed(() => targetValidation.value.message);

  // 重置错误
  const clearError = () => {
    submissionError.value = null;
  };

  // 设置错误
  const setError = (error: string | Error) => {
    submissionError.value = error instanceof Error ? error.message : error;
  };

  // 重置表单
  const resetForm = () => {
    form.target = initialTarget;
    form.protocol = initialProtocol;
    submitting.value = false;
    submissionError.value = null;
  };

  return {
    form,
    submitting,
    submissionError,
    isTargetValid,
    targetErrorMessage,
    clearError,
    setError,
    resetForm
  };
}
