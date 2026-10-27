import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');
const outDir = path.join(projectRoot, 'output', 'ui-audit');
const viewport = {
  width: Number(process.env.UI_AUDIT_WIDTH ?? 1365),
  height: Number(process.env.UI_AUDIT_HEIGHT ?? 760)
};
const screenshotMode = process.env.UI_AUDIT_SCREENSHOTS ?? 'failures';
const requestedBaseUrl = process.env.UI_AUDIT_BASE_URL;

function readRoutes() {
  const contractPath = path.join(projectRoot, 'src', 'navigationContract.ts');
  const source = readFileSync(contractPath, 'utf8');
  const matches = [...source.matchAll(/\{\s*key:\s*'([^']+)'/g)].map((match) => match[1]);
  return [...new Set(matches)];
}

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
      // Keep polling until Vite is ready.
    }
    await wait(250);
  }
  throw new Error(`Timed out waiting for dev server: ${url}`);
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
        reject(new Error('Timed out starting Vite dev server'));
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
        reject(new Error(`Vite exited before becoming ready, code=${code}`));
      }
    });
  });
}

function stopVite(server) {
  if (!server?.child || server.child.killed) return;
  server.child.kill('SIGTERM');
}

async function auditRoute(page, route, baseUrl) {
  const logs = [];
  page.removeAllListeners('console');
  page.on('console', (message) => {
    if (['error', 'warning'].includes(message.type())) {
      logs.push(`${message.type()}: ${message.text()}`);
    }
  });
  await page.goto(`${baseUrl}#${route}`, { waitUntil: 'networkidle' });

  const data = await page.evaluate(() => {
    const viewportW = document.documentElement.clientWidth;
    const cards = Array.from(document.querySelectorAll('.page .ant-card'));
    const pageRect = document.querySelector('.page')?.getBoundingClientRect();
    const expectedLeft = pageRect ? Math.round(pageRect.left + 16) : null;
    const expectedRight = pageRect ? Math.round(pageRect.right - 16) : null;
    const boundarySelectors = [
      '.legacy-list-panel',
      '.cmdb-workbench',
      '.model-management-content',
      '.sync-page-shell',
      '.data-card',
      '.workbench-grid',
      '.detail-shell',
      '.settings-grid',
      '.regex-tool-grid'
    ];
    const boundaryDrift = boundarySelectors
      .map((selector) => {
        const element = document.querySelector(selector);
        if (!element || expectedLeft === null || expectedRight === null) return null;
        const rect = element.getBoundingClientRect();
        return {
          selector,
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          expectedLeft,
          expectedRight
        };
      })
      .filter(Boolean)
      .filter((item) => Math.abs(item.left - item.expectedLeft) > 1 || Math.abs(item.right - item.expectedRight) > 1);
    const visibleTitles = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,.page-title')).filter(
      (element) => getComputedStyle(element).display !== 'none'
    );
    const overflowing = Array.from(document.querySelectorAll('body *'))
      .filter((element) => {
        if (element.closest('.ant-table-content')) return false;
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return (
          rect.width > 0 &&
          rect.height > 0 &&
          style.position !== 'fixed' &&
          (rect.right > viewportW + 1 || rect.left < -1)
        );
      })
      .slice(0, 8)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          tag: element.tagName.toLowerCase(),
          className: String(element.className).slice(0, 100),
          text: (element.textContent || '').trim().slice(0, 80),
          left: Math.round(rect.left),
          right: Math.round(rect.right)
        };
      });

    return {
      actualRoute: location.hash.slice(1),
      title: document.querySelector('.page-action-bar')?.textContent?.trim() || '',
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      overflowing,
      antCards: cards.length,
      nestedCards: cards.filter((card) => card.querySelector('.ant-card')).length,
      shadowCards: cards.filter((card) => getComputedStyle(card).boxShadow !== 'none').length,
      boundaryDrift,
      visibleTitles: visibleTitles.length,
      placeholder: document.body.innerText.includes('当前先以核心页面定风格')
    };
  });

  const problems = [];
  if (data.overflowX || data.overflowing.length) problems.push('horizontal-overflow');
  if (data.nestedCards > 0) problems.push('nested-cards');
  if (data.shadowCards > 0) problems.push('shadow-cards');
  if (data.boundaryDrift.length) problems.push('content-boundary-drift');
  if (data.visibleTitles >= 5) problems.push('too-many-titles');
  if (data.placeholder) problems.push('placeholder-page');
  if (logs.length) problems.push('console-warning-or-error');

  return { route, ...data, logs, problems };
}

async function main() {
  const routes = readRoutes();
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
  const page = await browser.newPage({ viewport, deviceScaleFactor: 1 });
  const results = [];

  try {
    for (const route of routes) {
      const result = await auditRoute(page, route, baseUrl);
      results.push(result);
      const shouldCapture =
        screenshotMode === 'all' ||
        (screenshotMode === 'failures' && result.problems.length > 0);
      if (shouldCapture) {
        await page.screenshot({
          path: path.join(outDir, `${route}.png`),
          fullPage: true
        });
      }
    }
  } finally {
    await browser.close();
    stopVite(server);
  }

  const summary = {
    baseUrl,
    viewport,
    routes: results.length,
    failures: results.filter((result) => result.problems.length > 0).length,
    generatedAt: new Date().toISOString()
  };
  writeFileSync(path.join(outDir, 'audit.json'), JSON.stringify({ summary, results }, null, 2));

  const failures = results.filter((result) => result.problems.length > 0);
  if (failures.length > 0) {
    console.table(
      failures.map((result) => ({
        route: result.route,
        title: result.title,
        problems: result.problems.join(', '),
        cards: result.antCards,
        titles: result.visibleTitles
      }))
    );
    console.error(`UI audit failed: ${failures.length}/${results.length} routes. Report: ${path.join(outDir, 'audit.json')}`);
    process.exitCode = 1;
    return;
  }

  console.log(`UI audit passed: ${results.length} routes at ${viewport.width}x${viewport.height}`);
  console.log(`Report: ${path.join(outDir, 'audit.json')}`);
  if (screenshotMode === 'all') {
    console.log(`Screenshots: ${outDir}`);
  }
}

if (!existsSync(path.join(projectRoot, 'src', 'navigationContract.ts'))) {
  throw new Error('Run this script from the oneall-antd-prototype project.');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
