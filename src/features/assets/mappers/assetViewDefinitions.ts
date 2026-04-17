import type {
  AssetCreatePayload,
  AssetRecord,
} from '@/features/assets/api/assetsApi';
import { parseContactsInput, parseListInput } from '@/features/assets/utils/importParsing';
import {
  formatArray,
  formatContacts,
  formatDate,
  formatPeople,
  formatSyncStatus,
  interfaceAvailabilityLabel,
  isZabbixHostDisabled,
  networkTypeLabel,
  normalizeOnlineStatusCode,
  onlineStatusFromRecord,
  onlineStatusLabel,
} from '@/features/assets/utils/assetHelpers';
import type {
  AssetRow,
  AssetViewDefinition,
  AssetViewKey,
} from '@/features/assets/types/assetCenter';

export const ROUTE_VIEW_KEY: Record<string, AssetViewKey> = {
  'assets-domain': 'cmdb-domain',
  'integrations-assets-domain': 'cmdb-domain',
  'assets-zabbix': 'zabbix-host',
  'integrations-assets-zabbix': 'zabbix-host',
  'assets-ipmp': 'ipmp-project',
  'integrations-assets-ipmp': 'ipmp-project',
  'assets-workorder-hosts': 'workorder-host',
  'integrations-assets-workorder-hosts': 'workorder-host',
};

export const ASSET_VIEW_DEFINITIONS: Record<AssetViewKey, AssetViewDefinition> = {
  'cmdb-domain': {
    title: 'CMDB 域名',
    description: '汇聚 CMDB 域名资产，展示所属系统、网络类型及责任人。',
    source: 'CMDB',
    assetTypes: ['cmdb-domain', 'domain'],
    pluginType: 'asset_cmdb_domain',
    integrationInfo: {
      summary:
        '从 CMDB 同步域名清单，可通过 ASSET_SYNC_CMDB_FILE 指定样例或脚本输出文件。',
      envVar: 'ASSET_SYNC_CMDB_FILE',
      note: '脚本运行后生成的 JSON 列表会被自动解析写入资产库。',
    },
    filters: { networkType: true },
    columns: [
      { key: 'domain', label: '域名', minWidth: 220 },
      { key: 'system_name', label: '所属系统', minWidth: 200 },
      { key: 'network_type', label: '互联网类型', width: 160 },
      { key: 'owner', label: '负责人', width: 140 },
      {
        key: 'alert_contacts',
        label: '告警联系人（工号）',
        minWidth: 200,
      },
    ],
    formFields: [
      {
        key: 'domain',
        label: '域名',
        component: 'input',
        required: true,
        placeholder: '例如 https://oneall.com',
      },
      {
        key: 'system_name',
        label: '所属系统',
        component: 'input',
        required: true,
        placeholder: '请输入系统名称',
      },
      {
        key: 'network_type',
        label: '互联网类型',
        component: 'select',
        required: true,
        options: [
          { label: '内网域名', value: 'internal' },
          { label: '互联网域名', value: 'internet' },
        ],
        default: 'internet',
      },
      {
        key: 'owner',
        label: '负责人',
        component: 'input',
        placeholder: '负责人姓名',
      },
      {
        key: 'alert_contacts',
        label: '告警联系人（工号）',
        component: 'input',
        placeholder: '000123,000456',
      },
    ],
    importTemplate: {
      columns: [
        {
          key: 'domain',
          label: '域名',
          required: true,
          sample: 'https://oneall.cn',
        },
        {
          key: 'system_name',
          label: '所属系统',
          required: true,
          sample: 'OneAll 平台',
        },
        {
          key: 'network_type',
          label: '互联网类型',
          sample: 'internet',
        },
        { key: 'owner', label: '负责人', sample: '张三' },
        {
          key: 'alert_contacts',
          label: '告警联系人（工号）',
          sample: '000123,000456',
        },
      ],
      mapRow: (row) => ({
        domain: row.domain || '',
        system_name: row.system_name || '',
        network_type: row.network_type || 'internet',
        owner: row.owner || '',
        alert_contacts: row.alert_contacts || '',
      }),
    },
    transform(record: AssetRecord) {
      const metadata = record.metadata || {};
      const networkCode = metadata.network_type || metadata.internet_type || '';
      const row: AssetRow = {
        id: record.id,
        domain: metadata.domain || record.name,
        system_name: metadata.system_name || record.system_name || '-',
        network_type: networkTypeLabel(networkCode),
        network_code: networkCode,
        owner: formatPeople(metadata.owner || metadata.owner_name || record.owners),
        alert_contacts: formatContacts(
          metadata.alert_contacts || record.contacts
        ),
        sync_status: formatSyncStatus(record.sync_status),
        created_at: formatDate(record.created_at),
        updated_at: formatDate(record.updated_at),
      };
      return row;
    },
    buildPayload(form: Record<string, any>): AssetCreatePayload {
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
    },
  },
  'zabbix-host': {
    title: 'Zabbix 主机',
    description: '同步 Zabbix 主机资产，展示 IP、主机组与 Proxy 信息。',
    source: 'Zabbix',
    assetTypes: ['zabbix-host'],
    pluginType: 'asset_zabbix_host',
    integrationInfo: {
      summary:
        'Zabbix 采集脚本输出主机列表，可通过 ASSET_SYNC_ZABBIX_FILE 覆盖默认样例。',
      envVar: 'ASSET_SYNC_ZABBIX_FILE',
    },
    columns: [
      { key: 'ip', label: 'IP 地址', minWidth: 160 },
      { key: 'host_name', label: '主机名称', minWidth: 200 },
      { key: 'visible_name', label: '可见名称', minWidth: 200 },
      { key: 'host_group', label: '主机群组', minWidth: 220 },
      { key: 'proxy', label: 'Proxy', minWidth: 160 },
      { key: 'interface_type', label: '接口类型', width: 140 },
      {
        key: 'interface_available',
        label: '接口可用性',
        width: 160,
        type: 'status',
      },
    ],
    formFields: [
      {
        key: 'ip',
        label: 'IP 地址',
        component: 'input',
        required: true,
        placeholder: '例如 10.0.0.5',
      },
      {
        key: 'host_name',
        label: '主机名称',
        component: 'input',
        required: true,
        placeholder: '主机显示名称',
      },
      {
        key: 'host_group',
        label: '主机群组',
        component: 'input',
        placeholder: '多个群组用逗号分隔',
      },
      {
        key: 'proxy',
        label: 'Proxy',
        component: 'input',
        placeholder: 'proxy 名称或 IP',
      },
    ],
    transform(record: AssetRecord) {
      const metadata = record.metadata || {};
      const hostDisabled = isZabbixHostDisabled(record, metadata);
      const interfaceAvailable = interfaceAvailabilityLabel(
        hostDisabled
          ? '停用'
          : metadata.interface_available_label ?? metadata.interface_available
      );
      return {
        id: record.id,
        ip: metadata.ip || metadata.host_ip || metadata.primary_ip || '-',
        host_name: metadata.host_name || record.name,
        visible_name: metadata.visible_name || record.name || '-',
        host_group: formatArray(metadata.host_groups || metadata.groups),
        proxy: metadata.proxy || metadata.proxy_name || '-',
        interface_type:
          metadata.interface_type_label || metadata.interface_type || '-',
        interface_available: interfaceAvailable,
        sync_status: formatSyncStatus(record.sync_status),
        created_at: formatDate(record.created_at),
        updated_at: formatDate(record.updated_at),
      };
    },
    buildPayload(form: Record<string, any>): AssetCreatePayload {
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
    },
  },
  'ipmp-project': {
    title: 'IPMP 项目',
    description: '展示 IPMP 项目信息，包括应用编号、状态与责任人。',
    source: 'IPMP',
    assetTypes: ['ipmp-project'],
    pluginType: 'asset_ipmp_project',
    integrationInfo: {
      summary:
        'IPMP 接口同步的应用档案，可通过 ASSET_SYNC_IPMP_FILE 指定脚本输出。',
      envVar: 'ASSET_SYNC_IPMP_FILE',
    },
    columns: [
      { key: 'app_code', label: '应用编号', minWidth: 160 },
      { key: 'app_name_cn', label: '应用中文名称', minWidth: 200 },
      { key: 'app_name_en', label: '应用英文简称', minWidth: 180 },
      { key: 'app_status', label: '应用状态', minWidth: 140, type: 'status' },
      { key: 'owner', label: '系统负责人', minWidth: 160 },
      { key: 'security_level', label: '等保级别', minWidth: 160 },
      { key: 'system_origin', label: '系统归属', minWidth: 160 },
    ],
    importTemplate: {
      columns: [
        {
          key: 'app_code',
          label: '应用编号',
          required: true,
          sample: 'APP-OPS-001',
        },
        {
          key: 'app_name_cn',
          label: '应用中文名称',
          required: true,
          sample: 'OneAll 运维门户',
        },
        {
          key: 'app_name_en',
          label: '应用英文简称',
          sample: 'OneAll Ops',
        },
        { key: 'app_status', label: '应用状态', sample: '运行中' },
        { key: 'owner', label: '系统负责人', sample: '王五' },
        { key: 'security_level', label: '等保级别', sample: '二级' },
        { key: 'system_origin', label: '系统归属', sample: '自研' },
      ],
      mapRow: (row) => ({
        app_code: row.app_code || row['应用编号'] || '',
        app_name_cn: row.app_name_cn || row['应用中文名称'] || '',
        app_name_en: row.app_name_en || row['应用英文简称'] || '',
        app_status: row.app_status || row['应用状态'] || '',
        owner: row.owner || row['系统负责人'] || '',
        security_level:
          row.security_level || row['系统等级保护定级级别'] || '',
        system_origin: row.system_origin || row['系统归属'] || '',
      }),
    },
    formFields: [
      { key: 'app_code', label: '应用编号', component: 'input', required: true },
      {
        key: 'app_name_cn',
        label: '应用中文名称',
        component: 'input',
        required: true,
      },
      { key: 'app_name_en', label: '应用英文简称', component: 'input' },
      {
        key: 'app_status',
        label: '应用状态',
        component: 'input',
        placeholder: '在研/上线等',
      },
      { key: 'owner', label: '系统负责人', component: 'input' },
      { key: 'security_level', label: '等保级别', component: 'input' },
      { key: 'system_origin', label: '系统归属', component: 'input' },
    ],
    transform(record: AssetRecord) {
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
        sync_status: formatSyncStatus(record.sync_status),
        created_at: formatDate(record.created_at),
        updated_at: formatDate(record.updated_at),
      };
    },
    buildPayload(form: Record<string, any>): AssetCreatePayload {
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
    },
  },
  'workorder-host': {
    title: '工单纳管主机信息',
    description:
      '展示工单纳管主机的 IP、机房、Proxy、端口及联系人信息。',
    source: 'Manual',
    assetTypes: ['workorder-host', 'workorder'],
    pluginType: 'asset_workorder_host',
    integrationInfo: {
      summary:
        '手工或 ITSM 脚本纳管的探针主机列表，可通过 ASSET_SYNC_WORKORDER_FILE 提供数据。',
      envVar: 'ASSET_SYNC_WORKORDER_FILE',
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
      { key: 'owner', label: '系统负责人', minWidth: 160 },
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
        { key: 'owner', label: '系统负责人', sample: '陈七' },
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
        owner: row.owner || '',
      }),
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
          { label: '下线', value: 'offline' },
        ],
        default: 'online',
      },
      { key: 'idc', label: '所在机房', component: 'input' },
      { key: 'proxy', label: '接入 ITSI Proxy', component: 'input' },
      {
        key: 'port',
        label: '端口',
        component: 'number',
        min: 1,
        max: 65535,
        step: 1,
      },
      {
        key: 'alert_contacts',
        label: '告警联系人',
        component: 'input',
        placeholder: '000123,000456',
      },
      { key: 'hostname', label: 'Hostname', component: 'input' },
      { key: 'app_system', label: '应用系统', component: 'input' },
      { key: 'owner', label: '系统负责人', component: 'input' },
    ],
    transform(record: AssetRecord) {
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
        sync_status: formatSyncStatus(record.sync_status),
        created_at: formatDate(record.created_at),
        updated_at: formatDate(record.updated_at),
      };
    },
    buildPayload(form: Record<string, any>): AssetCreatePayload {
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
    },
  },
};
