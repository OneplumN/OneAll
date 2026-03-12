<template>
  <el-dialog
    v-model="visible"
    title="新建插件"
    width="560px"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="96px"
      status-icon
      @submit.prevent
    >
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="如：站点可用性监控" />
      </el-form-item>
      <el-form-item label="唯一标识" prop="key">
        <el-input v-model="form.key" placeholder="如：site-availability" />
      </el-form-item>
      <el-form-item label="所属分组" prop="group">
        <el-select v-model="form.group" placeholder="选择分组">
          <el-option
            v-for="item in groupOptions"
            :key="item.key"
            :label="item.label"
            :value="item.key"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="路由" prop="route">
        <el-input v-model="form.route" placeholder="/monitoring/overview" />
      </el-form-item>
      <el-form-item label="组件" prop="component">
        <el-input v-model="form.component" placeholder="MonitoringOverview.vue" />
      </el-form-item>
      <el-form-item label="摘要">
        <el-input
          v-model="form.summary"
          type="textarea"
          :rows="3"
          placeholder="简要描述插件用途"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :disabled="!canCreate" @click="emit('submit')">
        提交
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';

import type { IntegrationPluginGroupKey } from '@/data/integrationPlugins';

const props = defineProps<{
  modelValue: boolean;
  groupOptions: Array<{ key: IntegrationPluginGroupKey; label: string }>;
  form: {
    name: string;
    key: string;
    group: IntegrationPluginGroupKey;
    route: string;
    component: string;
    summary?: string;
  };
  rules: FormRules;
  canCreate: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'submit'): void;
}>();

const formRef = ref<FormInstance>();
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const validate: FormInstance['validate'] = (callback) =>
  formRef.value?.validate(callback) ?? Promise.resolve(false);

defineExpose({
  validate
});
</script>
