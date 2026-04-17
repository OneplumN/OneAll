# One-Off Detection Task-ID Control Plane Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将一次性拨测从“gRPC 双向流直接投递任务并回传结果”改为“长连接只做控制面，任务围绕 `task_id` 走可确认、可幂等的短交互”。

**Architecture:** 保留现有 gRPC 长连接用于 `hello / heartbeat / metrics / config refresh / task available hint`，不再让其承担一次性任务的可靠投递。一次性拨测任务由 probe 使用现有 `ProbeToken` 鉴权通过 HTTP 领取与提交结果，后端以 `task_id` 为唯一关联键推进状态机，并通过 claim/result 接口保证幂等与超时收口。

**Tech Stack:** Django 4.2 + DRF、Celery（超时兜底）、Python gRPC gateway、Go probe agent、现有 ProbeToken HMAC 认证。

---

## Scope

- 本计划**只覆盖一次性拨测**（`metadata.execution_source = one_off`）。
- 定时调度（`ProbeSchedule` / `ProbeScheduleExecution`）继续保留现有 gRPC config + 结果回传模型，不在本阶段改造。
- gRPC 长连接保留，但只负责控制面，不再作为一次性任务的唯一事实来源。

## State Machine

- `scheduled`: 后端已创建任务，尚未被 probe 正式领取
- `running`: probe 已成功 claim 任务
- `succeeded`: probe 成功提交结果
- `failed`: probe 提交失败结果
- `timeout`: claim 后超时未完成，或发布后长期未被 claim

## API Contract (Phase 1)

- `POST /api/probes/tasks/claim`
  - 鉴权：`ProbeToken`
  - 请求：`{"limit": 1}` 或空体
  - 响应：
    - 无任务：`204 No Content`
    - 有任务：`200 OK`
    - 返回字段：`task_id`, `target`, `protocol`, `timeout_seconds`, `expected_status`, `metadata`
- `POST /api/probes/tasks/<task_id>/result`
  - 鉴权：`ProbeToken`
  - 请求字段：`status`, `message`, `status_code`, `response_time_ms`, `scheduled_at`, `finished_at`, `metadata`
  - 语义：幂等；若任务已终态则返回当前状态，不重复副作用
- gRPC `ServerMessage.task`、`ProbeMessage.task_ack`、`ProbeMessage.result(task_id one-off)` 在一次性拨测路径上停用

## Design Decisions

- 不新增 `attempt_id`，第一阶段限定“单任务单执行，不重派发”，避免把复杂度一次拉满。
- `published_at` 继续保留，用于表示“任务已对 probe 可见”。
- 新增 `claimed_at`，明确区分“已发布但未被领取”和“已被领取执行中”。
- 前端仍然只关心 `task_id` 详情查询；无需感知 transport 类型。
- `task available hint` 可选：第一阶段可以先不发，probe 采用短轮询 claim，优先确保稳定。

### Task 1: 固化状态机与数据字段

**Files:**
- Modify: `backend/src/apps/monitoring/models/detection_task.py`
- Create: `backend/src/apps/monitoring/migrations/00xx_detection_task_claimed_at.py`
- Modify: `backend/src/apps/monitoring/services/detection_service.py`
- Test: `backend/tests/unit/test_detection_service.py`

**Step 1: Write the failing test**

```python
def test_mark_detection_running_sets_claimed_at():
    task = DetectionTask.objects.create(...)
    task.mark_running()
    task.refresh_from_db()
    assert task.status == DetectionTask.Status.RUNNING
    assert task.claimed_at is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_service.py::test_mark_detection_running_sets_claimed_at -v`
Expected: FAIL with `DetectionTask has no field claimed_at` or missing behavior.

**Step 3: Write minimal implementation**

```python
claimed_at = models.DateTimeField(null=True, blank=True)

def mark_running(self, *, published_at=None, claimed_at=None) -> None:
    self.status = self.Status.RUNNING
    if self.published_at is None:
        self.published_at = published_at or timezone.now()
    if self.claimed_at is None:
        self.claimed_at = claimed_at or timezone.now()
    self.save(update_fields=["status", "published_at", "claimed_at", "updated_at"])
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_service.py::test_mark_detection_running_sets_claimed_at -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/monitoring/models/detection_task.py \
  backend/src/apps/monitoring/migrations/00xx_detection_task_claimed_at.py \
  backend/src/apps/monitoring/services/detection_service.py \
  backend/tests/unit/test_detection_service.py
git commit -m "feat: add claim timestamp for detection tasks"
```

### Task 2: 抽离一次性拨测的 claim 服务

**Files:**
- Create: `backend/src/apps/monitoring/services/detection_claim_service.py`
- Modify: `backend/src/apps/monitoring/services/__init__.py`
- Modify: `backend/src/apps/monitoring/services/detection_scheduler.py`
- Test: `backend/tests/unit/test_detection_claim_service.py`

**Step 1: Write the failing test**

```python
def test_claim_one_off_detection_marks_running_and_returns_payload():
    probe = ProbeNode.objects.create(...)
    task = DetectionTask.objects.create(
        probe=probe,
        status=DetectionTask.Status.SCHEDULED,
        target="https://example.com",
        protocol="HTTPS",
        metadata={"execution_source": "one_off", "timeout_seconds": 10},
    )
    claimed = claim_one_off_detection(probe=probe)
    task.refresh_from_db()
    assert claimed.task_id == str(task.id)
    assert task.status == DetectionTask.Status.RUNNING
    assert task.claimed_at is not None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_claim_service.py::test_claim_one_off_detection_marks_running_and_returns_payload -v`
Expected: FAIL with `ImportError` or missing service.

**Step 3: Write minimal implementation**

```python
@dataclass
class ClaimedDetection:
    task_id: str
    target: str
    protocol: str
    timeout_seconds: int
    expected_status: int
    metadata: dict[str, Any]

def claim_one_off_detection(*, probe: ProbeNode) -> ClaimedDetection | None:
    task = (
        DetectionTask.objects
        .select_for_update(skip_locked=True)
        .filter(
            probe=probe,
            status=DetectionTask.Status.SCHEDULED,
            metadata__execution_source="one_off",
        )
        .order_by("created_at", "id")
        .first()
    )
    ...
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_claim_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/monitoring/services/detection_claim_service.py \
  backend/src/apps/monitoring/services/__init__.py \
  backend/src/apps/monitoring/services/detection_scheduler.py \
  backend/tests/unit/test_detection_claim_service.py
git commit -m "feat: add one-off detection claim service"
```

### Task 3: 增加 probe 领取任务 API

**Files:**
- Create: `backend/src/apps/probes/api/probe_task_views.py`
- Modify: `backend/src/apps/probes/api/urls.py`
- Modify: `backend/src/apps/probes/authentication.py`
- Test: `backend/tests/unit/test_probe_task_api.py`

**Step 1: Write the failing test**

```python
def test_probe_can_claim_one_off_detection():
    probe = ProbeNode.objects.create(...)
    probe.set_api_token("secret")
    task = DetectionTask.objects.create(...)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="ProbeToken secret")
    response = client.post("/api/probes/tasks/claim", {"probe_id": str(probe.id)}, format="json")
    assert response.status_code == 200
    assert response.json()["task_id"] == str(task.id)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_task_api.py::test_probe_can_claim_one_off_detection -v`
Expected: FAIL with `404`.

**Step 3: Write minimal implementation**

```python
class ProbeTaskClaimView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        probe = get_object_or_404(ProbeNode, id=request.data["probe_id"])
        ensure_probe_authenticated(request, probe)
        claimed = detection_claim_service.claim_one_off_detection(probe=probe)
        if claimed is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({...}, status=status.HTTP_200_OK)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_task_api.py::test_probe_can_claim_one_off_detection -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/probes/api/probe_task_views.py \
  backend/src/apps/probes/api/urls.py \
  backend/tests/unit/test_probe_task_api.py
git commit -m "feat: add probe task claim api"
```

### Task 4: 增加 probe 结果提交 API（幂等）

**Files:**
- Create: `backend/src/apps/monitoring/services/detection_result_service.py`
- Modify: `backend/src/apps/probes/api/probe_task_views.py`
- Modify: `backend/src/apps/monitoring/services/detection_service.py`
- Test: `backend/tests/unit/test_probe_task_result_api.py`

**Step 1: Write the failing test**

```python
def test_probe_submit_result_marks_detection_succeeded_idempotently():
    task = DetectionTask.objects.create(status=DetectionTask.Status.RUNNING, ...)
    response = client.post(f"/api/probes/tasks/{task.id}/result", {...}, format="json")
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SUCCEEDED

    again = client.post(f"/api/probes/tasks/{task.id}/result", {...}, format="json")
    assert again.status_code == 200
    task.refresh_from_db()
    assert task.status == DetectionTask.Status.SUCCEEDED
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_task_result_api.py::test_probe_submit_result_marks_detection_succeeded_idempotently -v`
Expected: FAIL with `404`.

**Step 3: Write minimal implementation**

```python
def submit_detection_result(*, probe, task_id, payload):
    detection = DetectionTask.objects.get(id=task_id)
    if detection.status in TERMINAL_STATES:
        return detection
    if payload.status == "success":
        detection_service.mark_detection_succeeded(...)
    else:
        detection_service.mark_detection_failed(...)
    return detection
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_task_result_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/monitoring/services/detection_result_service.py \
  backend/src/apps/probes/api/probe_task_views.py \
  backend/tests/unit/test_probe_task_result_api.py
git commit -m "feat: add idempotent detection result api"
```

### Task 5: 让前端轮询状态与无 worker 场景保持一致

**Files:**
- Modify: `backend/src/apps/monitoring/api/detection_detail_view.py`
- Modify: `backend/src/apps/monitoring/tasks/execute_detection.py`
- Modify: `backend/src/apps/probes/services/probe_task_cleanup_service.py`
- Test: `backend/tests/unit/test_detection_detail_view.py`

**Step 1: Write the failing test**

```python
def test_detection_detail_marks_unclaimed_published_task_timeout():
    task = DetectionTask.objects.create(
        status=DetectionTask.Status.SCHEDULED,
        published_at=timezone.now() - timedelta(seconds=20),
        metadata={"timeout_seconds": 5},
    )
    response = client.get(reverse("detection-detail", kwargs={"detection_id": task.id}))
    assert response.json()["status"] == DetectionTask.Status.TIMEOUT
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_detail_view.py::test_detection_detail_marks_unclaimed_published_task_timeout -v`
Expected: FAIL until `claimed_at` semantics are handled correctly.

**Step 3: Write minimal implementation**

```python
if task.status == DetectionTask.Status.SCHEDULED and task.published_at and overdue:
    detection_service.mark_detection_timeout(task.id)
if task.status == DetectionTask.Status.RUNNING and task.claimed_at and overdue:
    detection_service.mark_detection_timeout(task.id)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_detail_view.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/monitoring/api/detection_detail_view.py \
  backend/src/apps/monitoring/tasks/execute_detection.py \
  backend/src/apps/probes/services/probe_task_cleanup_service.py \
  backend/tests/unit/test_detection_detail_view.py
git commit -m "fix: align timeout cleanup with claim-based delivery"
```

### Task 6: 为 probe 增加 HTTP 任务 client

**Files:**
- Create: `probes/internal/api/tasks.go`
- Modify: `probes/internal/api/client.go`
- Test: `probes/internal/api/tasks_test.go`

**Step 1: Write the failing test**

```go
func TestClaimOneOffTaskReturnsTask(t *testing.T) {
    srv := httptest.NewServer(...)
    client, _ := NewClient(srv.URL, "probe-id", "secret", 5*time.Second, false)
    task, err := client.ClaimOneOffTask(context.Background(), 1)
    require.NoError(t, err)
    require.Equal(t, "task-1", task.ID)
}
```

**Step 2: Run test to verify it fails**

Run: `cd probes && go test ./internal/api -run TestClaimOneOffTaskReturnsTask -v`
Expected: FAIL with missing method.

**Step 3: Write minimal implementation**

```go
func (c *Client) ClaimOneOffTask(ctx context.Context, limit int) (*Task, error) { ... }
func (c *Client) SubmitOneOffResult(ctx context.Context, result TaskResult) error { ... }
```

**Step 4: Run test to verify it passes**

Run: `cd probes && go test ./internal/api -v`
Expected: PASS

**Step 5: Commit**

```bash
git add probes/internal/api/client.go probes/internal/api/tasks.go probes/internal/api/tasks_test.go
git commit -m "feat: add probe http task client"
```

### Task 7: 将一次性任务从 gRPC Transport 中拆出

**Files:**
- Modify: `probes/internal/transport/transport.go`
- Modify: `probes/internal/transport/grpc_transport.go`
- Create: `probes/internal/transport/http_task_transport.go`
- Modify: `probes/internal/agent/agent.go`
- Modify: `probes/cmd/probe/main.go`
- Test: `probes/internal/agent/agent_test.go`
- Test: `probes/internal/transport/http_task_transport_test.go`

**Step 1: Write the failing test**

```go
func TestAgentPollsTaskClientAndSubmitsResultWithoutGrpcTaskStream(t *testing.T) {
    // grpc transport only handles heartbeat/commands
    // task transport returns one claimed task
    // result submit goes through HTTP client
}
```

**Step 2: Run test to verify it fails**

Run: `cd probes && go test ./internal/agent ./internal/transport -v`
Expected: FAIL because task source is still hard-wired to grpc `Tasks()`.

**Step 3: Write minimal implementation**

```go
type TaskSource interface {
    ClaimTask(ctx context.Context) (*api.Task, error)
    SubmitResult(ctx context.Context, result api.TaskResult) error
}

// gRPCTransport keeps: SendHeartbeat / PublishMetrics / Commands / Close
// HTTPTaskTransport owns: ClaimTask / SubmitResult
```

**Step 4: Run test to verify it passes**

Run: `cd probes && go test ./internal/agent ./internal/transport ./cmd/probe -v`
Expected: PASS

**Step 5: Commit**

```bash
git add probes/internal/transport/transport.go \
  probes/internal/transport/grpc_transport.go \
  probes/internal/transport/http_task_transport.go \
  probes/internal/agent/agent.go \
  probes/cmd/probe/main.go \
  probes/internal/agent/agent_test.go \
  probes/internal/transport/http_task_transport_test.go
git commit -m "refactor: split control and task delivery transports"
```

### Task 8: 停用 gRPC 一次性任务下发路径

**Files:**
- Modify: `backend/src/apps/probes/streaming/service.py`
- Modify: `proto/probes/v1/gateway.proto`
- Modify: `backend/src/probes/v1/gateway_pb2.py`
- Modify: `backend/src/probes/v1/gateway_pb2_grpc.py`
- Modify: `probes/internal/probes/v1/gateway.pb.go`
- Modify: `probes/internal/probes/v1/gateway_grpc.pb.go`
- Test: `backend/tests/unit/test_probe_gateway_one_off_detection.py`

**Step 1: Write the failing test**

```python
def test_gateway_does_not_dispatch_one_off_detection_over_stream():
    task = DetectionTask.objects.create(metadata={"execution_source": "one_off"}, ...)
    messages = service._claim_pending_detection_tasks(probe)
    assert messages == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_gateway_one_off_detection.py::test_gateway_does_not_dispatch_one_off_detection_over_stream -v`
Expected: FAIL because gRPC still builds `ServerMessage.task`.

**Step 3: Write minimal implementation**

```python
def _claim_pending_detection_tasks(...):
    return []
```

并清理：
- gRPC 一次性任务 ack 路径
- gRPC 一次性结果回传路径
- proto 中与 one-off detection 强绑定但不再使用的字段/消息（如果本阶段不删 proto，可先标 deprecated）

**Step 4: Run test to verify it passes**

Run: `cd backend && source .venv/bin/activate && pytest tests/unit/test_probe_gateway_one_off_detection.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/apps/probes/streaming/service.py \
  proto/probes/v1/gateway.proto \
  backend/src/probes/v1/gateway_pb2.py \
  backend/src/probes/v1/gateway_pb2_grpc.py \
  probes/internal/probes/v1/gateway.pb.go \
  probes/internal/probes/v1/gateway_grpc.pb.go \
  backend/tests/unit/test_probe_gateway_one_off_detection.py
git commit -m "refactor: stop delivering one-off detection over grpc stream"
```

### Task 9: 端到端验证一次性拨测

**Files:**
- Modify: `frontend/src/services/detectionApi.ts`（仅当返回字段需要补充）
- Modify: `frontend/src/pages/detection/OneOffDetection.vue`（仅当状态文案需要补充）
- Create: `backend/tests/integration/test_one_off_detection_claim_flow.py`
- Create: `docs/runbooks/one-off-detection-claim-flow.md`

**Step 1: Write the failing integration test**

```python
def test_one_off_detection_claim_flow_end_to_end():
    # create detection
    # probe claim task
    # probe submit result
    # detail endpoint returns succeeded
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source .venv/bin/activate && pytest tests/integration/test_one_off_detection_claim_flow.py -v`
Expected: FAIL before full chain is wired.

**Step 3: Write minimal implementation**

如前述任务完成后，仅补足字段和文档，不额外增加业务复杂度。

**Step 4: Run full verification**

Run:

```bash
cd backend && source .venv/bin/activate && pytest tests/unit/test_detection_service.py tests/unit/test_probe_task_api.py tests/unit/test_probe_task_result_api.py tests/unit/test_probe_gateway_one_off_detection.py -v
cd /mnt/d/workspace/OneAll/probes && go test ./internal/api ./internal/agent ./internal/transport ./cmd/probe -v
```

页面验证：
- 前端创建一次性拨测
- probe claim 成功
- 结果回传成功
- 断开 gRPC 控制流后，正在执行中的任务仍能通过 HTTP 回传结果

**Step 5: Commit**

```bash
git add frontend/src/services/detectionApi.ts \
  frontend/src/pages/detection/OneOffDetection.vue \
  backend/tests/integration/test_one_off_detection_claim_flow.py \
  docs/runbooks/one-off-detection-claim-flow.md
git commit -m "test: verify task-id based one-off detection flow"
```

## Rollout Notes

- 先在开发环境启用“probe HTTP claim/result + gRPC control-only”。
- 观察日志中的三个指标：
  - `claim_success_rate`
  - `result_submit_success_rate`
  - `scheduled_to_running_latency_ms`
- 若稳定，再考虑第二阶段把定时调度任务也迁移到同一套 task-id 短交互模型。

## Non-Goals

- 本阶段不引入 Redis/RabbitMQ/NATS 作为任务 broker。
- 本阶段不做多 `attempt_id` 重派发。
- 本阶段不移除 gRPC config/heartbeat/metrics 通道。

## Open Questions

- `claim` 接口是否允许一次返回多条任务？建议第一版固定 `limit=1`，先稳住行为。
- `published_at` 是否还要保留“对 probe 可见”的语义？建议保留，用于详情页与超时诊断。
- 是否要在 gRPC 控制流上保留 `task_available` hint？建议第二阶段再加，第一阶段先靠短轮询。

