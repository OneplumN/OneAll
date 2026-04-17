<template>
  <el-form
    label-width="140px"
    :disabled="disabled"
    class="channel-form settings-detail-form"
  >
    <div class="oa-detail-stack">
      <section class="channel-form-section settings-detail-section">
        <div class="channel-form-section__head settings-detail-section__head">
          <h3 class="oa-section-title">
            模板设置
          </h3>
          <p class="oa-section-subtitle">
            为当前通知渠道选择发送模板，未单独指定时将使用默认模板。
          </p>
        </div>

        <el-form-item label="通知模板">
          <div class="template-select">
            <el-select
              v-model="formModel.template_id"
              placeholder="使用默认模板"
              clearable
              :loading="templateLoading"
              :disabled="templateLoading"
              class="oa-input-xl"
            >
              <el-option
                v-for="tpl in templatesForChannel"
                :key="tpl.id"
                :label="tpl.name"
                :value="tpl.id"
              >
                <div class="template-option">
                  <span>{{ tpl.name }}</span>
                  <el-tag
                    v-if="tpl.is_default"
                    size="small"
                    type="success"
                    effect="plain"
                  >
                    默认
                  </el-tag>
                </div>
                <small>{{ tpl.updated_at && formatDate(tpl.updated_at) }}</small>
              </el-option>
            </el-select>
            <el-button
              text
              size="small"
              @click="emit('goTemplates')"
            >
              去通知模板
            </el-button>
            <p class="form-tip">
              未选择时将使用该通道默认模板。
            </p>
          </div>
        </el-form-item>
      </section>

      <section class="channel-form-section settings-detail-section">
        <div class="channel-form-section__head settings-detail-section__head">
          <h3 class="oa-section-title">
            {{ isScriptChannel ? '脚本配置' : '通道配置' }}
          </h3>
          <p class="oa-section-subtitle">
            {{ isScriptChannel ? '选择脚本仓库与版本，用于执行该通知渠道。' : '维护当前渠道的连接参数和发送配置。' }}
          </p>
        </div>

        <template v-if="isScriptChannel">
          <el-form-item label="脚本仓库">
            <div class="script-selection oa-soft-panel oa-soft-panel--dashed">
              <div
                v-if="scriptRepository"
                class="script-selection__info"
              >
                <div class="script-selection__title">
                  <strong>{{ scriptRepository.name }}</strong>
                  <el-tag
                    size="small"
                    type="info"
                    effect="plain"
                  >
                    {{ scriptRepository.language }}
                  </el-tag>
                </div>
                <p class="script-selection__desc">
                  {{ scriptRepository.description || '暂无描述' }}
                </p>
              </div>
              <p
                v-else
                class="script-selection__placeholder"
              >
                请选择脚本仓库中的脚本
              </p>
              <div class="script-selection__actions">
                <el-button
                  size="small"
                  type="primary"
                  @click="emit('openScriptDialog')"
                >
                  选择脚本
                </el-button>
                <el-button
                  v-if="scriptRepository"
                  size="small"
                  text
                  @click="emit('clearScriptSelection')"
                >
                  清除
                </el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="脚本版本">
            <el-select
              v-model="formModel.version_id"
              placeholder="请选择版本"
              :disabled="!scriptRepository"
              :loading="scriptVersionsLoading"
              class="oa-input-lg"
            >
              <el-option
                v-for="version in scriptVersions"
                :key="version.id"
                :label="formatVersionLabel(version)"
                :value="version.id"
              >
                <div class="version-option">
                  <span>{{ formatVersionLabel(version) }}</span>
                  <small>{{ formatDate(version.created_at) }}</small>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </template>

        <template v-else>
          <template
            v-for="field in configSchema"
            :key="field.key"
          >
            <el-form-item :label="field.label">
              <el-input
                v-if="field.type === 'text' || !field.type"
                v-model="formModel[field.key]"
                :placeholder="field.placeholder"
              />
              <el-input
                v-else-if="field.type === 'secret'"
                v-model="formModel[field.key]"
                type="password"
                show-password
                :placeholder="field.placeholder"
              />
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="formModel[field.key]"
                type="textarea"
                :rows="3"
                :placeholder="field.placeholder"
              />
              <el-switch
                v-else-if="field.type === 'switch'"
                v-model="formModel[field.key]"
              />
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="formModel[field.key]"
                :controls="false"
                :placeholder="field.placeholder"
              />
              <el-select
                v-else-if="field.type === 'select'"
                v-model="formModel[field.key]"
                :placeholder="field.placeholder"
              >
                <el-option
                  v-for="option in field.options || []"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>
            </el-form-item>
          </template>
        </template>
      </section>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import type {
  AlertChannelField,
  AlertTemplateRecord,
} from '@/features/settings/api/settingsApi';
import type { ScriptRepository, ScriptVersion } from '@/features/tools/api/codeRepositoryApi';

const formModel = defineModel<Record<string, any>>('form', { required: true });

defineProps<{
  disabled: boolean;
  isScriptChannel: boolean;
  templateLoading: boolean;
  templatesForChannel: AlertTemplateRecord[];
  configSchema: AlertChannelField[];
  scriptRepository: ScriptRepository | null;
  scriptVersions: ScriptVersion[];
  scriptVersionsLoading: boolean;
  formatDate: (value?: string | null) => string;
  formatVersionLabel: (version: ScriptVersion) => string;
}>();

const emit = defineEmits<{
  (event: 'goTemplates'): void;
  (event: 'openScriptDialog'): void;
  (event: 'clearScriptSelection'): void;
}>();
</script>

<style scoped>
.channel-form {
  width: 100%;
}

.template-select {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  margin: 6px 0 0;
  font-size: var(--oa-font-meta);
  color: var(--oa-text-secondary);
}

.script-selection {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  padding: 14px;
  border-radius: 12px;
}

.script-selection__title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.script-selection__desc,
.script-selection__placeholder {
  margin: 0;
  color: var(--oa-text-secondary);
  font-size: var(--oa-font-subtitle);
}

.script-selection__actions {
  display: flex;
  gap: 8px;
}

.version-option {
  display: flex;
  justify-content: space-between;
  width: 100%;
}
</style>
