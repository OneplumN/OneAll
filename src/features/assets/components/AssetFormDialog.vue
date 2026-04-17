<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    :width="width"
    @close="emit('close')"
  >
    <el-form
      :label-width="labelWidth"
      class="asset-form-dialog"
    >
      <el-form-item
        v-for="field in fields"
        :key="field.key"
        :label="field.label"
        :required="field.required"
      >
        <el-input
          v-if="field.component === 'input'"
          v-model="formModel[field.key]"
          :placeholder="resolvePlaceholder(field)"
          :type="field.inputType || 'text'"
          :maxlength="field.maxlength"
          clearable
        />
        <el-input
          v-else-if="field.component === 'textarea'"
          v-model="formModel[field.key]"
          type="textarea"
          :rows="3"
          :placeholder="resolvePlaceholder(field)"
        />
        <el-select
          v-else-if="field.component === 'select'"
          v-model="formModel[field.key]"
          :placeholder="resolvePlaceholder(field)"
          clearable
        >
          <el-option
            v-for="option in field.options || []"
            :key="`${field.key}-${String(option.value)}`"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <el-input-number
          v-else-if="field.component === 'number'"
          v-model="formModel[field.key]"
          :min="field.min ?? 0"
          :max="field.max ?? 65535"
          :step="field.step ?? 1"
          :placeholder="resolvePlaceholder(field)"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visibleModel = false">
        {{ cancelText }}
      </el-button>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="disabled"
        @click="emit('submit')"
      >
        {{ submitText }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
type AssetFormDialogField = {
  key: string;
  label: string;
  component: 'input' | 'textarea' | 'select' | 'number';
  placeholder?: string;
  options?: Array<{ label: string; value: unknown }>;
  required?: boolean;
  inputType?: string;
  maxlength?: number;
  min?: number;
  max?: number;
  step?: number;
};

const visibleModel = defineModel<boolean>('visible', { required: true });

const formModel = defineModel<Record<string, any>>('form', { required: true });

defineProps<{
  title: string;
  fields: AssetFormDialogField[];
  loading?: boolean;
  disabled?: boolean;
  width?: string;
  labelWidth?: string;
  submitText?: string;
  cancelText?: string;
}>();

const emit = defineEmits<{
  (event: 'submit'): void;
  (event: 'close'): void;
}>();

const resolvePlaceholder = (field: AssetFormDialogField) => {
  if (field.placeholder) return field.placeholder;
  if (field.component === 'select') return `请选择${field.label}`;
  return `请输入${field.label}`;
};
</script>

<style scoped>
.asset-form-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
