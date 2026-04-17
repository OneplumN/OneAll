import type {
  AssetCreatePayload,
  AssetRecord,
  AssetTypeSummary,
} from '@/features/assets/api/assetsApi';

export interface AssetTypeState {
  types: AssetTypeSummary[];
}

export interface AssetRow {
  id: string;
  [key: string]: any;
}

export type AssetViewKey =
  | 'cmdb-domain'
  | 'zabbix-host'
  | 'ipmp-project'
  | 'workorder-host';

export interface AssetColumn {
  key: string;
  label: string;
  width?: number | string;
  minWidth?: number | string;
  type?: 'status';
  isUnique?: boolean;
}

export interface AssetFormFieldOption {
  label: string;
  value: string;
}

export interface AssetFormField {
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

export interface ImportTemplateColumn {
  key: string;
  label: string;
  required?: boolean;
  sample?: string;
}

export interface ImportTemplate {
  columns: ImportTemplateColumn[];
  mapRow(row: Record<string, string>): Record<string, any>;
}

export interface AssetViewDefinition {
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

export type OnlineStatusCode = 'online' | 'maintenance' | 'offline' | '';

export type InterfaceAvailabilityCode =
  | 'available'
  | 'unavailable'
  | 'unknown'
  | 'disabled'
  | '';
