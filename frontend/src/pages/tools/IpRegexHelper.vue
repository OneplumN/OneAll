<template>
  <RepositoryPageShell root-title="运维工具" section-title="IP 正则助手">
    <template #actions>
      <el-button class="toolbar-button" @click="fillSample">填入示例</el-button>
      <el-button class="toolbar-button" @click="clearAll">清空</el-button>
    </template>

    <div class="helper-grid">
      <el-card shadow="never" class="helper-card">
        <template #header>
          <div class="panel-head">
            <div>
              <div class="panel-title">IP → 正则</div>
              <div class="panel-desc">每行一个 IPv4；会自动去重并忽略无效项。</div>
            </div>
            <div class="panel-head__right">
              <span class="badge">输入 {{ ipLineCount }} 行</span>
              <span class="badge badge--muted">匹配 {{ matchedCount }} 个</span>
            </div>
          </div>
        </template>

        <el-input
          v-model="ipInput"
          type="textarea"
          :rows="8"
          placeholder="每行一个 IP，示例：\n192.168.1.10\n192.168.1.11"
        />
        <div class="panel-actions">
          <el-button type="primary" :loading="converting" @click="handleGenerate">生成正则</el-button>
          <el-button text @click="clearIps">清空 IP</el-button>
          <span class="hint">最多支持 500 行</span>
        </div>
        <el-alert v-if="invalidIps.length" type="warning" show-icon :closable="false" class="mt-12">
          以下 {{ invalidIps.length }} 个 IP 校验失败：{{ invalidIps.join(', ') }}
        </el-alert>

        <el-divider class="panel-divider" />

        <div class="panel-head">
          <div>
            <div class="panel-title panel-title--sub">正则输出</div>
            <div class="panel-desc">用于精确匹配这批 IP 的正则表达式。</div>
          </div>
          <div class="panel-head__right">
            <el-button text :icon="DocumentCopy" :disabled="!regexOutput" @click="copyText(regexOutput)">复制</el-button>
            <el-button text :disabled="!regexOutput" @click="useGeneratedRegex">用于反推</el-button>
          </div>
        </div>
        <el-input v-model="regexOutput" type="textarea" :rows="8" readonly placeholder="生成的正则会显示在这里" />
      </el-card>

      <el-card shadow="never" class="helper-card">
        <template #header>
          <div class="panel-head">
            <div>
              <div class="panel-title">正则 → IP</div>
              <div class="panel-desc">输入已有的 IP 匹配正则，确认覆盖范围。</div>
            </div>
            <div class="panel-head__right">
              <span class="limit-label">最大解析条数</span>
              <el-input-number v-model="reverseLimit" size="small" :min="1" :max="2000" />
            </div>
          </div>
        </template>

        <el-input v-model="regexInput" type="textarea" :rows="8" placeholder="(192\\.168\\.1\\.1|192\\.168\\.1\\.2)" />
        <div class="panel-actions">
          <el-button type="primary" :loading="expanding" @click="handleReverse">解析 IP</el-button>
          <el-button text @click="useGeneratedRegex">使用左侧正则</el-button>
          <el-button text @click="regexInput = ''">清空正则</el-button>
        </div>

        <el-divider class="panel-divider" />

        <div class="panel-head">
          <div>
            <div class="panel-title panel-title--sub">解析结果</div>
            <div class="panel-desc">每行一个 IP，可直接复制用于白名单等配置。</div>
          </div>
          <div class="panel-head__right">
            <el-button text :icon="DocumentCopy" :disabled="!reverseResult.length" @click="copyText(reverseResult.join('\n'))">
              复制
            </el-button>
            <span class="badge badge--muted">共 {{ reverseResult.length }} 个</span>
          </div>
        </div>
        <el-input
          :model-value="reverseResult.join('\n')"
          type="textarea"
          :rows="8"
          readonly
          placeholder="解析结果将显示在此处"
        />
      </el-card>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { DocumentCopy } from '@element-plus/icons-vue';

import { compileIpRegex, expandRegexToIps } from '@/services/toolsApi';
import { usePageTitle } from '@/composables/usePageTitle';
import RepositoryPageShell from '@/components/RepositoryPageShell.vue';

const ipInput = ref('');
const regexOutput = ref('');
const matchedCount = ref(0);
const invalidIps = ref<string[]>([]);
const regexInput = ref('');
const reverseLimit = ref(500);
const reverseResult = ref<string[]>([]);
const converting = ref(false);
const expanding = ref(false);
const ipLineCount = computed(() => ipInput.value.split('\n').filter((line) => line.trim().length > 0).length);

const sampleIps = ['192.168.1.10', '192.168.1.11', '192.168.1.12', '10.0.0.5', '10.0.0.6'];

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
    const detail = error?.response?.data?.detail || error?.response?.data?.ips || '生成失败，请检查输入';
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
    const detail = error?.response?.data?.pattern || error?.response?.data?.detail || '解析失败，请检查正则';
    ElMessage.error(detail);
  } finally {
    expanding.value = false;
  }
};

const copyText = async (text: string) => {
  if (!text.trim()) return;
  const performFallbackCopy = () => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    if (!success) {
      throw new Error('fallback copy failed');
    }
  };

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      performFallbackCopy();
    }
    ElMessage.success('已复制到剪贴板');
  } catch (error) {
    try {
      performFallbackCopy();
      ElMessage.success('已复制到剪贴板');
    } catch {
      ElMessage.error('复制失败，请手动选择内容');
    }
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
</script>

<style scoped>
.helper-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
  min-height: 0;
}

.helper-card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-light);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
}

.helper-card :deep(.el-card__header) {
  padding: 12px;
}

.helper-card :deep(.el-card__body) {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.badge {
  background: #f0f5ff;
  color: #3b82f6;
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 12px;
  white-space: nowrap;
}

.badge--muted {
  background: var(--oa-bg-panel);
  color: var(--oa-text-secondary);
  border: 1px solid var(--oa-border-light);
}

.panel-divider {
  margin: 6px 0 2px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-head__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.panel-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.panel-title--sub {
  font-size: 13px;
}

.panel-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mt-12 {
  margin-top: 12px;
}

.limit-label {
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.hint {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

@media (max-width: 960px) {
  .helper-grid {
    grid-template-columns: 1fr;
  }
}
</style>
