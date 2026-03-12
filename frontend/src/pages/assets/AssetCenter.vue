<template>
  <RepositoryPageShell
    :root-title="rootTitle"
    :section-title="viewConfig.title"
    :breadcrumb="breadcrumbTitle"
  >
    <template #actions>
      <el-button
        v-if="showSyncButton"
        class="toolbar-button"
        type="primary"
        :loading="syncing"
        :disabled="!canManage"
        @click="handleSync"
      >
        同步资产
      </el-button>
    </template>

    <div class="asset-filters">
      <div class="filters-left">
        <el-button
          class="toolbar-button toolbar-button--primary"
          type="primary"
          plain
          :disabled="!canCreate"
          @click="openCreateDialog"
        >
          新增
        </el-button>
        <el-button
          v-if="canImport"
          class="toolbar-button"
          plain
          :disabled="!canCreate"
          @click="openImportDialog"
        >
          批量导入
        </el-button>
        <el-button class="toolbar-button" plain @click="handleExport">导出 CSV</el-button>
        <el-dropdown
          v-if="viewKey === 'workorder-host'"
          trigger="click"
          :disabled="!canManage || !selectedRowIds.length"
          @command="handleBatchStatusCommand"
        >
          <el-button class="toolbar-button" plain :disabled="!canManage || !selectedRowIds.length">
            批量状态（{{ selectedRowIds.length }}）
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="online">设为在线</el-dropdown-item>
              <el-dropdown-item command="maintenance">设为维护</el-dropdown-item>
              <el-dropdown-item command="offline">设为下线</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div class="filters-right">
        <el-select
          v-if="viewConfig.filters?.networkType"
          v-model="networkFilter"
          placeholder="互联网类型"
          clearable
          class="pill-input narrow-select"
        >
          <el-option label="全部" value="" />
          <el-option label="内网域名" value="internal" />
          <el-option label="互联网域名" value="internet" />
        </el-select>

        <el-select
          v-if="showOnlineStatusFilter"
          v-model="onlineStatusFilter"
          placeholder="在线状态"
          clearable
          class="pill-input narrow-select"
        >
          <el-option label="全部" value="" />
          <el-option label="在线" value="online" />
          <el-option label="维护" value="maintenance" />
          <el-option label="下线" value="offline" />
        </el-select>

        <el-select
          v-if="showProxyFilter"
          v-model="proxyFilter"
          placeholder="Proxy"
          clearable
          filterable
          class="pill-input narrow-select"
        >
          <el-option label="全部" value="" />
          <el-option v-for="option in proxyOptions" :key="option" :label="option" :value="option" />
        </el-select>

        <el-select
          v-if="showInterfaceAvailableFilter"
          v-model="interfaceAvailableFilter"
          placeholder="接口可用性"
          clearable
          filterable
          class="pill-input narrow-select"
        >
          <el-option label="全部" value="" />
          <el-option v-for="option in interfaceAvailableOptions" :key="option" :label="option" :value="option" />
        </el-select>

        <el-select
          v-if="showAppStatusFilter"
          v-model="appStatusFilter"
          placeholder="应用状态"
          clearable
          filterable
          class="pill-input narrow-select"
        >
          <el-option label="全部" value="" />
          <el-option v-for="option in appStatusOptions" :key="option" :label="option" :value="option" />
        </el-select>

        <el-input
          v-model="keyword"
          :placeholder="keywordPlaceholder"
          clearable
          class="pill-input search-input search-input--compact"
        />
      </div>
    </div>

    <div class="asset-table">
      <div :class="['asset-table__card', { 'asset-table__card--x-scroll': allowHorizontalScroll }]">
        <el-table
          height="100%"
          v-loading="tableLoading"
          :data="pagedRows"
          @selection-change="handleSelectionChange"
          stripe
          :header-cell-style="tableHeaderStyle"
          :cell-style="tableCellStyle"
        >
          <template #empty>
            <div class="table-empty">
              <p>暂无资产数据</p>
            </div>
          </template>
          <el-table-column v-if="viewKey === 'workorder-host'" type="selection" width="48" fixed="left" />
          <el-table-column
            v-for="column in viewConfig.columns"
            :key="column.key"
            :prop="column.key"
            :label="column.label"
            :width="column.width"
            :min-width="column.minWidth"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <el-dropdown
                v-if="viewKey === 'workorder-host' && column.key === 'online_status' && (row.online_status_code || '')"
                trigger="click"
                :disabled="!canManage || statusToggling[row.id]"
                @command="(command: string) => handleRowStatusCommand(row, command)"
              >
                <el-tag size="small" effect="plain" :type="statusTagType(row[column.key])">
                  {{ row[column.key] }}
                </el-tag>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="online">在线</el-dropdown-item>
                    <el-dropdown-item command="maintenance">维护</el-dropdown-item>
                    <el-dropdown-item command="offline">下线</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-tag
                v-else-if="column.type === 'status' && row[column.key] && row[column.key] !== '-'"
                size="small"
                :type="statusTagType(row[column.key])"
                effect="plain"
              >
                {{ row[column.key] }}
              </el-tag>
              <span v-else>{{ row[column.key] || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="showEditColumn" label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button text size="small" :disabled="!canManage" @click.stop="openEditDialog(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <div class="asset-footer">
        <div class="footer-left">
          <div class="asset-stats">共 {{ totalCount }} 条</div>
          <el-pagination
            class="asset-pagination__sizes"
            :total="totalCount"
            :current-page="page"
            :page-size="pageSize"
            :page-sizes="pageSizeOptions"
            layout="sizes"
            background
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
        <div class="footer-right">
          <el-pagination
            class="asset-pagination__pager"
            :total="totalCount"
            :current-page="page"
            :page-size="pageSize"
            layout="prev, pager, next"
            background
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </template>

    <el-dialog
      v-model="createDialogVisible"
      :title="createDialogTitle"
      width="520px"
      @close="resetCreateForm"
    >
      <el-form label-width="120px" class="create-form">
        <el-form-item
          v-for="field in currentFormFields"
          :key="field.key"
          :label="field.label"
          :required="field.required"
        >
          <el-input
            v-if="field.component === 'input'"
            v-model="createForm[field.key]"
            :placeholder="field.placeholder"
            :type="field.inputType || 'text'"
            :maxlength="field.maxlength"
            clearable
          />
          <el-input
            v-else-if="field.component === 'textarea'"
            type="textarea"
            v-model="createForm[field.key]"
            :rows="3"
            :placeholder="field.placeholder"
          />
          <el-select
            v-else-if="field.component === 'select'"
            v-model="createForm[field.key]"
            :placeholder="field.placeholder || '请选择'"
            clearable
          >
            <el-option
              v-for="option in field.options || []"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input-number
            v-else-if="field.component === 'number'"
            v-model="createForm[field.key]"
            :min="field.min ?? 0"
            :max="field.max ?? 65535"
            :step="field.step ?? 1"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="handleCreateSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑工单纳管主机"
      width="520px"
      @close="resetEditForm"
    >
      <el-form label-width="120px" class="create-form">
        <el-form-item
          v-for="field in currentFormFields"
          :key="field.key"
          :label="field.label"
          :required="field.required"
        >
          <el-input
            v-if="field.component === 'input'"
            v-model="editForm[field.key]"
            :placeholder="field.placeholder"
            :type="field.inputType || 'text'"
            :maxlength="field.maxlength"
            clearable
          />
          <el-input
            v-else-if="field.component === 'textarea'"
            type="textarea"
            v-model="editForm[field.key]"
            :rows="3"
            :placeholder="field.placeholder"
          />
          <el-select
            v-else-if="field.component === 'select'"
            v-model="editForm[field.key]"
            :placeholder="field.placeholder || '请选择'"
            clearable
          >
            <el-option
              v-for="option in field.options || []"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input-number
            v-else-if="field.component === 'number'"
            v-model="editForm[field.key]"
            :min="field.min ?? 0"
            :max="field.max ?? 65535"
            :step="field.step ?? 1"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" :disabled="!canManage" @click="handleEditSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="importDialogVisible"
      title="批量导入"
      width="640px"
      @close="resetImportState"
    >
      <div class="import-toolbar">
        <el-button size="small" @click="downloadImportTemplate">下载模板</el-button>
        <label class="upload-input">
          <input type="file" accept=".csv,.txt" @change="handleImportFileChange" />
          <span>{{ importFileName || '选择 CSV 文件' }}</span>
        </label>
      </div>

      <el-table
        v-if="importPreviewRows.length"
        :data="importPreviewRows"
        height="260"
        class="import-preview"
      >
        <el-table-column
          v-for="column in currentImportTemplate?.columns || []"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
        />
      </el-table>
      <el-empty v-else description="尚未选择文件" />

      <el-alert
        v-if="importErrors.length"
        type="warning"
        show-icon
        :closable="false"
        class="import-errors"
      >
        <ul>
          <li v-for="error in importErrors" :key="error">{{ error }}</li>
        </ul>
      </el-alert>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importSubmitting"
          :disabled="!canCreate || !importPreviewRows.length"
          @click="handleImportSubmit"
        >
          导入
        </el-button>
      </template>
    </el-dialog>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import * as XLSX from 'xlsx';

import RepositoryPageShell from '@/components/RepositoryPageShell.vue';
import {
  queryAssets,
  triggerAssetSync,
  createAsset,
  updateAsset,
  importAssets,
  type AssetCreatePayload,
  type QueryAssetsParams
} from '@/services/assetsApi';
import { listPluginConfigs, type PluginConfigRecord } from '@/services/monitoringApi';
import { executeScriptById, executeScriptByLabel } from '@/services/scriptExecutor';
import { listToolExecutions, type ToolExecutionRecord } from '@/services/toolsApi';
import { INTEGRATION_PLUGIN_MAP } from '@/data/integrationPlugins';
import { useSessionStore } from '@/stores/session';

interface AssetRecord {
  id: string;
  name: string;
  external_id?: string;
  system_name?: string | null;
  source: string;
  sync_status: string;
  synced_at: string;
  metadata?: Record<string, any> | null;
  owners?: any[];
  contacts?: any[];
}

interface AssetRow {
  id: string;
  [key: string]: any;
}

type AssetViewKey = 'cmdb-domain' | 'zabbix-host' | 'ipmp-project' | 'workorder-host';

interface AssetColumn {
  key: string;
  label: string;
  width?: number | string;
  minWidth?: number | string;
  type?: 'status';
}

interface AssetFormFieldOption {
  label: string;
  value: string;
}

interface AssetFormField {
  key: string;
  label: string;
  component: 'input' | 'textarea' | 'select' | 'number';
  placeholder?: string;
  options?: AssetFormFieldOption[];
  required?: boolean;
  inputType?: string;
  maxlength?: number;
  min?: number;
  max?: number;
  step?: number;
  default?: any;
}

interface ImportTemplateColumn {
  key: string;
  label: string;
  required?: boolean;
  sample?: string;
}

interface ImportTemplate {
  columns: ImportTemplateColumn[];
  mapRow(row: Record<string, string>): Record<string, any>;
}

interface AssetViewDefinition {
  title: string;
  description: string;
  source?: string;
  assetTypes?: string[];
  filters?: {
    networkType?: boolean;
  };
  columns: AssetColumn[];
  formFields: AssetFormField[];
  pluginType?: string;
  configFields?: Array<{ key: string; label: string; placeholder?: string }>;
  importTemplate?: ImportTemplate;
  integrationInfo?: {
    summary: string;
    envVar?: string;
    note?: string;
  };
  transform(record: AssetRecord): AssetRow | null;
  buildPayload(form: Record<string, any>): AssetCreatePayload;
}

const ROUTE_VIEW_KEY: Record<string, AssetViewKey> = {
  'assets-domain': 'cmdb-domain',
  'integrations-assets-domain': 'cmdb-domain',
  'assets-zabbix': 'zabbix-host',
  'integrations-assets-zabbix': 'zabbix-host',
  'assets-ipmp': 'ipmp-project',
  'integrations-assets-ipmp': 'ipmp-project',
  'assets-workorder-hosts': 'workorder-host',
  'integrations-assets-workorder-hosts': 'workorder-host'
};

const ASSET_VIEW_DEFINITIONS: Record<AssetViewKey, AssetViewDefinition> = {
  'cmdb-domain': {
    title: 'CMDB 域名',
    description: '汇聚 CMDB 域名资产，展示所属系统、网络类型及责任人。',
    source: 'CMDB',
    assetTypes: ['cmdb-domain', 'domain'],
    pluginType: 'asset_cmdb_domain',
    integrationInfo: {
      summary: '从 CMDB 同步域名清单，可通过 ASSET_SYNC_CMDB_FILE 指定样例或脚本输出文件。',
      envVar: 'ASSET_SYNC_CMDB_FILE',
      note: '脚本运行后生成的 JSON 列表会被自动解析写入资产库。'
    },
    filters: { networkType: true },
    columns: [
      { key: 'domain', label: '域名', minWidth: 220 },
      { key: 'system_name', label: '所属系统', minWidth: 200 },
      { key: 'network_type', label: '互联网类型', width: 160 },
      { key: 'owner', label: '负责人', width: 140 },
      { key: 'alert_contacts', label: '告警联系人（工号）', minWidth: 200 }
    ],
    formFields: [
      { key: 'domain', label: '域名', component: 'input', required: true, placeholder: '例如 https://oneall.com' },
      { key: 'system_name', label: '所属系统', component: 'input', required: true, placeholder: '请输入系统名称' },
      {
        key: 'network_type',
        label: '互联网类型',
        component: 'select',
        required: true,
        options: [
          { label: '内网域名', value: 'internal' },
          { label: '互联网域名', value: 'internet' }
        ],
        default: 'internet'
      },
      { key: 'owner', label: '负责人', component: 'input', placeholder: '负责人姓名' },
      { key: 'alert_contacts', label: '告警联系人（工号）', component: 'input', placeholder: '000123,000456' }
    ],
    importTemplate: {
      columns: [
        { key: 'domain', label: '域名', required: true, sample: 'https://oneall.cn' },
        { key: 'system_name', label: '所属系统', required: true, sample: 'OneAll 平台' },
        { key: 'network_type', label: '互联网类型', sample: 'internet' },
        { key: 'owner', label: '负责人', sample: '张三' },
        { key: 'alert_contacts', label: '告警联系人（工号）', sample: '000123,000456' }
      ],
      mapRow: (row) => ({
        domain: row.domain || '',
        system_name: row.system_name || '',
        network_type: row.network_type || 'internet',
        owner: row.owner || '',
        alert_contacts: row.alert_contacts || ''
      })
    },
    transform(record) {
      const metadata = record.metadata || {};
      const networkCode = metadata.network_type || metadata.internet_type || '';
      return {
        id: record.id,
        domain: metadata.domain || record.name,
        system_name: metadata.system_name || record.system_name || '-',
        network_type: networkTypeLabel(networkCode),
        network_code: networkCode,
        owner: formatPeople(metadata.owner || metadata.owner_name || record.owners),
        alert_contacts: formatContacts(metadata.alert_contacts || record.contacts),
        sync_status: record.sync_status || 'unknown',
        synced_at: formatDate(record.synced_at)
      };
    },
    buildPayload(form) {
      const contacts = parseContactsInput(form.alert_contacts);
      const owners = form.owner ? [form.owner] : [];
      const metadata = {
        asset_type: 'cmdb-domain',
        domain: form.domain,
        system_name: form.system_name,
        network_type: form.network_type || 'internet',
        owner: form.owner,
        alert_contacts: contacts,
      };
      return {
        source: 'CMDB',
        external_id: `domain:${form.domain}`,
        name: form.domain,
        system_name: form.system_name,
        owners,
        contacts,
        metadata,
      };
    }
  },
  'zabbix-host': {
    title: 'Zabbix 主机',
    description: '同步 Zabbix 主机资产，展示 IP、主机组与 Proxy 信息。',
    source: 'Zabbix',
    pluginType: 'asset_zabbix_host',
    integrationInfo: {
      summary: 'Zabbix 采集脚本输出主机列表，可通过 ASSET_SYNC_ZABBIX_FILE 覆盖默认样例。',
      envVar: 'ASSET_SYNC_ZABBIX_FILE'
    },
    columns: [
      { key: 'ip', label: 'IP 地址', minWidth: 160 },
      { key: 'host_name', label: '主机名称', minWidth: 200 },
      { key: 'visible_name', label: '可见名称', minWidth: 200 },
      { key: 'host_group', label: '主机群组', minWidth: 220 },
      { key: 'proxy', label: 'Proxy', minWidth: 160 },
      { key: 'interface_type', label: '接口类型', width: 140 },
      { key: 'interface_available', label: '接口可用性', width: 160, type: 'status' }
    ],
    formFields: [
      { key: 'ip', label: 'IP 地址', component: 'input', required: true, placeholder: '例如 10.0.0.5' },
      { key: 'host_name', label: '主机名称', component: 'input', required: true, placeholder: '主机显示名称' },
      { key: 'host_group', label: '主机群组', component: 'input', placeholder: '多个群组用逗号分隔' },
      { key: 'proxy', label: 'Proxy', component: 'input', placeholder: 'proxy 名称或 IP' }
    ],
    transform(record) {
      const metadata = record.metadata || {};
      const hostDisabled = isZabbixHostDisabled(record, metadata);
      const interfaceAvailable = interfaceAvailabilityLabel(
        hostDisabled ? '停用' : (metadata.interface_available_label ?? metadata.interface_available)
      );
      return {
        id: record.id,
        ip: metadata.ip || metadata.host_ip || metadata.primary_ip || '-',
        host_name: metadata.host_name || record.name,
        visible_name: metadata.visible_name || record.name || '-',
        host_group: formatArray(metadata.host_groups || metadata.groups),
        proxy: metadata.proxy || metadata.proxy_name || '-',
        interface_type: metadata.interface_type_label || metadata.interface_type || '-',
        interface_available: interfaceAvailable,
        sync_status: record.sync_status || 'unknown',
        synced_at: formatDate(record.synced_at)
      };
    },
    buildPayload(form) {
      const hostGroups = parseListInput(form.host_group);
      const metadata = {
        asset_type: 'zabbix-host',
        ip: form.ip,
        host_name: form.host_name,
        host_groups: hostGroups,
        proxy: form.proxy,
      };
      return {
        source: 'Zabbix',
        external_id: `zabbix:${form.host_name || form.ip}`,
        name: form.host_name || form.ip,
        metadata,
      };
    }
  },
  'ipmp-project': {
    title: 'IPMP 项目',
    description: '展示 IPMP 项目信息，包括应用编号、状态与责任人。',
    source: 'IPMP',
    pluginType: 'asset_ipmp_project',
    integrationInfo: {
      summary: 'IPMP 接口同步的应用档案，可通过 ASSET_SYNC_IPMP_FILE 指定脚本输出。',
      envVar: 'ASSET_SYNC_IPMP_FILE'
    },
    columns: [
      { key: 'app_code', label: '应用编号', minWidth: 160 },
      { key: 'app_name_cn', label: '应用中文名称', minWidth: 200 },
      { key: 'app_name_en', label: '应用英文简称', minWidth: 180 },
      { key: 'app_status', label: '应用状态', minWidth: 140, type: 'status' },
      { key: 'owner', label: '系统负责人', minWidth: 160 },
      { key: 'security_level', label: '等保级别', minWidth: 160 },
      { key: 'system_origin', label: '系统归属', minWidth: 160 }
    ],
    importTemplate: {
      columns: [
        { key: 'app_code', label: '应用编号', required: true, sample: 'APP-OPS-001' },
        { key: 'app_name_cn', label: '应用中文名称', required: true, sample: 'OneAll 运维门户' },
        { key: 'app_name_en', label: '应用英文简称', sample: 'OneAll Ops' },
        { key: 'app_status', label: '应用状态', sample: '运行中' },
        { key: 'owner', label: '系统负责人', sample: '王五' },
        { key: 'security_level', label: '等保级别', sample: '二级' },
        { key: 'system_origin', label: '系统归属', sample: '自研' }
      ],
      mapRow: (row) => ({
        app_code: row.app_code || row['应用编号'] || '',
        app_name_cn: row.app_name_cn || row['应用中文名称'] || '',
        app_name_en: row.app_name_en || row['应用英文简称'] || '',
        app_status: row.app_status || row['应用状态'] || '',
        owner: row.owner || row['系统负责人'] || '',
        security_level: row.security_level || row['系统等级保护定级级别'] || '',
        system_origin: row.system_origin || row['系统归属'] || ''
      })
    },
    formFields: [
      { key: 'app_code', label: '应用编号', component: 'input', required: true },
      { key: 'app_name_cn', label: '应用中文名称', component: 'input', required: true },
      { key: 'app_name_en', label: '应用英文简称', component: 'input' },
      { key: 'app_status', label: '应用状态', component: 'input', placeholder: '在研/上线等' },
      { key: 'owner', label: '系统负责人', component: 'input' },
      { key: 'security_level', label: '等保级别', component: 'input' },
      { key: 'system_origin', label: '系统归属', component: 'input' }
    ],
    transform(record) {
      const metadata = record.metadata || {};
      return {
        id: record.id,
        app_code: metadata.app_code || metadata.application_code || record.external_id || '-',
        app_name_cn: metadata.app_name_cn || metadata.application_cn || record.name,
        app_name_en: metadata.app_name_en || metadata.application_en || '-',
        app_status: metadata.app_status || metadata.status || '-',
        owner: metadata.owner || metadata.system_owner || formatPeople(record.owners),
        security_level: metadata.security_level || metadata.grade || '-',
        system_origin: metadata.system_origin || metadata.system_group || '-',
        sync_status: record.sync_status || 'unknown',
        synced_at: formatDate(record.synced_at)
      };
    },
    buildPayload(form) {
      const metadata = {
        asset_type: 'ipmp-project',
        app_code: form.app_code,
        app_name_cn: form.app_name_cn,
        app_name_en: form.app_name_en,
        app_status: form.app_status,
        owner: form.owner,
        security_level: form.security_level,
        system_origin: form.system_origin,
      };
      return {
        source: 'IPMP',
        external_id: form.app_code,
        name: form.app_name_cn || form.app_code,
        system_name: form.app_name_cn,
        owners: form.owner ? [form.owner] : [],
        metadata,
      };
    }
  },
  'workorder-host': {
    title: '工单纳管主机信息',
    description: '展示工单纳管主机的 IP、机房、Proxy、端口及联系人信息。',
    source: 'Manual',
    assetTypes: ['workorder-host', 'workorder'],
    pluginType: 'asset_workorder_host',
    integrationInfo: {
      summary: '手工或 ITSM 脚本纳管的探针主机列表，可通过 ASSET_SYNC_WORKORDER_FILE 提供数据。',
      envVar: 'ASSET_SYNC_WORKORDER_FILE'
    },
    columns: [
      { key: 'ip', label: 'IP 地址', minWidth: 160 },
      { key: 'online_status', label: '在线状态', width: 120, type: 'status' },
      { key: 'idc', label: '所在机房', minWidth: 160 },
      { key: 'proxy', label: '接入 ITSI Proxy', minWidth: 200 },
      { key: 'port', label: '端口', width: 100 },
      { key: 'alert_contacts', label: '告警联系人', minWidth: 200 },
      { key: 'hostname', label: 'Hostname', minWidth: 180 },
      { key: 'app_system', label: '应用系统', minWidth: 200 },
      { key: 'owner', label: '系统负责人', minWidth: 160 }
    ],
    importTemplate: {
      columns: [
        { key: 'ip', label: 'IP 地址', required: true, sample: '10.30.1.5' },
        { key: 'online_status', label: '在线状态', sample: 'online' },
        { key: 'idc', label: '所在机房', sample: '北京亦庄' },
        { key: 'proxy', label: '接入 ITSI Proxy', sample: 'itsi-bj-proxy' },
        { key: 'port', label: '端口', sample: '8080' },
        { key: 'alert_contacts', label: '告警联系人', sample: '001234' },
        { key: 'hostname', label: 'Hostname', sample: 'payment-worker-01' },
        { key: 'app_system', label: '应用系统', sample: '支付调度' },
        { key: 'owner', label: '系统负责人', sample: '陈七' }
      ],
      mapRow: (row) => ({
        ip: row.ip || '',
        online_status: normalizeOnlineStatusCode(row.online_status) || 'online',
        idc: row.idc || '',
        proxy: row.proxy || '',
        port: row.port || '',
        alert_contacts: row.alert_contacts || '',
        hostname: row.hostname || '',
        app_system: row.app_system || '',
        owner: row.owner || ''
      })
    },
    formFields: [
      { key: 'ip', label: 'IP 地址', component: 'input', required: true },
      {
        key: 'online_status',
        label: '在线状态',
        component: 'select',
        required: true,
        options: [
          { label: '在线', value: 'online' },
          { label: '维护', value: 'maintenance' },
          { label: '下线', value: 'offline' }
        ],
        default: 'online'
      },
      { key: 'idc', label: '所在机房', component: 'input' },
      { key: 'proxy', label: '接入 ITSI Proxy', component: 'input' },
      { key: 'port', label: '端口', component: 'number', min: 1, max: 65535, step: 1 },
      { key: 'alert_contacts', label: '告警联系人', component: 'input', placeholder: '000123,000456' },
      { key: 'hostname', label: 'Hostname', component: 'input' },
      { key: 'app_system', label: '应用系统', component: 'input' },
      { key: 'owner', label: '系统负责人', component: 'input' }
    ],
    transform(record) {
      const metadata = record.metadata || {};
      const statusCode = onlineStatusFromRecord(record);
      return {
        id: record.id,
        ip: metadata.ip || metadata.host_ip || '-',
        online_status: onlineStatusLabel(statusCode),
        online_status_code: statusCode,
        idc: metadata.idc || metadata.idc_name || '-',
        proxy: metadata.proxy || metadata.proxy_name || '-',
        port: metadata.port || '-',
        alert_contacts: formatContacts(metadata.alert_contacts || record.contacts),
        hostname: metadata.hostname || record.name || '-',
        app_system: metadata.app_system || metadata.application || '-',
        owner: metadata.owner || metadata.system_owner || formatPeople(record.owners),
        sync_status: record.sync_status || 'unknown',
        synced_at: formatDate(record.synced_at)
      };
    },
    buildPayload(form) {
      const contacts = parseContactsInput(form.alert_contacts);
      const metadata = {
        asset_type: 'workorder-host',
        online_status: form.online_status,
        ip: form.ip,
        idc: form.idc,
        proxy: form.proxy,
        port: form.port,
        alert_contacts: contacts,
        hostname: form.hostname,
        app_system: form.app_system,
        owner: form.owner,
      };
      return {
        source: 'Manual',
        external_id: `workorder:${form.ip}`,
        name: form.hostname || form.ip,
        system_name: form.app_system,
        owners: form.owner ? [form.owner] : [],
        contacts,
        metadata,
      };
    }
  }
};

const sessionStore = useSessionStore();
const canCreate = computed(() => sessionStore.hasPermission('assets.records.create'));
const canManage = computed(() => sessionStore.hasPermission('assets.records.manage'));

const assets = ref<AssetRecord[]>([]);
const totalCount = ref(0);
const facets = ref<Record<string, string[]>>({});
const facetsByView = reactive<Record<string, Record<string, string[]>>>({});
const suppressReload = ref(false);
const syncing = ref(false);
const tableLoading = ref(false);
const keyword = ref('');
const keywordDebounced = ref('');
const networkFilter = ref('');
const onlineStatusFilter = ref('');
const proxyFilter = ref('');
const interfaceAvailableFilter = ref('');
const appStatusFilter = ref('');
const page = ref(1);
const pageSize = ref(20);
const pageSizeOptions = [10, 20, 50];
const createDialogVisible = ref(false);
const createSubmitting = ref(false);
const createForm = reactive<Record<string, any>>({});
const editDialogVisible = ref(false);
const editSubmitting = ref(false);
const editForm = reactive<Record<string, any>>({});
const editingRecordId = ref<string | null>(null);
const statusToggling = reactive<Record<string, boolean>>({});
const selectedRowIds = ref<string[]>([]);
const importDialogVisible = ref(false);
const importSubmitting = ref(false);
const importPreviewRows = ref<Record<string, any>[]>([]);
const importPayloads = ref<AssetCreatePayload[]>([]);
const importErrors = ref<string[]>([]);
const importFileName = ref('');
const MAX_IMPORT_RECORDS = 500;
const pluginConfig = ref<PluginConfigRecord | null>(null);
const pluginConfigLoading = ref(false);

const route = useRoute();
const viewKey = computed<AssetViewKey>(() => ROUTE_VIEW_KEY[String(route.name)] || 'cmdb-domain');
const viewConfig = computed(() => ASSET_VIEW_DEFINITIONS[viewKey.value]);
const isIntegrationRoute = computed(() => route.meta?.navGroup === 'integrations');
const rootTitle = computed(() => (isIntegrationRoute.value ? '集成' : '资产信息'));
const breadcrumbTitle = computed(() => (isIntegrationRoute.value ? '资产信息' : ''));
const showEditColumn = computed(() => viewKey.value === 'workorder-host');
const allowHorizontalScroll = computed(() => true);
const showSyncButton = computed(() => viewKey.value !== 'workorder-host');
const keywordPlaceholder = computed(() => {
  if (viewKey.value === 'cmdb-domain') return '搜索域名 / 系统 / 负责人';
  if (viewKey.value === 'zabbix-host') return '搜索 IP / 主机名 / 群组';
  if (viewKey.value === 'ipmp-project') return '搜索应用编号 / 名称 / 负责人';
  return '搜索 IP / Hostname / 系统';
});

const showOnlineStatusFilter = computed(() => viewKey.value === 'workorder-host');
const showProxyFilter = computed(() => viewKey.value === 'zabbix-host' || viewKey.value === 'workorder-host');
const showInterfaceAvailableFilter = computed(() => viewKey.value === 'zabbix-host');
const showAppStatusFilter = computed(() => viewKey.value === 'ipmp-project');
const currentFormFields = computed(() => viewConfig.value.formFields);
const createDialogTitle = computed(() => `新增${viewConfig.value.title}`);
const currentImportTemplate = computed(() => viewConfig.value.importTemplate);
const canImport = computed(() => Boolean(currentImportTemplate.value));
const pluginDefinition = computed(() => {
  const type = viewConfig.value.pluginType;
  if (!type) return undefined;
  return INTEGRATION_PLUGIN_MAP[type];
});
const runtimeMode = computed(() => pluginDefinition.value?.runtime.mode || 'embedded');
const runtimeScriptDefault = computed(() => pluginDefinition.value?.runtime.scriptLabel || '');
const pluginScriptLabel = computed(() => {
  const label = pluginConfig.value?.config?.script_label;
  return typeof label === 'string' ? label : '';
});
const pluginScriptRepositoryId = computed(() => {
  const repoId = pluginConfig.value?.config?.script_repository_id;
  return typeof repoId === 'string' ? repoId : undefined;
});
const runtimeScriptLabel = computed(() => pluginScriptLabel.value || runtimeScriptDefault.value);
const shouldLoadPluginConfig = computed(
  () => runtimeMode.value === 'script' && Boolean(viewConfig.value.pluginType)
);

const tableHeaderStyle = () => ({
  background: 'var(--oa-bg-muted)',
  color: 'var(--oa-text-secondary)',
  fontWeight: 600,
  height: '44px'
});

const tableCellStyle = () => ({
  height: '44px',
  padding: '8px 10px'
});

const matchingRecords = computed(() =>
  assets.value.filter((record) => matchesDefinition(record, viewConfig.value))
);

const shapedRows = computed(() =>
  matchingRecords.value
    .map((record) => viewConfig.value.transform(record))
    .filter((row): row is AssetRow => Boolean(row))
);

function normalizeFilterOption(value: unknown): string {
  const text = value == null ? '' : String(value).trim();
  if (!text || text === '-') return '';
  return text;
}

function uniqueRowValues(rows: AssetRow[], key: string): string[] {
  const values = rows
    .map((row) => normalizeFilterOption(row[key]))
    .filter(Boolean);
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
}

const proxyOptions = computed(() => facets.value.proxy || uniqueRowValues(shapedRows.value, 'proxy'));
const interfaceAvailableOptions = computed(() => {
  const raw = facets.value.interface_available || uniqueRowValues(shapedRows.value, 'interface_available');
  const mapped = raw
    .map((item) => {
      const label = interfaceAvailabilityLabel(item);
      return label === '-' ? '' : label;
    })
    .filter(Boolean);
  const unique = Array.from(new Set(mapped));
  const base = ['可用', '不可用', '未知', '停用'];
  const rest = unique
    .filter((value) => !base.includes(value))
    .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
  return [...base, ...rest];
});
const appStatusOptions = computed(() => facets.value.app_status || uniqueRowValues(shapedRows.value, 'app_status'));

const displayRows = computed(() => {
  let rows = shapedRows.value;
  if (viewKey.value === 'ipmp-project') {
    rows = stableSortBy(rows, (row) => normalizeAppCode(row.app_code), compareAppCodeAsc);
  }
  return rows;
});

const pagedRows = computed(() => displayRows.value);

watch(viewKey, () => {
  suppressReload.value = true;
  if (keywordDebounceTimer) {
    window.clearTimeout(keywordDebounceTimer);
    keywordDebounceTimer = null;
  }
  keyword.value = '';
  keywordDebounced.value = '';
  networkFilter.value = '';
  onlineStatusFilter.value = '';
  proxyFilter.value = '';
  interfaceAvailableFilter.value = '';
  appStatusFilter.value = '';
  selectedRowIds.value = [];
  page.value = 1;
  resetCreateForm();
  resetEditForm();
  resetImportState();
  createDialogVisible.value = false;
  editDialogVisible.value = false;
  editingRecordId.value = null;
  importDialogVisible.value = false;
  if (shouldLoadPluginConfig.value) {
    loadPluginConfig();
  } else {
    pluginConfig.value = null;
  }

  facets.value = facetsByView[viewKey.value] || {};
  suppressReload.value = false;
  void loadAssets();
});

resetCreateForm();
resetEditForm();
resetImportState();
if (shouldLoadPluginConfig.value) {
  loadPluginConfig();
}

let keywordDebounceTimer: number | null = null;

watch(keyword, () => {
  page.value = 1;
  if (keywordDebounceTimer) {
    window.clearTimeout(keywordDebounceTimer);
  }
  keywordDebounceTimer = window.setTimeout(() => {
    keywordDebounced.value = keyword.value.trim();
  }, 300);
});

function resetPageAndReload() {
  if (suppressReload.value) return;
  const current = page.value;
  page.value = 1;
  if (current === 1) {
    void loadAssets();
  }
}

watch(networkFilter, resetPageAndReload);
watch(onlineStatusFilter, resetPageAndReload);
watch(proxyFilter, resetPageAndReload);
watch(interfaceAvailableFilter, resetPageAndReload);
watch(appStatusFilter, resetPageAndReload);

onBeforeUnmount(() => {
  if (keywordDebounceTimer) {
    window.clearTimeout(keywordDebounceTimer);
    keywordDebounceTimer = null;
  }
});

function resetCreateForm() {
  currentFormFields.value.forEach((field) => {
    createForm[field.key] = field.default ?? '';
  });
}

function resetEditForm() {
  currentFormFields.value.forEach((field) => {
    editForm[field.key] = field.default ?? '';
  });
}

function openCreateDialog() {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  resetCreateForm();
  createDialogVisible.value = true;
}

function contactsToInput(value: unknown): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === 'string' ? item : item?.id || item?.name))
      .filter(Boolean)
      .join(',');
  }
  if (typeof value === 'string') return value;
  return '';
}

function fillEditFormFromRecord(record: AssetRecord) {
  if (viewKey.value !== 'workorder-host') return;
  const metadata = record.metadata || {};
  editForm.ip = metadata.ip || metadata.host_ip || '';
  editForm.online_status = onlineStatusFromRecord(record) || 'online';
  editForm.idc = metadata.idc || metadata.idc_name || '';
  editForm.proxy = metadata.proxy || metadata.proxy_name || '';
  const port = metadata.port;
  editForm.port = typeof port === 'number' ? port : port ? Number(port) : undefined;
  editForm.alert_contacts = contactsToInput(metadata.alert_contacts || record.contacts);
  editForm.hostname = metadata.hostname || record.name || '';
  editForm.app_system = metadata.app_system || metadata.application || record.system_name || '';
  const owner = metadata.owner || metadata.system_owner || formatPeople(record.owners);
  editForm.owner = owner === '-' ? '' : owner;
}

function openEditDialog(row: AssetRow) {
  if (!showEditColumn.value) return;
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  const record = matchingRecords.value.find((item) => item.id === row.id);
  if (!record) {
    ElMessage.error('找不到对应资产记录');
    return;
  }
  resetEditForm();
  editingRecordId.value = record.id;
  fillEditFormFromRecord(record);
  editDialogVisible.value = true;
}

function validateForm(form: Record<string, any>) {
  const missingField = currentFormFields.value.find((field) => {
    if (!field.required) return false;
    const value = form[field.key];
    if (field.component === 'number') {
      return value === undefined || value === null || value === '';
    }
    return !value || !String(value).trim();
  });
  if (missingField) {
    ElMessage.error(`请输入${missingField.label}`);
    return false;
  }
  return true;
}

function validateCreateForm() {
  return validateForm(createForm);
}

function validateEditForm() {
  return validateForm(editForm);
}

function handleSelectionChange(rows: Array<{ id: string }>) {
  if (viewKey.value !== 'workorder-host') return;
  selectedRowIds.value = rows.map((row) => row.id).filter(Boolean);
}

function handleRowStatusCommand(row: AssetRow, command: unknown) {
  const next = normalizeOnlineStatusCode(command);
  if (!next) return;
  void updateWorkorderOnlineStatus(row.id, next);
}

function handleBatchStatusCommand(command: unknown) {
  const next = normalizeOnlineStatusCode(command);
  if (!next) return;
  void batchUpdateWorkorderOnlineStatus(next);
}

async function updateWorkorderOnlineStatus(recordId: string, next: OnlineStatusCode) {
  if (viewKey.value !== 'workorder-host') return;
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  const record = matchingRecords.value.find((item) => item.id === recordId);
  if (!record) return;
  if (statusToggling[recordId]) return;
  statusToggling[recordId] = true;
  try {
    const metadata = { ...(record.metadata || {}), online_status: next, asset_type: 'workorder-host' };
    await updateAsset(recordId, { metadata });
    assets.value = assets.value.map((item) =>
      item.id === recordId ? { ...item, metadata } : item
    );
  } catch (error) {
    ElMessage.error('状态更新失败，请稍后重试');
  } finally {
    statusToggling[recordId] = false;
  }
}

async function batchUpdateWorkorderOnlineStatus(next: OnlineStatusCode) {
  if (viewKey.value !== 'workorder-host') return;
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  const ids = selectedRowIds.value;
  if (!ids.length) return;
  const tasks = ids.filter((id) => !statusToggling[id]).map((id) => updateWorkorderOnlineStatus(id, next));
  await Promise.all(tasks);
  ElMessage.success(`已批量设置为「${onlineStatusLabel(next)}」`);
}

async function handleEditSubmit() {
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  if (!editingRecordId.value) return;
  if (!validateEditForm()) return;
  editSubmitting.value = true;
  try {
    const snapshot: Record<string, any> = {};
    currentFormFields.value.forEach((field) => {
      snapshot[field.key] = editForm[field.key];
    });
    const payload = viewConfig.value.buildPayload(snapshot);
    await updateAsset(editingRecordId.value, {
      external_id: payload.external_id,
      name: payload.name,
      system_name: payload.system_name,
      owners: payload.owners,
      contacts: payload.contacts,
      metadata: payload.metadata
    });
    ElMessage.success('已保存');
    editDialogVisible.value = false;
    editingRecordId.value = null;
    await loadAssets();
  } catch (error) {
    ElMessage.error('保存失败，请稍后重试');
  } finally {
    editSubmitting.value = false;
  }
}

async function handleCreateSubmit() {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  if (!validateCreateForm()) return;
  createSubmitting.value = true;
  try {
    const snapshot: Record<string, any> = {};
    currentFormFields.value.forEach((field) => {
      snapshot[field.key] = createForm[field.key];
    });
    const payload = viewConfig.value.buildPayload(snapshot);
    await createAsset(payload);
    ElMessage.success('资产已创建');
    createDialogVisible.value = false;
    await loadAssets();
  } catch (error) {
    ElMessage.error('创建失败，请稍后重试');
  } finally {
    createSubmitting.value = false;
  }
}

function resetImportState() {
  importPreviewRows.value = [];
  importPayloads.value = [];
  importErrors.value = [];
  importFileName.value = '';
}

function openImportDialog() {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  resetImportState();
  importDialogVisible.value = true;
}

function downloadImportTemplate() {
  const template = currentImportTemplate.value;
  if (!template) return;
  const header = template.columns.map((col) => col.key).join(',');
  const sampleRow = template.columns.map((col) => col.sample ?? '').join(',');
  const content = `${header}\n${sampleRow}`;
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${viewConfig.value.title}-template.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function handleImportFileChange(event: Event) {
  if (!canCreate.value) {
    ElMessage.warning('暂无新增权限');
    return;
  }
  const template = currentImportTemplate.value;
  if (!template) {
    importErrors.value = ['当前视图暂不支持导入。'];
    return;
  }
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  importFileName.value = file.name;
  importErrors.value = [];

  try {
    const buffer = await file.arrayBuffer();
    const headers = template.columns.map((col) => col.key);
    const rows = isExcelFile(file)
      ? extractWorkbookRows(buffer, headers)
      : parseCsvContent(decodeTextBuffer(buffer), headers);
    processImportRows(rows);
  } catch (error) {
    console.error('Failed to parse import file', error);
    importPreviewRows.value = [];
    importPayloads.value = [];
    importErrors.value = ['文件解析失败，请确认格式为 CSV 或 Excel，且编码为 UTF-8/GBK。'];
  } finally {
    if (target) {
      target.value = '';
    }
  }
}

function processImportRows(rows: Record<string, string>[]) {
  const template = currentImportTemplate.value;
  if (!template) return;
  const preview: Record<string, any>[] = [];
  const payloads: AssetCreatePayload[] = [];
  const errors: string[] = [];
  let nonEmptyCount = 0;

  rows.forEach((row, index) => {
    try {
      if (isRowEmpty(row)) return;
      nonEmptyCount += 1;
      if (nonEmptyCount > MAX_IMPORT_RECORDS) return;
      const mapped = template.mapRow(row);
      template.columns.forEach((col) => {
        if (col.required && !String(mapped[col.key] ?? '').trim()) {
          throw new Error(`${col.label} 不能为空`);
        }
      });
      const payload = viewConfig.value.buildPayload(mapped);
      preview.push(mapped);
      payloads.push(payload);
    } catch (error) {
      errors.push(`第 ${index + 1} 行：${error instanceof Error ? error.message : String(error)}`);
    }
  });

  if (nonEmptyCount > MAX_IMPORT_RECORDS) {
    errors.unshift(`导入数据超过 ${MAX_IMPORT_RECORDS} 条（当前 ${nonEmptyCount} 条），请拆分文件后再导入。`);
  }

  importPreviewRows.value = preview;
  importPayloads.value = payloads;
  importErrors.value = errors;
}

	async function handleImportSubmit() {
	  if (!canCreate.value) {
	    ElMessage.warning('暂无新增权限');
	    return;
	  }
	  if (!importPreviewRows.value.length) return;
	  if (importPayloads.value.length > MAX_IMPORT_RECORDS) {
	    ElMessage.warning(`最多导入 ${MAX_IMPORT_RECORDS} 条，请拆分文件后重试`);
	    return;
	  }
	  importSubmitting.value = true;
	  try {
	    const result = await importAssets(importPayloads.value);
	    if (result.failed) {
	      importErrors.value = formatImportServerErrors(result.errors || []);
	      ElMessage.warning(`导入完成：成功 ${result.created} 条，失败 ${result.failed} 条`);
	    } else {
	      ElMessage.success(`导入成功：${result.created} 条`);
	      importDialogVisible.value = false;
	    }
	    await loadAssets();
	  } catch (error) {
	    ElMessage.error(getErrorMessage(error) || '导入失败，请检查文件内容');
	  } finally {
	    importSubmitting.value = false;
	  }
	}

async function loadPluginConfig() {
  if (!shouldLoadPluginConfig.value || !viewConfig.value.pluginType) {
    pluginConfig.value = null;
    return;
  }
  pluginConfigLoading.value = true;
  try {
    const configs = await listPluginConfigs();
    pluginConfig.value =
      configs.find((item: PluginConfigRecord) => item.type === viewConfig.value.pluginType) || null;
  } catch (error) {
    pluginConfig.value = null;
  } finally {
    pluginConfigLoading.value = false;
  }
}

async function loadAssets() {
  tableLoading.value = true;
  try {
    const includeFacets = !facetsByView[viewKey.value];
    const source = viewConfig.value.source;
    const assetTypes = viewConfig.value.assetTypes || [];

    const networkType = viewConfig.value.filters?.networkType ? networkFilter.value : '';
    const params: QueryAssetsParams = {
      source: source || undefined,
      asset_type: assetTypes.length === 1 ? assetTypes[0] : assetTypes,
      keyword: keywordDebounced.value,
      proxy: showProxyFilter.value ? proxyFilter.value : '',
      interface_available: showInterfaceAvailableFilter.value ? interfaceAvailableFilter.value : '',
      app_status: showAppStatusFilter.value ? appStatusFilter.value : '',
      online_status: showOnlineStatusFilter.value ? onlineStatusFilter.value : '',
      network_type: networkType,
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
      include_facets: includeFacets,
      order: viewKey.value === 'ipmp-project' ? 'external_id' : 'synced_at',
      direction: viewKey.value === 'ipmp-project' ? 'asc' : 'desc'
    };

    const result = await queryAssets(params);
    assets.value = (result.items || []) as any;
    totalCount.value = result.pagination?.total || 0;

    if (includeFacets && result.facets) {
      facetsByView[viewKey.value] = result.facets;
      facets.value = result.facets;
    } else {
      facets.value = facetsByView[viewKey.value] || {};
    }
  } finally {
    tableLoading.value = false;
  }
}

async function handleSync() {
  if (viewKey.value === 'workorder-host') {
    ElMessage.info('工单纳管主机信息不支持同步资产');
    return;
  }
  if (!canManage.value) {
    ElMessage.warning('暂无管理权限');
    return;
  }
  syncing.value = true;
  try {
    if (runtimeMode.value === 'script') {
      if (!runtimeScriptLabel.value && !pluginScriptRepositoryId.value) {
        throw new Error('当前插件未绑定脚本，请在集成中心中配置。');
      }
      const parameters = {
        asset_view: viewKey.value,
        plugin: viewConfig.value.pluginType,
        full_snapshot: true,
        triggered_at: new Date().toISOString()
      };
      const execution = pluginScriptRepositoryId.value
        ? await executeScriptById(pluginScriptRepositoryId.value, parameters)
        : await executeScriptByLabel(runtimeScriptLabel.value!, parameters);
      ElMessage.success(`已触发同步脚本（执行 ID: ${execution.run_id}），正在写入资产数据…`);
      const finalExecution = await waitForToolExecution(execution.run_id, 120_000);
      if (finalExecution.status !== 'succeeded') {
        throw new Error(finalExecution.error_message || '同步脚本执行失败');
      }
      const ingest = (finalExecution.metadata || {})?.asset_ingest;
      if (!ingest) {
        throw new Error('脚本执行完成，但未触发平台入库；请确认脚本 main() 返回 records（List[dict]）。');
      }
      ElMessage.success(
        `资产同步完成：新增 ${ingest.created ?? 0}，更新 ${ingest.updated ?? 0}，移除 ${ingest.removed ?? 0}（本次 ${ingest.fetched ?? 0}）`
      );
    } else {
      await triggerAssetSync({ mode: 'async' });
      ElMessage.success('同步任务已触发');
    }
    await loadAssets();
  } catch (error) {
    if (runtimeScriptLabel.value && isScriptMissingError(error)) {
      ElMessage.error(`找不到脚本「${runtimeScriptLabel.value}」，请在代码管理中创建同名脚本后重试。`);
    } else {
      ElMessage.error(getErrorMessage(error));
    }
  } finally {
    syncing.value = false;
  }
}

async function waitForToolExecution(runId: string, timeoutMs: number): Promise<ToolExecutionRecord> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const items = await listToolExecutions();
    const found = items.find((item) => item.run_id === runId);
    if (found && (found.status === 'succeeded' || found.status === 'failed')) {
      return found;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 1200));
  }
  throw new Error('同步脚本执行超时，请在“代码管理-执行记录”中查看详情。');
}

function getErrorMessage(error: unknown) {
  if (typeof error === 'string') return error;
  if (error && typeof error === 'object') {
    const detail =
      (error as any)?.response?.data?.detail ||
      (error as any)?.message;
    if (detail) return String(detail);
  }
  return '同步失败，请稍后重试';
}

function isScriptMissingError(error: unknown) {
  const message = getErrorMessage(error);
  return message.includes('未找到名称或标签');
}

async function handleExport() {
  if (!totalCount.value) {
    ElMessage.warning('暂无可导出的数据');
    return;
  }
  if (totalCount.value > 5000) {
    ElMessage.warning(`当前数据量过大（${totalCount.value} 条），请先通过筛选缩小范围再导出`);
    return;
  }
  try {
    const source = viewConfig.value.source;
    const assetTypes = viewConfig.value.assetTypes || [];
    const networkType = viewConfig.value.filters?.networkType ? networkFilter.value : '';
    const params: QueryAssetsParams = {
      source: source || undefined,
      asset_type: assetTypes.length === 1 ? assetTypes[0] : assetTypes,
      keyword: keywordDebounced.value,
      proxy: showProxyFilter.value ? proxyFilter.value : '',
      interface_available: showInterfaceAvailableFilter.value ? interfaceAvailableFilter.value : '',
      app_status: showAppStatusFilter.value ? appStatusFilter.value : '',
      online_status: showOnlineStatusFilter.value ? onlineStatusFilter.value : '',
      network_type: networkType,
      limit: 5000,
      offset: 0,
      include_facets: false,
      order: viewKey.value === 'ipmp-project' ? 'external_id' : 'synced_at',
      direction: viewKey.value === 'ipmp-project' ? 'asc' : 'desc'
    };
    const result = await queryAssets(params);
    const records = (result.items || []) as AssetRecord[];
    const rows = records
      .filter((record) => matchesDefinition(record, viewConfig.value))
      .map((record) => viewConfig.value.transform(record))
      .filter((row): row is AssetRow => Boolean(row));

    const headers = viewConfig.value.columns.map((column) => column.label).join(',');
    const body = rows
      .map((row) => viewConfig.value.columns.map((column) => sanitizeCsvCell(row[column.key])).join(','))
      .join('\n');
    const blob = new Blob([`${headers}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${viewConfig.value.title}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    ElMessage.error('导出失败，请稍后重试');
  }
}

function handlePageChange(newPage: number) {
  page.value = newPage;
}

function handlePageSizeChange(newSize: number) {
  pageSize.value = newSize;
  page.value = 1;
}

watch([page, pageSize], () => {
  if (suppressReload.value) return;
  void loadAssets();
});

watch(keywordDebounced, () => {
  resetPageAndReload();
});

function matchesDefinition(record: AssetRecord, definition: AssetViewDefinition) {
  if (definition.source && record.source !== definition.source) {
    return false;
  }
  if (definition.assetTypes && definition.assetTypes.length) {
    const recordType = String(
      record.metadata?.asset_type || record.metadata?.category || record.metadata?.type || ''
    ).toLowerCase();
    if (recordType && !definition.assetTypes.map((t) => t.toLowerCase()).includes(recordType)) {
      return false;
    }
  }
  return true;
}

function statusTagType(status: string) {
  if (!status) return 'info';
  if (status === '可用') return 'success';
  if (status === '不可用') return 'danger';
  if (status === '未知') return 'info';
  if (status === '停用') return 'info';
  if (status === '生产') return 'success';
  if (status === '在建' || status === '挂起') return 'warning';
  if (status === '下线' || status === '中止或取消' || status.includes('中止') || status.includes('取消')) return 'info';
  if (status === '在线' || status === 'online') return 'success';
  if (status === '维护' || status === 'maintenance') return 'warning';
  if (status === '下线' || status === 'offline') return 'danger';
  if (status === 'success' || status === 'synced') return 'success';
  const text = String(status);
  if (text.includes('运行') || text.includes('正常') || text.includes('启用') || text.includes('上线')) return 'success';
  if (text.includes('维护') || text.includes('检修')) return 'warning';
  if (text.includes('停用') || text.includes('下线') || text.includes('终止') || text.includes('失败')) return 'danger';
  if (text.includes('测试') || text.includes('灰度') || text.includes('建设') || text.includes('开发') || text.includes('在研')) return 'warning';
  if (status === 'warning') return 'warning';
  if (status === 'error' || status === 'failed') return 'danger';
  return 'info';
}

type OnlineStatusCode = 'online' | 'maintenance' | 'offline' | '';

function normalizeOnlineStatusCode(value: unknown): OnlineStatusCode {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'online' : 'offline';
  if (typeof value === 'number') {
    if (value === 1) return 'online';
    if (value === 0) return 'offline';
    return '';
  }
  const text = String(value).trim();
  if (!text) return '';
  const lowered = text.toLowerCase();
  if (lowered === 'online' || lowered === 'up' || lowered === 'available' || lowered === 'true' || lowered === '1') return 'online';
  if (lowered === 'maintenance' || lowered === 'maint' || lowered === 'maintain') return 'maintenance';
  if (lowered === 'offline' || lowered === 'down' || lowered === 'unavailable' || lowered === 'false' || lowered === '0') return 'offline';
  if (text.includes('在线') || text.includes('可用') || text.includes('运行') || text.includes('上线')) return 'online';
  if (text.includes('维护') || text.includes('检修')) return 'maintenance';
  if (text.includes('下线') || text.includes('不可用') || text.includes('停用') || text.includes('停机')) return 'offline';
  return '';
}

function onlineStatusFromRecord(record: AssetRecord): OnlineStatusCode {
  const metadata = record.metadata || {};
  const direct = metadata.online_status ?? metadata.onlineStatus ?? metadata.online ?? metadata.availability;
  const directCode = normalizeOnlineStatusCode(direct);
  if (directCode) return directCode;

  const interfaceAvailable = metadata.interface_available_label ?? metadata.interface_available;
  const interfaceCode = normalizeOnlineStatusCode(interfaceAvailable);
  if (interfaceCode) return interfaceCode;

  const appStatus = metadata.app_status ?? metadata.status;
  const appCode = normalizeOnlineStatusCode(appStatus);
  if (appCode) return appCode;

  return '';
}

function onlineStatusLabel(code: OnlineStatusCode): string {
  if (code === 'online') return '在线';
  if (code === 'maintenance') return '维护';
  if (code === 'offline') return '下线';
  return '-';
}

function interfaceAvailabilityLabel(value: unknown): string {
  const code = normalizeInterfaceAvailabilityCode(value);
  if (code === 'available') return '可用';
  if (code === 'unavailable') return '不可用';
  if (code === 'unknown') return '未知';
  if (code === 'disabled') return '停用';
  const text = value == null ? '' : String(value).trim();
  return text || '-';
}

type InterfaceAvailabilityCode = 'available' | 'unavailable' | 'unknown' | 'disabled' | '';

function normalizeInterfaceAvailabilityCode(value: unknown): InterfaceAvailabilityCode {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'available' : 'unavailable';
  if (typeof value === 'number') {
    if (value === 1) return 'available';
    if (value === 2) return 'unavailable';
    if (value === 0) return 'unknown';
    return '';
  }
  const text = String(value).trim();
  if (!text || text === '-') return '';
  const lowered = text.toLowerCase();
  if (lowered === '1' || lowered === 'available' || lowered === 'up') return 'available';
  if (lowered === '2' || lowered === 'unavailable' || lowered === 'down') return 'unavailable';
  if (lowered === '0' || lowered === 'unknown') return 'unknown';
  if (lowered === 'disabled' || text.includes('停用')) return 'disabled';
  if (text.includes('不可用') || text.includes('不可达') || text.includes('异常')) return 'unavailable';
  if (text.includes('可用') || text.includes('正常')) return 'available';
  if (text.includes('未知')) return 'unknown';
  return '';
}

function isZabbixHostDisabled(record: AssetRecord, metadata: Record<string, any>): boolean {
  const raw =
    metadata.status ??
    metadata.host_status ??
    metadata.hostStatus ??
    metadata.enabled ??
    metadata.monitoring_status ??
    record.sync_status;
  if (raw === null || raw === undefined) return false;
  if (typeof raw === 'boolean') return !raw;
  if (typeof raw === 'number') return raw === 1;
  const text = String(raw).trim().toLowerCase();
  if (!text) return false;
  return text === '1' || text === 'disabled' || text.includes('停用');
}

function formatPeople(value: unknown): string {
  if (Array.isArray(value)) {
    const names = value
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          return item.name || item.username || item.id || '';
        }
        return '';
      })
      .filter(Boolean);
    if (names.length) return names.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

function formatContacts(value: unknown): string {
  if (Array.isArray(value)) {
    const contacts = value.map((item) => (typeof item === 'string' ? item : item?.id || item?.name)).filter(Boolean);
    if (contacts.length) return contacts.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

function formatArray(value: unknown): string {
  if (Array.isArray(value)) {
    const items = value.map((item) => (typeof item === 'string' ? item : item?.name || '')).filter(Boolean);
    if (items.length) return items.join('、');
  }
  if (typeof value === 'string') return value;
  return '-';
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
}

function sanitizeCsvCell(value: unknown): string {
  const text = value == null ? '' : String(value);
  if (text.includes(',') || text.includes('"')) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function networkTypeLabel(code: string) {
  if (code === 'internal') return '内网域名';
  if (code === 'internet') return '互联网域名';
  return code || '-';
}

function parseContactsInput(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item) => (item == null ? '' : String(item).trim()))
      .filter(Boolean);
  }
  return String(value)
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseListInput(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value
      .map((item) => (item == null ? '' : String(item).trim()))
      .filter(Boolean);
  }
  return String(value)
    .split(/[,，\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function isExcelFile(file: File) {
  const name = file.name.toLowerCase();
  if (name.endsWith('.xlsx') || name.endsWith('.xls')) return true;
  if (file.type && file.type.includes('spreadsheet')) return true;
  return false;
}

function extractWorkbookRows(buffer: ArrayBuffer, headers: string[]): Record<string, string>[] {
  const workbook = XLSX.read(buffer, { type: 'array' });
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) return [];
  const sheet = workbook.Sheets[sheetName];
  const json = XLSX.utils.sheet_to_json<Record<string, any>>(sheet, { defval: '' });
  void headers;
  return json.map((row) => {
    const mapped: Record<string, string> = {};
    Object.entries(row || {}).forEach(([key, value]) => {
      const normalizedKey = normalizeHeaderKey(key);
      if (!normalizedKey) return;
      mapped[normalizedKey] = value == null ? '' : String(value).trim();
    });
    return mapped;
  });
}

function decodeTextBuffer(buffer: ArrayBuffer): string {
  const attempts: Array<{ label: string; fatal?: boolean }> = [
    { label: 'utf-8', fatal: true },
    { label: 'utf-16le', fatal: true },
    { label: 'utf-16be', fatal: true },
    { label: 'gb18030' }
  ];
  for (const attempt of attempts) {
    try {
      const decoder = new TextDecoder(attempt.label as any, { fatal: attempt.fatal ?? false });
      return decoder.decode(buffer);
    } catch (error) {
      continue;
    }
  }
  return new TextDecoder().decode(buffer);
}

function parseCsvContent(content: string, expectedHeaders: string[]): Record<string, string>[] {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) return [];
  void expectedHeaders;
  const delimiter = detectDelimiter(lines[0]);
  const headerCells = splitSeparatedLine(lines[0], delimiter).map((cell) => normalizeHeaderKey(cell));
  const rows: Record<string, string>[] = [];
  lines.slice(1).forEach((line) => {
    const row: Record<string, string> = {};
    const cells = splitSeparatedLine(line, delimiter);
    headerCells.forEach((header, idx) => {
      const key = header.trim();
      if (!key) return;
      row[key] = (cells[idx] ?? '').trim();
    });
    rows.push(row);
  });
  return rows;
}

function detectDelimiter(line: string): string {
  const candidates = ['\t', ';', ','] as const;
  let best: string = ',';
  let bestCount = -1;
  for (const delimiter of candidates) {
    const count = countDelimiterOutsideQuotes(line, delimiter);
    if (count > bestCount) {
      bestCount = count;
      best = delimiter;
    }
  }
  return best;
}

function splitSeparatedLine(line: string, delimiter: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === delimiter && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

function countDelimiterOutsideQuotes(line: string, delimiter: string): number {
  let inQuotes = false;
  let count = 0;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        i += 1;
        continue;
      }
      inQuotes = !inQuotes;
      continue;
    }
    if (!inQuotes && char === delimiter) count += 1;
  }
  return count;
}

function normalizeHeaderKey(value: unknown): string {
  if (value == null) return '';
  return String(value)
    .replace(/^\uFEFF/, '')
    .replace(/\u3000/g, ' ')
    .trim();
}

	function isRowEmpty(row: Record<string, string>): boolean {
	  const values = Object.values(row || {});
	  if (!values.length) return true;
	  return values.every((value) => !String(value ?? '').trim());
	}

	function formatImportServerErrors(items: Array<{ index: number; errors: Record<string, unknown> }>): string[] {
	  const lines: string[] = [];
	  const maxLines = 50;
	  const sorted = [...items].sort((a, b) => (a?.index ?? 0) - (b?.index ?? 0));

	  sorted.slice(0, maxLines).forEach((item) => {
	    const rowNo = (item?.index ?? 0) + 1;
	    const messages = formatFieldErrors(item?.errors);
	    lines.push(`第 ${rowNo} 条：${messages || '导入失败'}`);
	  });

	  if (sorted.length > maxLines) {
	    lines.push(`还有 ${sorted.length - maxLines} 条错误未展示`);
	  }

	  return lines;
	}

	function formatFieldErrors(value: unknown): string {
	  if (!value || typeof value !== 'object') return '';
	  const entries = Object.entries(value as Record<string, unknown>);
	  const parts: string[] = [];
	  entries.forEach(([field, detail]) => {
	    const message = normalizeErrorMessage(detail);
	    if (!message) return;
	    if (!field || field === 'non_field_errors' || field === 'detail') {
	      parts.push(message);
	      return;
	    }
	    parts.push(`${field}：${message}`);
	  });
	  return parts.join('；');
	}

	function normalizeErrorMessage(detail: unknown): string {
	  if (!detail) return '';
	  if (typeof detail === 'string') return detail;
	  if (Array.isArray(detail)) {
	    const texts = detail.map((item) => normalizeErrorMessage(item)).filter(Boolean);
	    return texts.join('，');
	  }
	  if (typeof detail === 'object') {
	    const maybeMessage = (detail as any)?.message ?? (detail as any)?.detail;
	    if (typeof maybeMessage === 'string') return maybeMessage;
	  }
	  return String(detail);
	}

	function stableSortBy<T>(
	  values: T[],
	  selector: (value: T) => string,
	  compare: (a: string, b: string) => number
): T[] {
  return values
    .map((value, index) => ({ value, index, key: selector(value) }))
    .sort((left, right) => {
      const result = compare(left.key, right.key);
      if (result !== 0) return result;
      return left.index - right.index;
    })
    .map((entry) => entry.value);
}

function normalizeAppCode(value: unknown): string {
  const text = value == null ? '' : String(value).trim();
  if (!text || text === '-') return '';
  return text;
}

function compareAppCodeAsc(a: string, b: string): number {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  const aMatch = /^([A-Za-z]+)?(\d+)?$/.exec(a);
  const bMatch = /^([A-Za-z]+)?(\d+)?$/.exec(b);
  const aPrefix = (aMatch?.[1] || '').toUpperCase();
  const bPrefix = (bMatch?.[1] || '').toUpperCase();
  if (aPrefix !== bPrefix) return aPrefix.localeCompare(bPrefix);
  const aNumRaw = aMatch?.[2];
  const bNumRaw = bMatch?.[2];
  if (aNumRaw && bNumRaw) {
    const aNum = Number(aNumRaw);
    const bNum = Number(bNumRaw);
    if (Number.isFinite(aNum) && Number.isFinite(bNum) && aNum !== bNum) return aNum - bNum;
  }
  return a.localeCompare(b);
}

onMounted(() => {
  loadAssets();
});
</script>

<style scoped>
:deep(.page-panel__body) {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
}

:deep(.page-panel__footer) {
  border-top: none;
  background: var(--oa-bg-panel);
  padding: 0 16px 0px;
}

.asset-filters,
.asset-table {
  padding-left: 16px;
  padding-right: 16px;
  background: var(--oa-bg-panel);
}

.asset-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 16px;
  padding-bottom: 16px;
  margin: 0;
  border-bottom: 1px solid var(--oa-border-light);
}

.filters-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-left: auto;
}

.toolbar-button {
  border-radius: 6px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

.toolbar-button--primary {
  box-shadow: none;
}

.search-input {
  flex: 1;
  min-width: 220px;
}

.search-input--compact {
  max-width: 320px;
}

.narrow-select {
  width: 180px;
}

.pill-input :deep(.el-input__wrapper),
.pill-input :deep(.el-select__wrapper) {
  border-radius: 999px;
  padding-left: 0.85rem;
  background: var(--oa-filter-control-bg);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

.asset-table {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  padding-top: 0;
  padding-bottom: 12px;
}

.asset-table__card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.asset-table__card :deep(.el-table) {
  flex: 1;
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.asset-table__card :deep(.el-table__body-wrapper),
.asset-table__card :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.asset-table__card--x-scroll :deep(.el-table__body-wrapper),
.asset-table__card--x-scroll :deep(.el-scrollbar__wrap) {
  overflow-x: auto;
}

.asset-table__card :deep(.el-table__inner-wrapper) {
  border-left: none !important;
  border-right: none !important;
}

.asset-table__card :deep(.el-table__cell) {
  padding: 8px 10px;
}

.table-empty {
  padding: 2rem;
  text-align: center;
  color: var(--oa-text-secondary);
}

.asset-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.asset-stats {
  color: var(--oa-text-secondary);
  font-size: 13px;
}

.import-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1rem 0;
}

.upload-input {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border: 1px dashed var(--oa-border-light);
  border-radius: 6px;
  color: var(--oa-color-primary);
  cursor: pointer;
}

.upload-input input {
  display: none;
}

.import-errors {
  margin-top: 1rem;
}

.import-errors ul {
  margin: 0.5rem 0 0;
  padding-left: 1.2rem;
}

.create-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
