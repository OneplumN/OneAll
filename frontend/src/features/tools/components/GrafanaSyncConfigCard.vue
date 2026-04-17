<template>
  <el-card
    shadow="never"
    class="card"
  >
    <template #header>
      <div class="card-head">
        <div>
          <div class="card-title">
            连接配置
          </div>
          <div class="card-subtitle">
            分别配置 Zabbix 与 Grafana 的 API 地址与 Token。
          </div>
        </div>
        <div class="card-meta">
          <el-tag
            size="small"
            effect="plain"
            :type="isZabbixReady ? 'success' : 'info'"
          >
            Zabbix：{{ isZabbixReady ? '已配置' : '未配置' }}
          </el-tag>
          <el-tag
            size="small"
            effect="plain"
            :type="isGrafanaReady ? 'success' : 'info'"
          >
            Grafana：{{ isGrafanaReady ? '已配置' : '未配置' }}
          </el-tag>
          <el-button
            size="small"
            text
            type="primary"
            @click="emit('toggleExpand')"
          >
            {{ expanded ? '收起' : '展开' }}
          </el-button>
        </div>
      </div>
    </template>

    <el-collapse-transition>
      <div
        v-show="expanded"
        class="card-body"
      >
        <el-collapse
          v-model="panelsModel"
          class="config-collapse"
        >
          <el-collapse-item
            name="zabbix"
            title="Zabbix 连接信息"
          >
            <div class="section-hint">
              脚本会从 Zabbix 读取用户列表。
            </div>
            <el-form
              label-position="top"
              :model="formValues"
            >
              <div class="form-grid">
                <el-form-item
                  label="Zabbix API 地址"
                  required
                >
                  <el-input
                    v-model="formValues.zabbix_url"
                    placeholder="https://zabbix/api_jsonrpc.php"
                  />
                </el-form-item>
                <el-form-item
                  label="Zabbix API Token"
                  required
                >
                  <el-input
                    v-model="formValues.zabbix_token"
                    :placeholder="zabbixTokenPlaceholder"
                    type="password"
                    show-password
                  />
                </el-form-item>
              </div>
            </el-form>
          </el-collapse-item>
          <el-collapse-item
            name="grafana"
            title="Grafana 连接信息"
          >
            <div class="section-hint">
              仅需管理员 API Token；默认密码/角色等逻辑固定在脚本中。
            </div>
            <el-form
              label-position="top"
              :model="formValues"
            >
              <div class="form-grid">
                <el-form-item
                  label="Grafana API 地址"
                  required
                >
                  <el-input
                    v-model="formValues.grafana_url"
                    placeholder="https://grafana/api"
                  />
                </el-form-item>
                <el-form-item
                  label="Grafana API Token"
                  required
                >
                  <el-input
                    v-model="formValues.grafana_token"
                    :placeholder="grafanaTokenPlaceholder"
                    type="password"
                    show-password
                  />
                </el-form-item>
              </div>
            </el-form>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup lang="ts">
type CollapsePanel = 'zabbix' | 'grafana';

const panelsModel = defineModel<CollapsePanel[]>('panels', { required: true });
const formValues = defineModel<Record<string, string>>('formValues', { required: true });

defineProps<{
  expanded: boolean;
  isZabbixReady: boolean;
  isGrafanaReady: boolean;
  zabbixTokenPlaceholder: string;
  grafanaTokenPlaceholder: string;
}>();

const emit = defineEmits<{
  (event: 'toggleExpand'): void;
}>();
</script>

<style scoped>
.card {
  border-radius: 16px;
  border: 1px solid var(--oa-border-light);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.card-title {
  font-weight: 700;
  color: var(--oa-text-primary);
}

.card-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.card-body {
  padding: 4px 2px 0;
}

.config-collapse :deep(.el-collapse-item__header) {
  font-weight: 600;
}

.section-hint {
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
</style>
