<template>
  <el-dialog
    v-model="visibleModel"
    title="新增本地用户"
    width="560px"
    destroy-on-close
  >
    <el-form label-position="top">
      <el-form-item
        label="账号"
        required
      >
        <el-input
          v-model="formModel.username"
          placeholder="例如：zhangsan"
        />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input
          v-model="formModel.display_name"
          placeholder="可选"
        />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input
          v-model="formModel.email"
          placeholder="可选"
        />
      </el-form-item>
      <el-form-item label="初始角色模板">
        <el-select
          v-model="formModel.role_id"
          placeholder="未分配"
          clearable
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="role in roles"
            :key="role.id"
            :label="role.name"
            :value="role.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item
        label="密码"
        required
      >
        <el-input
          v-model="formModel.password"
          type="password"
          show-password
          placeholder="至少 8 位"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visibleModel = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="emit('submit')"
        >
          创建
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import type { RolePayload } from '@/features/settings/api/settingsApi';

type CreateUserForm = {
  username: string;
  display_name: string;
  email: string;
  role_id: string | null;
  password: string;
};

const visibleModel = defineModel<boolean>('visible', { required: true });
const formModel = defineModel<CreateUserForm>('form', { required: true });

defineProps<{
  roles: RolePayload[];
  loading: boolean;
}>();

const emit = defineEmits<{
  (event: 'submit'): void;
}>();
</script>

<style scoped>
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
</style>
