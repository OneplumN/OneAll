import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import { apiV1Endpoints } from '../src/platformContracts.ts';
import { technicalArchitectureDecision } from '../src/technicalArchitecture.ts';

const tasklist = readFileSync(new URL('../../oneall-redesign/05-tasklist.md', import.meta.url), 'utf8');
const techDoc = readFileSync(new URL('../../oneall-redesign/06-technical-architecture.md', import.meta.url), 'utf8');
const initialSchema = readFileSync(new URL('../../oneall-api/db/migrations/001_initial_schema.sql', import.meta.url), 'utf8');

test('technical document and executable contract agree on core decisions', () => {
  assert.match(techDoc, /Go \+ Gin/);
  assert.match(techDoc, /PostgreSQL/);
  assert.match(techDoc, /outbox\/event_log \+ Redis Streams/);
  assert.match(techDoc, /HTTPS \+ JSON/);
  assert.equal(technicalArchitectureDecision.backend.framework, 'go-gin');
  assert.equal(technicalArchitectureDecision.database.primary, 'postgresql');
  assert.equal(technicalArchitectureDecision.eventDelivery.mode, 'outbox-redis-stream');
  assert.equal(technicalArchitectureDecision.probe.protocol, 'https-json');
});

test('probe protocol endpoints exist in API v1 contract', () => {
  const paths = new Set(apiV1Endpoints.map((endpoint) => `${endpoint.method} ${endpoint.path}`));

  for (const endpoint of technicalArchitectureDecision.probe.endpoints) {
    assert.equal(paths.has(endpoint), true, `${endpoint} should exist in API contract`);
  }
});

test('tasklist records technical decisions as confirmed', () => {
  assert.match(tasklist, /- \[x\] 确认是否采用 Go \+ Gin 重写后端/);
  assert.match(tasklist, /- \[x\] 确认数据库选型和迁移方式/);
  assert.match(tasklist, /- \[x\] 确认鉴权方案/);
  assert.match(tasklist, /- \[x\] 确认事件投递方案/);
  assert.match(tasklist, /- \[x\] 确认 Redis 使用边界/);
  assert.match(tasklist, /- \[x\] 确认 TimescaleDB 使用边界/);
  assert.match(tasklist, /- \[x\] 确认探针通信协议/);
});

test('technical database decision has an executable initial schema', () => {
  assert.match(techDoc, /oneall-api\/db\/migrations\/001_initial_schema\.sql/);
  assert.match(tasklist, /- \[x\] 确认 PostgreSQL 首版目标 schema/);
  assert.match(initialSchema, /CREATE TABLE asset_models/);
  assert.match(initialSchema, /CREATE TABLE asset_records/);
  assert.match(initialSchema, /CREATE TABLE event_outbox/);
  assert.match(initialSchema, /asset_records_fields_object CHECK \(jsonb_typeof\(fields\) = 'object'\)/);
});
