import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import http from 'node:http';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn } from 'node:child_process';

const root = new URL('..', import.meta.url).pathname;
const report = [];

async function main() {
  const workdir = mkdtempSync(join(tmpdir(), 'oneall-real-probe-'));
  const apiPort = await freePort();
  const apiBase = `http://127.0.0.1:${apiPort}`;
  const targetServer = await startTargetServer();
  const api = spawnManaged('go', ['run', './cmd/oneall-api'], {
    cwd: root,
    env: { ...process.env, GIN_MODE: 'release', ONEALL_LISTEN_ADDR: `127.0.0.1:${apiPort}`, DATABASE_URL: '' }
  });

  try {
    await waitForHealth(apiBase);

    const probe = await step('register probe', () => post(apiBase, '/api/v1/probes/register', {
      name: 'probe-smoke-local',
      region: 'local',
      network_type: 'localhost',
      ip_address: '127.0.0.1',
      capabilities: ['HTTP']
    }));
    assert.equal(typeof probe.token, 'string');
    assert.ok(probe.token.length > 0);

    const task = await step('create one-off detection', () => post(apiBase, '/api/v1/detection/one-off', {
      type: 'http',
      protocol: 'HTTP',
      target: targetServer.url,
      probe: probe.id,
      timeout_seconds: 2,
      related_asset: 'probe-smoke.local',
      business_line: 'smoke',
      environment: 'prod'
    }, 'OpsEngineer'));
    assert.equal(task.status, 'pending');

    const spoolPath = join(workdir, 'pending-results.json');
    await step('run real probe agent once', () => run('go', [
      'run',
      './cmd/oneall-probe-agent',
      '-api',
      apiBase,
      '-probe-id',
      probe.id,
      '-token',
      probe.token,
      '-version',
      'smoke',
      '-spool-path',
      spoolPath,
      '-once'
    ], { cwd: root }));

    const detail = await step('verify completed detection task', () => get(apiBase, `/api/v1/detection/tasks/${task.id}`));
    assert.equal(detail.status, 'success');
    assert.equal(detail.claimed_by_probe_id, probe.id);
    assert.equal(detail.result?.result_id, `${probe.id}:${task.id}`);
    assert.equal(detail.result?.probe_id, probe.id);
    assert.equal(detail.result?.task_id, task.id);
    assert.equal(detail.result?.status_code, 204);

    const runtime = await step('verify probe runtime updated', () => get(apiBase, `/api/v1/probes/nodes/${probe.id}/runtime`));
    assert.equal(runtime.status, 'online');
    assert.ok(runtime.tasks.executed >= 1);

    const audit = await step('verify audit evidence', () => get(apiBase, '/api/v1/settings/audit-logs'));
    assert.ok(audit.items.some((item) => item.object === task.id || item.object === probe.id));

    printReport(apiBase);
  } finally {
    await api.stop();
    await targetServer.close();
    rmSync(workdir, { recursive: true, force: true });
  }
}

async function startTargetServer() {
  const server = http.createServer((_, response) => {
    response.writeHead(204);
    response.end();
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  return {
    url: `http://127.0.0.1:${port}/health`,
    close: () => new Promise((resolve) => server.close(resolve))
  };
}

async function freePort() {
  const server = http.createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address();
  await new Promise((resolve) => server.close(resolve));
  return port;
}

function spawnManaged(command, args, options) {
  const child = spawn(command, args, { ...options, detached: true, stdio: ['ignore', 'pipe', 'pipe'] });
  const exited = new Promise((resolve) => child.once('exit', resolve));
  child.stderr.on('data', (chunk) => process.stderr.write(chunk));
  child.stdout.on('data', (chunk) => process.stdout.write(chunk));
  child.on('exit', (code, signal) => {
    if (code && code !== 0) {
      process.stderr.write(`${command} ${args.join(' ')} exited with ${code}${signal ? ` (${signal})` : ''}\n`);
    }
  });
  return {
    stop: async () => {
      if (child.exitCode !== null || child.killed) return;
      killProcessGroup(child.pid, 'SIGTERM');
      await Promise.race([
        exited,
        sleep(2000).then(() => {
          if (child.exitCode === null) killProcessGroup(child.pid, 'SIGKILL');
        })
      ]);
    }
  };
}

function killProcessGroup(pid, signal) {
  try {
    process.kill(-pid, signal);
  } catch {
    try {
      process.kill(pid, signal);
    } catch {
      // already exited
    }
  }
}

async function waitForHealth(base) {
  const started = Date.now();
  let lastError;
  while (Date.now() - started < 20000) {
    try {
      const response = await fetch(`${base}/healthz`);
      if (response.ok) return;
    } catch (error) {
      lastError = error;
    }
    await sleep(300);
  }
  throw new Error(`Go API did not become healthy: ${lastError?.message ?? 'timeout'}`);
}

async function run(command, args, options) {
  await new Promise((resolve, reject) => {
    const child = spawn(command, args, { ...options, stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    child.stdout.on('data', (chunk) => process.stdout.write(chunk));
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
      process.stderr.write(chunk);
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(' ')} failed with ${code}: ${stderr.trim()}`));
    });
  });
  return { ok: true };
}

async function step(name, fn) {
  const result = await fn();
  report.push({ step: name, status: 'ok', evidence: summarize(result) });
  return result;
}

async function get(base, path, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, {
    headers: { 'x-oneall-role': role }
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`GET ${path} ${response.status}: ${JSON.stringify(body)}`);
  return body;
}

async function post(base, path, body, role = 'OpsAdmin') {
  const response = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-oneall-role': role },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(`POST ${path} ${response.status}: ${JSON.stringify(payload)}`);
  return payload;
}

function summarize(value) {
  if (value?.id) return value.id;
  if (value?.items) return `${value.items.length} items`;
  if (value?.ok) return 'ok';
  return 'ok';
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function printReport(base) {
  console.log(JSON.stringify({ base, passed: true, steps: report }, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({ passed: false, error: error.message, steps: report }, null, 2));
  process.exitCode = 1;
});
