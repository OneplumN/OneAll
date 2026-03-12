<template>
  <RepositoryPageShell root-title="统计分析" section-title="资产监控治理">
    <template #actions>
      <el-button class="toolbar-button" type="primary" :loading="loading" @click="loadData">刷新</el-button>
    </template>

    <div class="content">
      <el-alert
        type="info"
        show-icon
        :closable="false"
        title="口径说明：IPMP 系统名称按“中文名-英文名”拼接，并与 Zabbix 主机群组名称匹配。"
      />

      <el-card shadow="never">
        <template #header><span>概览</span></template>
        <el-descriptions :column="4">
          <el-descriptions-item label="IPMP 系统数">{{ data.summary.ipmp_total }}</el-descriptions-item>
          <el-descriptions-item label="Zabbix 主机数">{{ data.summary.zabbix_host_total }}</el-descriptions-item>
          <el-descriptions-item label="工单台账主机数">{{ data.summary.workorder_host_total }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatDateTime(data.generated_at) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never">
        <template #header><span>系统覆盖（工单 / 监控）</span></template>
        <el-tabs v-model="coverageTab">
          <el-tab-pane label="监控覆盖（Zabbix ↔ IPMP）" name="zabbix">
            <el-row :gutter="12">
              <el-col :span="10">
                <BaseChart :option="coverageOption" :height="220" />
              </el-col>
              <el-col :span="14">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">覆盖率</div>
                      <div class="kpi-value">{{ formatPercent(data.zabbix_coverage.monitored_rate || data.ipmp_coverage.monitored_rate) }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">总数</div>
                      <div class="kpi-value">{{ data.zabbix_coverage.total || data.ipmp_coverage.total }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">已覆盖</div>
                      <div class="kpi-value">{{ data.zabbix_coverage.monitored || data.ipmp_coverage.monitored }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">未覆盖</div>
                      <div class="kpi-value danger">{{ data.zabbix_coverage.uncovered || data.ipmp_coverage.uncovered }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-col>
            </el-row>

            <el-divider />

            <el-table :data="data.zabbix_coverage.uncovered_items.length ? data.zabbix_coverage.uncovered_items : data.ipmp_coverage.uncovered_items" style="width: 100%" height="360">
              <el-table-column prop="app_code" label="应用编号" width="140" />
              <el-table-column prop="display_name" label="系统（中文-英文）" min-width="240" show-overflow-tooltip />
              <el-table-column prop="app_status" label="应用状态" width="140">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain" :type="statusTagType(row.app_status)">
                    {{ row.app_status || '-' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
              <el-table-column prop="security_level" label="等保级别" width="140" show-overflow-tooltip />
              <el-table-column prop="system_origin" label="系统归属" width="140" show-overflow-tooltip />
            </el-table>
            <el-empty
              v-if="!(data.zabbix_coverage.uncovered_items.length || data.ipmp_coverage.uncovered_items.length)"
              description="暂无未覆盖系统"
            />
          </el-tab-pane>

          <el-tab-pane label="工单覆盖（工单 ↔ IPMP）" name="ledger" lazy>
            <el-row :gutter="12">
              <el-col :span="10">
                <BaseChart :option="ledgerCoverageOption" :height="220" />
              </el-col>
              <el-col :span="14">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">纳管率</div>
                      <div class="kpi-value">{{ formatPercent(workorderCoverage.covered_rate) }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">总数</div>
                      <div class="kpi-value">{{ workorderCoverage.total }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">已纳管</div>
                      <div class="kpi-value">{{ workorderCoverage.covered }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">未纳管</div>
                      <div class="kpi-value warning">{{ workorderCoverage.uncovered }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-col>
            </el-row>

            <el-divider />

            <el-table :data="workorderCoverage.uncovered_items" style="width: 100%" height="360">
              <el-table-column prop="app_code" label="应用编号" width="140" />
              <el-table-column prop="display_name" label="系统（中文-英文）" min-width="240" show-overflow-tooltip />
              <el-table-column prop="app_status" label="应用状态" width="140">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain" :type="statusTagType(row.app_status)">
                    {{ row.app_status || '-' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
              <el-table-column prop="security_level" label="等保级别" width="140" show-overflow-tooltip />
              <el-table-column prop="system_origin" label="系统归属" width="140" show-overflow-tooltip />
            </el-table>
            <el-empty v-if="!workorderCoverage.uncovered_items.length" description="暂无未纳管系统" />
          </el-tab-pane>

          <el-tab-pane label="交叉矩阵（4象限）" name="matrix" lazy>
            <el-row :gutter="12">
              <el-col :span="10">
                <BaseChart :option="matrixOption" :height="220" />
              </el-col>
              <el-col :span="14">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">工单+监控</div>
                      <div class="kpi-value">{{ data.coverage_matrix.counts.both }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="kpi">
                      <div class="kpi-label">有工单无监控</div>
                      <div class="kpi-value warning">{{ data.coverage_matrix.counts.ledger_only }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">有监控无工单</div>
                      <div class="kpi-value danger">{{ data.coverage_matrix.counts.zabbix_only }}</div>
                    </div>
                  </el-col>
                  <el-col :span="12" style="margin-top: 12px">
                    <div class="kpi">
                      <div class="kpi-label">两边都无</div>
                      <div class="kpi-value">{{ data.coverage_matrix.counts.neither }}</div>
                    </div>
                  </el-col>
                </el-row>
              </el-col>
            </el-row>

            <el-divider />

            <el-tabs v-model="matrixTab">
              <el-tab-pane label="有工单无监控" name="ledger_only" lazy>
                <el-table :data="data.coverage_matrix.items.ledger_only" style="width: 100%" height="320">
                  <el-table-column prop="app_code" label="应用编号" width="140" />
                  <el-table-column prop="display_name" label="系统（中文-英文）" min-width="240" show-overflow-tooltip />
                  <el-table-column prop="app_status" label="应用状态" width="140">
                    <template #default="{ row }">
                      <el-tag size="small" effect="plain" :type="statusTagType(row.app_status)">
                        {{ row.app_status || '-' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="有监控无工单" name="zabbix_only" lazy>
                <el-table :data="data.coverage_matrix.items.zabbix_only" style="width: 100%" height="320">
                  <el-table-column prop="app_code" label="应用编号" width="140" />
                  <el-table-column prop="display_name" label="系统（中文-英文）" min-width="240" show-overflow-tooltip />
                  <el-table-column prop="app_status" label="应用状态" width="140">
                    <template #default="{ row }">
                      <el-tag size="small" effect="plain" :type="statusTagType(row.app_status)">
                        {{ row.app_status || '-' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="两边都无" name="neither" lazy>
                <el-table :data="data.coverage_matrix.items.neither" style="width: 100%" height="320">
                  <el-table-column prop="app_code" label="应用编号" width="140" />
                  <el-table-column prop="display_name" label="系统（中文-英文）" min-width="240" show-overflow-tooltip />
                  <el-table-column prop="app_status" label="应用状态" width="140">
                    <template #default="{ row }">
                      <el-tag size="small" effect="plain" :type="statusTagType(row.app_status)">
                        {{ row.app_status || '-' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </el-tab-pane>
        </el-tabs>

      </el-card>

      <el-card shadow="never">
        <template #header><span>工单 vs Zabbix（按 IP 对齐）</span></template>

        <el-row :gutter="12" class="kpi-row">
          <el-col :span="10">
            <BaseChart :option="reconcileOption" :height="220" />
          </el-col>
          <el-col :span="14">
            <el-row :gutter="12">
              <el-col :span="12">
                <div class="kpi">
                  <div class="kpi-label">匹配</div>
                  <div class="kpi-value">{{ data.ip_reconcile.matched_by_ip }}</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="kpi">
                  <div class="kpi-label">工单缺失监控</div>
                  <div class="kpi-value danger">{{ data.ip_reconcile.missing_in_zabbix }}</div>
                </div>
              </el-col>
              <el-col :span="12" style="margin-top: 12px">
                <div class="kpi">
                  <div class="kpi-label">监控未入工单</div>
                  <div class="kpi-value warning">{{ data.ip_reconcile.extra_in_zabbix }}</div>
                </div>
              </el-col>
              <el-col :span="12" style="margin-top: 12px">
                <div class="kpi">
                  <div class="kpi-label">Zabbix IP 冲突</div>
                  <div class="kpi-value warning">{{ data.ip_reconcile.zabbix_ip_conflicts }}</div>
                </div>
              </el-col>
            </el-row>
          </el-col>
        </el-row>

        <el-divider />

        <el-tabs v-model="reconcileTab">
          <el-tab-pane label="工单缺失监控" name="missing">
            <el-table :data="data.ip_reconcile.missing_in_zabbix_items" style="width: 100%" height="320">
              <el-table-column prop="ip" label="IP" width="160" />
              <el-table-column prop="hostname" label="Hostname" width="200" />
              <el-table-column prop="system_name" label="系统" min-width="240" show-overflow-tooltip />
              <el-table-column prop="owner" label="负责人" width="140" show-overflow-tooltip />
            </el-table>
            <el-empty v-if="!data.ip_reconcile.missing_in_zabbix_items.length" description="暂无缺失项" />
          </el-tab-pane>
          <el-tab-pane label="监控未入工单" name="extra">
            <el-table :data="data.ip_reconcile.extra_in_zabbix_items" style="width: 100%" height="320">
              <el-table-column prop="ip" label="IP" width="160" />
              <el-table-column label="主机" min-width="520">
                <template #default="{ row }">
                  <div v-for="host in row.hosts" :key="host.host_name" class="host-line">
                    <span class="host-name">{{ host.host_name || '-' }}</span>
                    <span class="host-meta">（{{ host.visible_name || '-' }} / {{ host.proxy || '-' }} / {{ host.availability || '-' }}）</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!data.ip_reconcile.extra_in_zabbix_items.length" description="暂无额外监控项" />
          </el-tab-pane>
          <el-tab-pane label="Zabbix IP 冲突" name="conflict">
            <el-table :data="data.ip_reconcile.zabbix_ip_conflict_items" style="width: 100%" height="320">
              <el-table-column prop="ip" label="IP" width="160" />
              <el-table-column label="冲突主机" min-width="520">
                <template #default="{ row }">
                  <div v-for="host in row.hosts" :key="host.host_name" class="host-line">
                    <span class="host-name">{{ host.host_name || '-' }}</span>
                    <span class="host-meta">（{{ host.visible_name || '-' }} / {{ host.proxy || '-' }}）</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!data.ip_reconcile.zabbix_ip_conflict_items.length" description="暂无冲突项" />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <el-card shadow="never">
        <template #header><span>Proxy 维度（主机数 / 可用性）</span></template>
        <div class="proxy-toolbar">
          <el-input v-model="proxyKeyword" placeholder="搜索 Proxy（支持模糊匹配）" clearable style="max-width: 360px" />
          <el-checkbox v-model="proxyOnlyAbnormal">仅显示异常（不可用/未知>0）</el-checkbox>
          <el-button v-if="canManage" plain @click="openProxyMappingDialog">维护映射</el-button>
          <div class="proxy-toolbar-right">
            <span class="proxy-toolbar-label">Top</span>
            <el-select v-model="proxyTopN" style="width: 120px">
              <el-option :value="10" label="10" />
              <el-option :value="20" label="20" />
              <el-option :value="50" label="50" />
              <el-option :value="0" label="全部" />
            </el-select>
            <el-switch v-model="proxyMergeOther" active-text="合并其他" inactive-text="不合并" />
          </div>
        </div>
        <BaseChart :option="proxyOption" :height="320" />
        <el-divider />
        <el-table :data="proxyTableData" style="width: 100%" height="360">
          <el-table-column label="Proxy" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ proxyLabel(row.proxy) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="total" label="总数" width="120" />
          <el-table-column prop="available" label="可用" width="120" />
          <el-table-column prop="unavailable" label="不可用" width="120" />
          <el-table-column prop="unknown" label="未知" width="120" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openProxyDetail(row.proxy)">明细</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!proxyTableData.length" description="暂无 Proxy 数据" />
      </el-card>

      <el-drawer v-model="proxyDetailVisible" :title="`Proxy 明细：${proxyLabel(proxyDetailProxy)}`" size="860px">
        <div class="proxy-detail-toolbar">
          <el-input
            v-model="proxyDetailKeyword"
            placeholder="搜索（IP/主机名/可见名/群组）"
            clearable
            style="max-width: 360px"
          />
          <el-checkbox v-model="proxyDetailOnlyAbnormal">仅看异常（不可用/未知）</el-checkbox>
        </div>

        <el-row :gutter="12" style="margin-bottom: 12px">
          <el-col :span="6">
            <div class="kpi">
              <div class="kpi-label">主机数</div>
              <div class="kpi-value">{{ proxyDetail.summary.host_total }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="kpi">
              <div class="kpi-label">异常主机</div>
              <div class="kpi-value danger">{{ proxyDetail.summary.abnormal_host_total }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="kpi">
              <div class="kpi-label">IP 数</div>
              <div class="kpi-value">{{ proxyDetail.summary.ip_total }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="kpi">
              <div class="kpi-label">IP 冲突</div>
              <div class="kpi-value warning">{{ proxyDetail.summary.conflict_ip_total }}</div>
            </div>
          </el-col>
        </el-row>

        <el-table :data="proxyDetail.items" v-loading="proxyDetailLoading" style="width: 100%" height="520">
          <el-table-column type="expand" width="44">
            <template #default="{ row }">
              <div v-for="host in row.hosts" :key="host.external_id || host.host_name" class="host-line">
                <span class="host-name">{{ host.host_name || '-' }}</span>
                <span class="host-meta">
                  （{{ host.visible_name || '-' }} / {{ host.availability || '-' }} / {{ (host.groups || []).join(', ') || '-' }} / {{ proxyLabel(host.proxy || '') }}）
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="ip" label="IP" width="180" />
          <el-table-column prop="host_count" label="主机数" width="100" />
          <el-table-column prop="abnormal_count" label="异常" width="100" />
        </el-table>

        <div style="margin-top: 12px; display: flex; justify-content: flex-end">
          <el-pagination
            :current-page="proxyDetailPage"
            :page-size="proxyDetailPageSize"
            :total="proxyDetail.pagination.total"
            layout="prev, pager, next, total"
            @current-change="onProxyDetailPageChange"
          />
        </div>
      </el-drawer>

      <el-dialog v-model="proxyMappingDialogVisible" title="Proxy 映射维护（英文 -> 中文）" width="860px">
        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="说明：中文名称用于展示与报表，不会改动 Zabbix 原始数据；清空中文名称并保存可删除映射。"
          style="margin-bottom: 12px"
        />
        <el-table :data="proxyMappingDraft" style="width: 100%" height="520">
          <el-table-column prop="proxy" label="Proxy 编码" width="220" show-overflow-tooltip />
          <el-table-column label="中文名称" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input v-model="row.display_name" placeholder="例如：廊坊机房 ITSI Proxy 2" clearable />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input v-model="row.remark" placeholder="可选" clearable />
            </template>
          </el-table-column>
        </el-table>
        <template #footer>
          <div style="display: flex; justify-content: space-between; width: 100%">
            <el-button plain @click="loadProxyMappings">刷新映射</el-button>
            <div style="display: flex; gap: 8px">
              <el-button @click="proxyMappingDialogVisible = false">取消</el-button>
              <el-button type="primary" :loading="proxyMappingSaving" @click="saveProxyMappings">保存</el-button>
            </div>
          </div>
        </template>
      </el-dialog>
    </div>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed, reactive, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import type { EChartsOption } from 'echarts';

import BaseChart from '@/components/BaseChart.vue';
import RepositoryPageShell from '@/components/RepositoryPageShell.vue';
import { fetchAssetGovernanceOverview, fetchAssetProxyHosts, type AssetGovernanceOverview, type AssetProxyHostsResponse } from '@/services/assetGovernanceApi';
import { fetchProxyMappings, upsertProxyMappings, type ProxyMappingItem } from '@/services/proxyMappingApi';
import { useSessionStore } from '@/stores/session';

const loading = ref(false);
const reconcileTab = ref<'missing' | 'extra' | 'conflict'>('missing');
const coverageTab = ref<'zabbix' | 'ledger' | 'matrix'>('zabbix');
const matrixTab = ref<'ledger_only' | 'zabbix_only' | 'neither'>('ledger_only');
const proxyTopN = ref<number>(20);
const proxyMergeOther = ref(true);
const proxyKeyword = ref('');
const proxyOnlyAbnormal = ref(false);
const proxyDetailVisible = ref(false);
const proxyDetailProxy = ref('');
const proxyDetailKeyword = ref('');
const proxyDetailOnlyAbnormal = ref(false);
const proxyDetailLoading = ref(false);
const proxyDetailPage = ref(1);
const proxyDetailPageSize = ref(50);
const proxyMappingDialogVisible = ref(false);
const proxyMappingSaving = ref(false);
const proxyMappings = ref<ProxyMappingItem[]>([]);
const proxyMappingDraft = ref<Array<{ proxy: string; display_name: string; remark: string }>>([]);

const proxyDetail = reactive<AssetProxyHostsResponse>({
  generated_at: '',
  proxy: '',
  summary: { host_total: 0, abnormal_host_total: 0, ip_total: 0, conflict_ip_total: 0, no_ip_total: 0 },
  pagination: { limit: 50, offset: 0, total: 0 },
  items: []
});

const sessionStore = useSessionStore();
const canManage = computed(() => sessionStore.hasPermission('assets.records.manage'));

const proxyNameMap = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {};
  for (const item of proxyMappings.value) {
    if (item.is_active && item.proxy && item.display_name) {
      map[item.proxy] = item.display_name;
    }
  }
  return map;
});

function proxyLabel(proxy: string) {
  const key = (proxy || '').trim();
  if (!key) return '-';
  const display = proxyNameMap.value[key];
  if (!display) return key;
  if (display === key) return key;
  return `${display}（${key}）`;
}

const data = reactive<AssetGovernanceOverview>({
  generated_at: '',
  summary: {
    ipmp_total: 0,
    zabbix_host_total: 0,
    workorder_host_total: 0
  },
  ledger_coverage: {
    total: 0,
    covered: 0,
    uncovered: 0,
    covered_rate: 0,
    uncovered_items: []
  },
  workorder_coverage: undefined,
  ipmp_coverage: {
    total: 0,
    monitored: 0,
    uncovered: 0,
    monitored_rate: 0,
    uncovered_items: []
  },
  zabbix_coverage: {
    total: 0,
    monitored: 0,
    uncovered: 0,
    monitored_rate: 0,
    uncovered_items: []
  },
  coverage_matrix: {
    counts: { both: 0, ledger_only: 0, zabbix_only: 0, neither: 0 },
    items: { ledger_only: [], zabbix_only: [], neither: [] }
  },
  ip_reconcile: {
    workorder_total: 0,
    zabbix_total: 0,
    matched_by_ip: 0,
    missing_in_zabbix: 0,
    extra_in_zabbix: 0,
    workorder_ip_conflicts: 0,
    zabbix_ip_conflicts: 0,
    missing_in_zabbix_items: [],
    extra_in_zabbix_items: [],
    zabbix_ip_conflict_items: []
  },
  proxy_stats: []
});

const workorderCoverage = computed(() => data.workorder_coverage || data.ledger_coverage);

function buildDonutBase(params: {
  title: string;
  centerText: string;
  data: Array<{ value: number; name: string; itemStyle?: { color?: string } }>;
  colors?: string[];
}): EChartsOption | null {
  const total = params.data.reduce((sum, item) => sum + (item.value || 0), 0);
  if (total <= 0) return null;
  const option: EChartsOption = {
    tooltip: { trigger: 'item', appendToBody: true, extraCssText: 'z-index: 3000;' },
    legend: { bottom: 0, left: 'center', type: 'scroll' },
    graphic: {
      type: 'text',
      left: 'center',
      top: '42%',
      style: {
        text: `${params.title}\n${params.centerText}`,
        align: 'center',
        fill: '#303133',
        fontSize: 13,
        fontWeight: 600,
        lineHeight: 18
      }
    },
    series: [
      {
        type: 'pie',
        center: ['50%', '42%'],
        radius: ['55%', '78%'],
        avoidLabelOverlap: true,
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: params.data
      }
    ],
    color: params.colors
  };
  return option;
}

function buildRateDonut(params: { total: number; covered: number; coveredLabel: string; uncoveredLabel: string; title: string }) {
  const total = params.total || 0;
  const covered = Math.max(0, params.covered || 0);
  const uncovered = Math.max(0, total - covered);
  const rate = total ? covered / total : 0;
  return buildDonutBase({
    title: params.title,
    centerText: `${(rate * 100).toFixed(1)}%`,
    data: [
      { value: covered, name: params.coveredLabel },
      { value: uncovered, name: params.uncoveredLabel }
    ],
    colors: ['#67C23A', '#909399']
  });
}

const coverageOption = computed<EChartsOption | null>(() => {
  const total = data.zabbix_coverage.total || data.ipmp_coverage.total || 0;
  const monitored = data.zabbix_coverage.monitored || data.ipmp_coverage.monitored || 0;
  return buildRateDonut({
    total,
    covered: monitored,
    coveredLabel: '已覆盖',
    uncoveredLabel: '未覆盖',
    title: '监控覆盖率'
  });
});

const ledgerCoverageOption = computed<EChartsOption | null>(() => {
  const total = workorderCoverage.value.total || 0;
  const covered = workorderCoverage.value.covered || 0;
  return buildRateDonut({
    total,
    covered,
    coveredLabel: '已纳管',
    uncoveredLabel: '未纳管',
    title: '工单纳管率'
  });
});

const matrixOption = computed<EChartsOption | null>(() => {
  const c = data.coverage_matrix.counts;
  const total = (c.both || 0) + (c.ledger_only || 0) + (c.zabbix_only || 0) + (c.neither || 0);
  return buildDonutBase({
    title: '交叉矩阵',
    centerText: `总计 ${total}`,
    data: [
      { name: '工单+监控', value: c.both || 0 },
      { name: '有工单无监控', value: c.ledger_only || 0 },
      { name: '有监控无工单', value: c.zabbix_only || 0 },
      { name: '两边都无', value: c.neither || 0 }
    ],
    colors: ['#67C23A', '#E6A23C', '#F56C6C', '#909399']
  });
});

const proxyTableData = computed(() => {
  const keyword = proxyKeyword.value.trim().toLowerCase();
  return (data.proxy_stats || []).filter((item) => {
    if (proxyOnlyAbnormal.value && (item.unavailable || 0) + (item.unknown || 0) <= 0) return false;
    if (!keyword) return true;
    const proxy = (item.proxy || '').toLowerCase();
    const display = (proxyNameMap.value[item.proxy] || '').toLowerCase();
    return proxy.includes(keyword) || display.includes(keyword);
  });
});

const proxyOption = computed<EChartsOption | null>(() => {
  const all = proxyTableData.value;
  if (!all.length) return null;

  const topN = proxyTopN.value;
  const useAll = topN === 0;
  const sliceCount = useAll ? all.length : Math.max(1, Math.min(topN, all.length));
  const top = all.slice(0, sliceCount);

  const categories: string[] = [];
  const available: number[] = [];
  const unavailable: number[] = [];
  const unknown: number[] = [];

  for (const item of top) {
    categories.push(proxyLabel(item.proxy));
    available.push(item.available || 0);
    unavailable.push(item.unavailable || 0);
    unknown.push(item.unknown || 0);
  }

  if (proxyMergeOther.value && !useAll && all.length > sliceCount) {
    const rest = all.slice(sliceCount);
    const other = rest.reduce(
      (acc, item) => {
        acc.available += item.available || 0;
        acc.unavailable += item.unavailable || 0;
        acc.unknown += item.unknown || 0;
        acc.total += item.total || 0;
        return acc;
      },
      { proxy: '其他', total: 0, available: 0, unavailable: 0, unknown: 0 }
    );
    if (other.total > 0) {
      categories.push(other.proxy);
      available.push(other.available);
      unavailable.push(other.unavailable);
      unknown.push(other.unknown);
    }
  }

  const showZoom = categories.length > 12;
  const end = showZoom ? Math.max(10, Math.round((12 / categories.length) * 100)) : 100;
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      extraCssText: 'z-index: 3000;'
    },
    legend: { top: 0, left: 'center', type: 'scroll' },
    grid: { left: 240, right: 18, top: 36, bottom: showZoom ? 28 : 12, containLabel: true },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        width: 220,
        overflow: 'break'
      }
    },
    dataZoom: showZoom
      ? [
          { type: 'inside', yAxisIndex: 0 },
          { type: 'slider', yAxisIndex: 0, right: 2, start: 0, end, height: 220 }
        ]
      : undefined,
    series: [
      { name: '可用', type: 'bar', stack: 'total', data: available },
      { name: '不可用', type: 'bar', stack: 'total', data: unavailable },
      { name: '未知', type: 'bar', stack: 'total', data: unknown }
    ],
    color: ['#67C23A', '#F56C6C', '#909399']
  };
  return option;
});

const reconcileOption = computed<EChartsOption | null>(() => {
  const values = [
    { key: 'matched', name: '匹配', value: data.ip_reconcile.matched_by_ip || 0, color: '#67C23A' },
    { key: 'missing', name: '工单缺失监控', value: data.ip_reconcile.missing_in_zabbix || 0, color: '#F56C6C' },
    { key: 'extra', name: '监控未入工单', value: data.ip_reconcile.extra_in_zabbix || 0, color: '#E6A23C' },
    { key: 'conflict', name: 'Zabbix IP 冲突', value: data.ip_reconcile.zabbix_ip_conflicts || 0, color: '#909399' }
  ];
  const total = values.reduce((sum, item) => sum + item.value, 0);
  if (total <= 0) return null;
  const option: EChartsOption = {
    tooltip: { trigger: 'item', appendToBody: true, extraCssText: 'z-index: 3000;' },
    legend: { bottom: 0, left: 'center', type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        label: { show: false },
        labelLine: { show: false },
        data: values.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } }))
      }
    ]
  };
  return option;
});

async function loadData() {
  loading.value = true;
  try {
    const result = await fetchAssetGovernanceOverview({ limit: 50 });
    Object.assign(data, result);
    await loadProxyMappings();
  } catch (error) {
    ElMessage.error('统计数据加载失败');
  } finally {
    loading.value = false;
  }
}

async function loadProxyMappings() {
  try {
    proxyMappings.value = await fetchProxyMappings();
  } catch (error) {
    // 映射属于增强能力，失败不阻断主流程
  }
}

function openProxyMappingDialog() {
  const list = (data.proxy_stats || []).map((item) => item.proxy).filter((p) => String(p || '').trim());
  const unique = Array.from(new Set(list));
  proxyMappingDraft.value = unique.map((proxy) => {
    const existing = proxyMappings.value.find((m) => m.proxy === proxy && m.is_active);
    return { proxy, display_name: existing?.display_name || '', remark: existing?.remark || '' };
  });
  proxyMappingDialogVisible.value = true;
}

async function saveProxyMappings() {
  proxyMappingSaving.value = true;
  try {
    const payload = proxyMappingDraft.value.map((row) => ({
      proxy: row.proxy,
      display_name: row.display_name,
      remark: row.remark
    }));
    const result = await upsertProxyMappings(payload);
    proxyMappings.value = result.items;
    ElMessage.success('Proxy 映射已保存');
    proxyMappingDialogVisible.value = false;
  } catch (error) {
    ElMessage.error('Proxy 映射保存失败（需要 assets.records.manage 权限）');
  } finally {
    proxyMappingSaving.value = false;
  }
}

function openProxyDetail(proxy: string) {
  proxyDetailProxy.value = proxy || '';
  proxyDetailKeyword.value = '';
  proxyDetailOnlyAbnormal.value = false;
  proxyDetailPage.value = 1;
  proxyDetailVisible.value = true;
  loadProxyDetail();
}

async function loadProxyDetail() {
  if (!proxyDetailProxy.value) return;
  proxyDetailLoading.value = true;
  try {
    const result = await fetchAssetProxyHosts({
      proxy: proxyDetailProxy.value,
      limit: proxyDetailPageSize.value,
      offset: (proxyDetailPage.value - 1) * proxyDetailPageSize.value,
      keyword: proxyDetailKeyword.value,
      only_abnormal: proxyDetailOnlyAbnormal.value
    });
    Object.assign(proxyDetail, result);
  } catch (error) {
    ElMessage.error('Proxy 明细加载失败');
  } finally {
    proxyDetailLoading.value = false;
  }
}

function onProxyDetailPageChange(page: number) {
  proxyDetailPage.value = page;
  loadProxyDetail();
}

watch([proxyDetailKeyword, proxyDetailOnlyAbnormal], () => {
  if (!proxyDetailVisible.value) return;
  proxyDetailPage.value = 1;
  loadProxyDetail();
});

watch(proxyDetailVisible, (visible) => {
  if (visible) return;
  proxyDetail.items = [];
  proxyDetail.pagination = { limit: proxyDetailPageSize.value, offset: 0, total: 0 };
});

function formatPercent(value: number) {
  if (typeof value !== 'number') return '-';
  return `${(value * 100).toFixed(2)}%`;
}

function formatDateTime(value: string) {
  if (!value) return '-';
  return dayjs(value).format('YYYY-MM-DD HH:mm');
}

function statusTagType(status?: string) {
  const text = (status || '').trim();
  if (!text) return 'info';
  if (text === '生产') return 'success';
  if (text === '在建' || text === '挂起') return 'warning';
  if (text === '下线' || text === '中止或取消' || text.includes('中止') || text.includes('取消')) return 'info';
  return 'info';
}

loadData();
</script>

<style scoped>
.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-row {
  margin-bottom: 0.25rem;
}

.kpi {
  border: 1px solid var(--oa-border-light);
  border-radius: 8px;
  padding: 12px;
  background: var(--oa-bg-panel);
}

.kpi-label {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.kpi-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
  color: var(--oa-text-primary);
}

.kpi-value.danger {
  color: var(--el-color-danger);
}

.kpi-value.warning {
  color: var(--el-color-warning);
}

.host-line {
  line-height: 1.6;
}

.host-name {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.host-meta {
  color: var(--oa-text-secondary);
}

.proxy-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.proxy-toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.proxy-toolbar-label {
  color: var(--oa-text-secondary);
  font-size: 12px;
}

.proxy-detail-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
</style>
