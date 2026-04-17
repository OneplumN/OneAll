import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

import { usePageTitle } from '@/composables/usePageTitle';
import { copyTextWithFallback } from '@/shared/utils/clipboard';
import { compileIpRegex, expandRegexToIps } from '@/features/tools/api/toolsApi';

const sampleIps = ['192.168.1.10', '192.168.1.11', '192.168.1.12', '10.0.0.5', '10.0.0.6'];

export function useIpRegexHelperPage() {
  const ipInput = ref('');
  const regexOutput = ref('');
  const matchedCount = ref(0);
  const invalidIps = ref<string[]>([]);
  const regexInput = ref('');
  const reverseLimit = ref(500);
  const reverseResult = ref<string[]>([]);
  const converting = ref(false);
  const expanding = ref(false);

  const ipLineCount = computed(() =>
    ipInput.value.split('\n').filter((line) => line.trim().length > 0).length
  );

  usePageTitle('IP 正则助手');

  const handleGenerate = async () => {
    const ips = ipInput.value
      .split('\n')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
    if (!ips.length) {
      ElMessage.warning('请至少输入一个 IP 地址');
      return;
    }
    converting.value = true;
    try {
      const { regex, matched_count, invalid_ips } = await compileIpRegex(ips);
      regexOutput.value = regex;
      matchedCount.value = matched_count;
      invalidIps.value = invalid_ips || [];
      if (invalid_ips.length) {
        ElMessage.warning('存在格式不正确的 IP，已自动忽略');
      } else {
        ElMessage.success('已生成正则表达式');
      }
    } catch (error: any) {
      regexOutput.value = '';
      matchedCount.value = 0;
      invalidIps.value = [];
      const detail =
        error?.response?.data?.detail || error?.response?.data?.ips || '生成失败，请检查输入';
      ElMessage.error(Array.isArray(detail) ? detail.join(', ') : detail);
    } finally {
      converting.value = false;
    }
  };

  const handleReverse = async () => {
    if (!regexInput.value.trim()) {
      ElMessage.warning('请先输入正则表达式');
      return;
    }
    expanding.value = true;
    try {
      const { ips } = await expandRegexToIps(regexInput.value.trim(), reverseLimit.value);
      reverseResult.value = ips;
      ElMessage.success(`已解析 ${ips.length} 个 IP`);
    } catch (error: any) {
      reverseResult.value = [];
      const detail =
        error?.response?.data?.pattern || error?.response?.data?.detail || '解析失败，请检查正则';
      ElMessage.error(detail);
    } finally {
      expanding.value = false;
    }
  };

  const copyText = async (text: string) => {
    if (!text.trim()) return;
    try {
      await copyTextWithFallback(text);
      ElMessage.success('已复制到剪贴板');
    } catch {
      ElMessage.error('复制失败，请手动选择内容');
    }
  };

  const useGeneratedRegex = () => {
    if (!regexOutput.value.trim()) {
      ElMessage.info('请先在左侧生成正则表达式');
      return;
    }
    regexInput.value = regexOutput.value;
  };

  const fillSample = () => {
    ipInput.value = sampleIps.join('\n');
  };

  const clearIps = () => {
    ipInput.value = '';
    regexOutput.value = '';
    matchedCount.value = 0;
    invalidIps.value = [];
  };

  const clearAll = () => {
    clearIps();
    regexInput.value = '';
    reverseResult.value = [];
  };

  return {
    clearAll,
    clearIps,
    converting,
    copyText,
    expanding,
    fillSample,
    handleGenerate,
    handleReverse,
    invalidIps,
    ipInput,
    ipLineCount,
    matchedCount,
    regexInput,
    regexOutput,
    reverseLimit,
    reverseResult,
    useGeneratedRegex,
  };
}
