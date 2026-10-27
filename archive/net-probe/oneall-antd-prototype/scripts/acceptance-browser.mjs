import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const outDir = path.join(projectRoot, 'output', 'acceptance-browser');
const requestedBaseUrl = process.env.ACCEPTANCE_BASE_URL;
const viewport = { width: 1365, height: 760 };

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForServer(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // keep polling
    }
    await wait(250);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function startVite() {
  return new Promise((resolve, reject) => {
    const child = spawn('pnpm', ['exec', 'vite', '--host', '127.0.0.1', '--port', '5183'], {
      cwd: projectRoot,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) {
        child.kill('SIGTERM');
        reject(new Error('Timed out starting Vite'));
      }
    }, 30000);
    const onData = (chunk) => {
      const text = chunk.toString();
      const match = text.match(/Local:\s+(http:\/\/127\.0\.0\.1:\d+\/)/);
      if (match && !settled) {
        settled = true;
        clearTimeout(timer);
        resolve({ child, url: match[1] });
      }
    };
    child.stdout.on('data', onData);
    child.stderr.on('data', onData);
    child.on('exit', (code) => {
      if (!settled) {
        clearTimeout(timer);
        reject(new Error(`Vite exited before ready: ${code}`));
      }
    });
  });
}

function stopVite(server) {
  if (server?.child && !server.child.killed) server.child.kill('SIGTERM');
}

async function clickByText(page, text) {
  const target = page.getByText(text, { exact: true }).first();
  await target.waitFor({ state: 'visible', timeout: 8000 });
  await target.click();
}

async function clickButton(page, name) {
  const target = page.getByRole('button', { name }).first();
  await target.waitFor({ state: 'visible', timeout: 8000 });
  await target.click();
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: true });
}

async function expectVisibleText(page, text, label) {
  await page.waitForFunction((value) => document.body.innerText.includes(value), text, { timeout: 8000 });
  const visible = await page.evaluate((value) => document.body.innerText.includes(value), text);
  if (!visible) throw new Error(`${label}: expected visible text "${text}"`);
}

async function main() {
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });

  let server = null;
  let baseUrl = requestedBaseUrl;
  if (!baseUrl) {
    server = await startVite();
    baseUrl = server.url;
  }
  if (!baseUrl.endsWith('/')) baseUrl += '/';
  await waitForServer(baseUrl);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport });
  const consoleIssues = [];
  page.on('console', (message) => {
    if (['error', 'warning'].includes(message.type())) {
      const text = message.text();
      if (text.includes('antd v5 support React is 16 ~ 18')) return;
      if (text.includes('Failed to load resource: the server responded with a status of')) return;
      consoleIssues.push(`${message.type()}: ${text}`);
    }
  });

  const checks = [];
  async function step(name, fn) {
    await fn();
    checks.push({ name, status: 'passed' });
  }

  try {
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      for (const key of Object.keys(localStorage)) {
        if (key.startsWith('oneall.')) localStorage.removeItem(key);
      }
      localStorage.setItem('oneall.currentRole', 'OpsAdmin');
    });

    await step('asset model create', async () => {
      await page.goto(`${baseUrl}#asset-new`, { waitUntil: 'networkidle' });
      await clickByText(page, '创建模型');
      await expectVisibleText(page, '模型 ID', 'asset model create');
      await screenshot(page, '01-asset-model-created');
    });

    await step('asset sync save config and writeback', async () => {
      await page.goto(`${baseUrl}#asset-sync`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '脚本配置', 'asset sync config');
      await clickButton(page, '保存配置');
      await expectVisibleText(page, '配置已保存', 'asset sync save config');
      await clickButton(page, '执行同步');
      await expectVisibleText(page, '同步完成', 'asset sync writeback');
      await screenshot(page, '02-asset-sync-completed');
      await page.goto(`${baseUrl}#assets`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, 'svc-01.oneall.internal', 'asset records visible');
      await screenshot(page, '03-asset-records-visible');
    });

    await step('monitoring strategy list and switch', async () => {
      await page.goto(`${baseUrl}#policies`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, 'HTTP 可用性', 'strategy list');
      await expectVisibleText(page, '启用', 'strategy switch');
      await screenshot(page, '04-strategy-created-toggled');
    });

    await step('alert close', async () => {
      await page.goto(`${baseUrl}#alerts`, { waitUntil: 'networkidle' });
      await clickByText(page, '关闭');
      await expectVisibleText(page, '已恢复', 'alert close');
      await screenshot(page, '05-alert-closed');
    });

    await step('probe register', async () => {
      await page.goto(`${baseUrl}#probes`, { waitUntil: 'networkidle' });
      await clickButton(page, '注册探针');
      await expectVisibleText(page, '注册探针', 'probe register drawer');
      await clickButton(page, '保 存');
      await expectVisibleText(page, '接入信息', 'probe access info');
      await expectVisibleText(page, 'ONEALL_PROBE_ID', 'probe bootstrap');
      await clickButton(page, '完 成');
      await expectVisibleText(page, 'probe-new-01', 'probe register');
      await screenshot(page, '06-probe-registered');
    });

    await step('IP regex helper generates and tests regex', async () => {
      await page.goto(`${baseUrl}#ip-regex`, { waitUntil: 'networkidle' });
      await page.getByPlaceholder('192.168.1.10\n192.168.1.11').fill('10.0.0.1,10.0.0.2\n10.0.0.1，10.0.0.3');
      await clickButton(page, '生成正则');
      await expectVisibleText(page, '有效 3 个', 'ip regex valid count');
      await expectVisibleText(page, '重复 1 个', 'ip regex duplicate count');
      await page.getByPlaceholder('输入一个 IPv4 测试正则是否命中').fill('10.0.0.2');
      await clickButton(page, '测 试');
      await expectVisibleText(page, '命中', 'ip regex hit test');
      await screenshot(page, '07-ip-regex-helper');
    });

    await step('one-off detection creates task', async () => {
      await page.goto(`${baseUrl}#detection`, { waitUntil: 'networkidle' });
      await clickButton(page, '执行检测');
      await expectVisibleText(page, '已提交 1 个探针检测', 'one-off domain detection');
      await expectVisibleText(page, '成功', 'one-off domain detection result');
      await page.goto(`${baseUrl}#certificate-detection`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '证书检测', 'certificate mode');
      await clickButton(page, '执行检测');
      await expectVisibleText(page, 'CERTIFICATE', 'certificate detection');
      await page.goto(`${baseUrl}#cmdb-domain-check`, { waitUntil: 'networkidle' });
      await clickButton(page, '执行校验');
      await expectVisibleText(page, 'CMDB 校验已完成', 'cmdb check');
      await page.goto(`${baseUrl}#detection-records`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, 'www.oneall.internal', 'detection records');
      await screenshot(page, '08-detection-task-created');
    });

    await step('workorder pages render current IA', async () => {
      await page.goto(`${baseUrl}#workorder-new`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '拨测监控申请', 'workorder create page');
      await page.goto(`${baseUrl}#workorders`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '我的申请', 'my workorders page');
      await page.goto(`${baseUrl}#approvals`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '我的审批', 'approval page');
      await screenshot(page, '09-workorder-pages');
    });

    await step('settings audit and notifications visible', async () => {
      await page.goto(`${baseUrl}#settings-audit-logs`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '审计日志', 'audit logs');
      await screenshot(page, '10-audit-logs');
      await page.goto(`${baseUrl}#settings-notification-channels`, { waitUntil: 'networkidle' });
      await expectVisibleText(page, '站内信', 'notification channels');
      await screenshot(page, '11-notification-channels');
    });

    const browserState = await page.evaluate(() => ({
      modelCount: JSON.parse(localStorage.getItem('oneall.assetModels') || '[]').length,
      recordBuckets: Object.keys(JSON.parse(localStorage.getItem('oneall.assetRecords') || '{}')).length,
      syncRuns: JSON.parse(localStorage.getItem('oneall.assetSyncRuns') || '[]').length,
      strategies: JSON.parse(localStorage.getItem('oneall.monitoringStrategies') || '[]').length,
      probes: JSON.parse(localStorage.getItem('oneall.probeNodes') || '[]').length,
      detections: JSON.parse(localStorage.getItem('oneall.detectionTasks') || '[]').length,
      workorders: JSON.parse(localStorage.getItem('oneall.workorders') || '[]').length,
      alerts: JSON.parse(localStorage.getItem('oneall.alertEvents') || '[]').length,
      auditLogs: JSON.parse(localStorage.getItem('oneall.auditLogs') || '[]').length,
      notifications: JSON.parse(localStorage.getItem('oneall.notifications') || '[]').length
    }));

    const summary = { baseUrl, viewport, checks, browserState, consoleIssues, screenshots: outDir };
    writeFileSync(path.join(outDir, 'acceptance.json'), JSON.stringify(summary, null, 2));

    if (consoleIssues.length) {
      throw new Error(`Browser console issues found:\n${consoleIssues.join('\n')}`);
    }

    console.log(`Browser acceptance passed: ${checks.length} checks`);
    console.log(`Report: ${path.join(outDir, 'acceptance.json')}`);
    console.log(`Screenshots: ${outDir}`);
  } finally {
    await browser.close();
    stopVite(server);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
