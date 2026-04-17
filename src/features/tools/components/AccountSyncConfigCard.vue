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
            配置 LDAP 与 Zabbix 连接信息后，可一键触发同步。
          </div>
        </div>
        <div class="card-meta">
          <el-tag
            size="small"
            effect="plain"
            :type="isLdapReady ? 'success' : 'info'"
          >
            LDAP：{{ isLdapReady ? '已配置' : '未配置' }}
          </el-tag>
          <el-tag
            size="small"
            effect="plain"
            :type="isZabbixReady ? 'success' : 'info'"
          >
            Zabbix：{{ isZabbixReady ? '已配置' : '未配置' }}
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
            name="ldap"
            title="LDAP 连接信息"
          >
            <div class="section-hint">
              脚本会从 LDAP 读取用户列表，并将用户同步到 Zabbix。
            </div>
            <el-form
              label-position="top"
              :model="formValues"
            >
              <div class="form-grid">
                <el-form-item
                  label="LDAP 地址"
                  required
                >
                  <el-input
                    v-model="formValues.ldap_domain"
                    placeholder="172.31.226.3:589"
                  />
                </el-form-item>
                <el-form-item
                  label="LDAP Base DN"
                  required
                >
                  <el-input
                    v-model="formValues.ldap_dc"
                    placeholder="ou=ou,dc=xxx,dc=com"
                  />
                </el-form-item>
                <el-form-item
                  label="绑定 DN"
                  required
                >
                  <el-input
                    v-model="formValues.ldap_user"
                    placeholder="uid=xxxx,ou=ldapaccount,dc=xxx,dc=com"
                  />
                </el-form-item>
                <el-form-item
                  label="绑定密码"
                  required
                >
                  <el-input
                    v-model="formValues.ldap_pwd"
                    :placeholder="ldapPasswordPlaceholder"
                    type="password"
                    show-password
                  />
                </el-form-item>
              </div>
            </el-form>
          </el-collapse-item>
          <el-collapse-item
            name="zabbix"
            title="Zabbix 连接信息"
          >
            <div class="section-hint">
              需要管理员 API Token；用户组/角色等逻辑在脚本内维护。
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
                  label="Zabbix Token"
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
        </el-collapse>
        <div class="form-hint">
          敏感字段不会在页面回填；留空表示保持已保存的密钥不变。
        </div>
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script setup lang="ts">
type CollapsePanel = 'ldap' | 'zabbix';

const panelsModel = defineModel<CollapsePanel[]>('panels', { required: true });
const formValues = defineModel<Record<string, string>>('formValues', { required: true });

defineProps<{
  expanded: boolean;
  isLdapReady: boolean;
  isZabbixReady: boolean;
  ldapPasswordPlaceholder: string;
  zabbixTokenPlaceholder: string;
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

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--oa-text-secondary);
}
</style>
