<template>
  <div class="forbidden">
    <el-result icon="warning" title="无访问权限" sub-title="请联系管理员为你分配相应权限。">
      <template #extra>
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.forbidden {
  padding: 2rem;
  display: flex;
  justify-content: center;
}
</style>
