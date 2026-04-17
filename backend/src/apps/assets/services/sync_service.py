from __future__ import annotations

import logging
import os
import shlex
import subprocess
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from django.db import transaction
from django.utils import timezone

from integrations.assets_sync import COLLECTOR_REGISTRY
from apps.assets.models import AssetRecord, AssetModel
from apps.assets.types import ASSET_TYPES, AssetTypeDefinition
from apps.settings.services.system_settings_service import get_integration_settings
from apps.assets.models.asset_sync_run import AssetSyncChange, AssetSyncRun
from apps.assets.services.conflict_resolver import AssetConflictResolver
from apps.assets.services.script_loader import load_sync_script

logger = logging.getLogger(__name__)

SCRIPT_ENV_VAR = "ASSET_SYNC_SCRIPT"
SCRIPT_TIMEOUT_ENV = "ASSET_SYNC_SCRIPT_TIMEOUT"


def collect_sources(source_filters: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    # Backward-compatible adapter: retain old "flat list" behavior.
    snapshots = collect_snapshots(source_filters)
    records: List[Dict[str, Any]] = []
    for _, _, rows in snapshots:
        records.extend(rows)
    return records


def collect_snapshots(source_filters: Iterable[str] | None = None) -> List[Tuple[str, str, List[Dict[str, Any]]]]:
    """
    Collect asset snapshots for each integration plugin key.

    Returns: List[(plugin_key, source_name, records)]
    """
    normalized_filters = {value.strip().lower() for value in source_filters or [] if str(value).strip()}
    snapshots: List[Tuple[str, str, List[Dict[str, Any]]]] = []

    for source_name, collector, aliases in COLLECTOR_REGISTRY:
        keys = {source_name.lower(), *(alias.lower() for alias in aliases)}
        if normalized_filters and normalized_filters.isdisjoint(keys):
            continue
        plugin_key = aliases[0] if aliases else source_name
        snapshots.append((plugin_key, source_name, list(collector())))
    return snapshots


def _build_canonical_key(
    asset_type: str | None,
    metadata: Dict[str, Any],
    record: Dict[str, Any],
    unique_fields_override: list[str] | None = None,
) -> str:
    """根据资产类型与元数据构造规范化业务主键。

    当前实现仅支持单字段主键或带简单回退顺序的单字段（例如 ip→host_name）。
    后续如果需要支持复合主键，可以在这里扩展。
    """

    atype = (asset_type or "").strip()
    definition: AssetTypeDefinition | None = ASSET_TYPES.get(atype)
    if not definition:
        return ""
    fields = unique_fields_override if unique_fields_override is not None else definition.unique_fields
    if not fields:
        return ""

    for field in fields:
        # 优先从 metadata 中取值；如无则尝试从 normalized record 顶层取一次
        value = metadata.get(field)
        if value is None:
            value = record.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        # 当前统一按小写处理，避免大小写导致的重复
        return text.lower()

    return ""


def _normalize_record(record: Dict[str, Any], type_overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    metadata = dict(record.get('metadata') or {})
    # Ensure asset_type exists for前端/后端匹配。
    # 优先使用显式 asset_type，其次回退到插件 scope 或源名称。
    asset_type = record.get('asset_type') or metadata.get('asset_type') or record.get('source')
    metadata.setdefault('asset_type', asset_type)

    override_conf = (type_overrides or {}).get(str(asset_type or "").strip()) if type_overrides else None
    unique_fields_override = None
    if isinstance(override_conf, dict):
        fields = override_conf.get("unique_fields")
        if isinstance(fields, list):
            cleaned = [str(f).strip() for f in fields if str(f).strip()]
            if cleaned:
                unique_fields_override = cleaned

    canonical_key = _build_canonical_key(str(asset_type or ""), metadata, record, unique_fields_override)

    normalized = {
        'source': record.get('source') or AssetRecord.Source.MANUAL,
        'external_id': record.get('external_id') or record.get('name') or 'unknown',
        'asset_type': asset_type or '',
        'canonical_key': canonical_key or '',
        'name': record.get('name') or metadata.get('domain') or metadata.get('host_name') or '未命名资产',
        'system_name': record.get('system_name') or metadata.get('system_name') or '',
        'owners': _ensure_str_list(record.get('owners') or metadata.get('owners') or metadata.get('owner')),
        'contacts': _ensure_str_list(
            record.get('contacts')
            or metadata.get('contacts')
            or metadata.get('alert_contacts')
        ),
        'metadata': metadata,
        'sync_status': record.get('status') or 'synced',
    }
    return normalized


def _ensure_str_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _looks_like_template_rows(rows: List[Dict[str, Any]]) -> bool:
    if len(rows) != 1:
        return False
    row = rows[0] or {}
    if str(row.get("external_id") or "").strip() != "demo-1":
        return False
    metadata = row.get("metadata") or {}
    if not isinstance(metadata, dict) or not metadata:
        return True
    return all(str(value or "").strip() == "" for value in metadata.values())


def store_assets(records: List[Dict[str, Any]]) -> None:
    # 通过系统设置支持按资产类型覆盖唯一键字段配置：
    # integrations.assets.types.<asset_type>.unique_fields = [...]
    asset_settings = get_integration_settings("assets")
    type_overrides: Dict[str, Any] = asset_settings.get("types") or {}

    for raw in records:
        record = _normalize_record(raw, type_overrides=type_overrides)
        defaults = {k: v for k, v in record.items() if k not in {'source', 'external_id'}}
        AssetRecord.objects.update_or_create(
            source=record['source'],
            external_id=record['external_id'],
            defaults=defaults,
        )


ASSET_PLUGIN_SCOPES: dict[str, dict[str, str]] = {
    "asset_zabbix_host": {"source": AssetRecord.Source.ZABBIX, "asset_type": "zabbix-host"},
    "asset_cmdb_domain": {"source": AssetRecord.Source.CMDB, "asset_type": "cmdb-domain"},
    "asset_ipmp_project": {"source": AssetRecord.Source.IPMP, "asset_type": "ipmp-project"},
    "asset_workorder_host": {"source": AssetRecord.Source.MANUAL, "asset_type": "workorder-host"},
}


def ingest_asset_snapshot(
    records: List[Dict[str, Any]],
    *,
    plugin: str | None = None,
    full_snapshot: bool = False,
    run: AssetSyncRun | None = None,
) -> Dict[str, int]:
    """
    Ingest asset records from a script return value and optionally reconcile (soft-delete) missing records.

    - Upsert by (source, external_id)
    - Mark seen records is_removed=False and last_seen_at=now
    - If full_snapshot=True: soft-delete records in the same scope that were not returned this time.
    """

    now = timezone.now()
    # 允许通过系统设置覆盖唯一键字段配置：
    #   SystemSettings.integrations["assets"]["types"][<asset_type>]["unique_fields"] = [...]
    asset_settings = get_integration_settings("assets")
    type_overrides: Dict[str, Any] = asset_settings.get("types") or {}

    normalized_rows = [_normalize_record(raw, type_overrides=type_overrides) for raw in (records or [])]
    if not normalized_rows:
        return {"fetched": 0, "created": 0, "updated": 0, "removed": 0}

    unique_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in normalized_rows:
        key = (str(row.get("source") or ""), str(row.get("external_id") or ""))
        if not key[0] or not key[1]:
            continue
        unique_by_key[key] = row

    if not unique_by_key:
        return {"fetched": 0, "created": 0, "updated": 0, "removed": 0}

    sources = {source for source, _ in unique_by_key.keys()}
    if len(sources) != 1:
        # 避免跨 source 的混合快照被误对账
        full_snapshot = False
    source = next(iter(sources))

    external_ids = [external_id for _, external_id in unique_by_key.keys()]
    existing_records = AssetRecord.objects.filter(source=source, external_id__in=external_ids)
    existing_by_external_id: dict[str, AssetRecord] = {record.external_id: record for record in existing_records}

    created_count = 0
    updated_count = 0
    restored_count = 0
    change_rows: list[AssetSyncChange] = []

    def _snapshot(record: AssetRecord) -> dict[str, Any]:
        return {
            "id": str(record.id),
            "source": record.source,
            "external_id": record.external_id,
            "name": record.name,
            "system_name": record.system_name,
            "owners": record.owners or [],
            "contacts": record.contacts or [],
            "metadata": record.metadata or {},
            "sync_status": record.sync_status,
            "is_removed": record.is_removed,
            "removed_at": record.removed_at.isoformat() if record.removed_at else None,
            "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None,
        }

    with transaction.atomic():
        for (row_source, external_id), row in unique_by_key.items():
            existing = existing_by_external_id.get(external_id)
            before = _snapshot(existing) if existing else {}
            is_restore = bool(existing and existing.is_removed)

            defaults = {k: v for k, v in row.items() if k not in {"source", "external_id"}}
            defaults.update(
                {
                    "is_removed": False,
                    "removed_at": None,
                    "last_seen_at": now,
                }
            )
            obj, created = AssetRecord.objects.update_or_create(
                source=row_source,
                external_id=external_id,
                defaults=defaults,
            )

            after = _snapshot(obj)
            if created:
                created_count += 1
                action = AssetSyncChange.Action.CREATE
            elif is_restore:
                restored_count += 1
                action = AssetSyncChange.Action.RESTORE
            else:
                updated_count += 1
                action = AssetSyncChange.Action.UPDATE

            changed_fields = []
            if before:
                for key in ["name", "system_name", "owners", "contacts", "metadata", "sync_status", "is_removed"]:
                    if before.get(key) != after.get(key):
                        changed_fields.append(key)

            if run is not None:
                change_rows.append(
                    AssetSyncChange(
                        run=run,
                        record=obj,
                        source=row_source,
                        external_id=external_id,
                        action=action,
                        changed_fields=changed_fields,
                        before=before,
                        after=after,
                    )
                )

    removed_count = 0
    if full_snapshot:
        scope = ASSET_PLUGIN_SCOPES.get(str(plugin or "").strip(), {})
        scope_asset_type = scope.get("asset_type")
        if not scope_asset_type:
            asset_types = {
                str((row.get("metadata") or {}).get("asset_type") or "").strip()
                for row in unique_by_key.values()
            }
            asset_types = {t for t in asset_types if t}
            if len(asset_types) == 1:
                scope_asset_type = next(iter(asset_types))

        if scope_asset_type:
            qs = (
                AssetRecord.objects.filter(source=source, is_removed=False)
                .filter(metadata__asset_type=scope_asset_type)
                .exclude(sync_status="manual")
                .exclude(external_id__in=external_ids)
            )
            to_remove: list[AssetRecord] = list(qs)
            removed_count = len(to_remove)
            if removed_count:
                qs.update(
                    is_removed=True,
                    removed_at=now,
                    sync_status="removed",
                    updated_at=now,
                )
                if run is not None:
                    for record in to_remove:
                        before = _snapshot(record)
                        after = dict(before)
                        after.update(
                            {
                                "is_removed": True,
                                "removed_at": now.isoformat(),
                                "sync_status": "removed",
                            }
                        )
                        change_rows.append(
                            AssetSyncChange(
                                run=run,
                                record=record,
                                source=record.source,
                                external_id=record.external_id,
                                action=AssetSyncChange.Action.SOFT_DELETE,
                                changed_fields=["is_removed", "removed_at", "sync_status"],
                                before=before,
                                after=after,
                            )
                        )

    if run is not None and change_rows:
        AssetSyncChange.objects.bulk_create(change_rows, batch_size=500)

    return {
        "fetched": len(external_ids),
        "created": created_count,
        "updated": updated_count,
        "restored": restored_count,
        "removed": removed_count,
    }


def sync_asset_model(model: AssetModel, *, run: AssetSyncRun | None = None) -> Dict[str, Any]:
    """Run the bound sync script for a given AssetModel and upsert AssetRecord rows.

    This is a lightweight adapter around `load_sync_script` and `ingest_asset_snapshot`:
    - Loads the script by model.script_id (fallback to model.key)
    - Calls run(context) with at least asset_type
    - Passes returned rows into ingest_asset_snapshot for upsert
    """

    if not model.is_active:
        raise ValueError(f"资产模型 {model.key} 已被禁用，无法同步")

    script_id = (model.script_id or model.key or "").strip()
    if not script_id:
        raise ValueError(f"资产模型 {model.key} 未绑定同步脚本")

    run_fn = load_sync_script(script_id)
    context: Dict[str, Any] = {
        "asset_type": model.key,
        "model_id": str(model.id),
        "unique_key": list(model.unique_key or []),
    }

    rows = run_fn(context) or []
    if not isinstance(rows, list):
        raise ValueError(f"脚本 {script_id} 的返回值必须是列表，当前类型为 {type(rows).__name__}")
    if _looks_like_template_rows(rows):
        raise ValueError(f"脚本 {script_id} 仍是模板示例，请修改真实同步逻辑后再执行同步")

    # 这里复用 ingest_asset_snapshot 的 upsert 逻辑：
    stats = ingest_asset_snapshot(rows, plugin=None, full_snapshot=False, run=run)
    totals = {
        "fetched": stats.get("fetched", len(rows)),
        "created": stats.get("created", 0),
        "updated": stats.get("updated", 0),
        "restored": stats.get("restored", 0),
        "removed": stats.get("removed", 0),
    }
    summary = {
        "trigger_type": "asset_model",
        "model_id": str(model.id),
        "model_key": model.key,
        "script_id": script_id,
        "totals": totals,
    }
    if run is not None:
        run.summary = summary
    logger.info(
        "sync_asset_model completed",
        extra={"model_key": model.key, "script_id": script_id, "summary": summary},
    )
    return summary


def sync_assets(
    source_filters: Sequence[str] | None = None,
    *,
    run: AssetSyncRun | None = None,
) -> Dict[str, Any]:
    script_command = os.getenv(SCRIPT_ENV_VAR)
    if script_command:
        result = run_external_sync(script_command)
        if run is not None:
            run.status = AssetSyncRun.Status.SCRIPT_TRIGGERED
            run.started_at = run.started_at or timezone.now()
            run.finished_at = timezone.now()
            run.summary = {"script": result}
            run.save(update_fields=["status", "started_at", "finished_at", "summary", "updated_at"])
        return result

    if run is None:
        records = collect_sources(source_filters)
        store_assets(records)
        return {"synced": len(records)}

    run_started_at = timezone.now()
    per_plugin: dict[str, dict[str, int]] = {}
    totals = {"fetched": 0, "created": 0, "updated": 0, "restored": 0, "removed": 0}

    snapshots = collect_snapshots(source_filters)
    for plugin_key, _, records in snapshots:
        stats = ingest_asset_snapshot(
            records,
            plugin=plugin_key,
            full_snapshot=True,
            run=run,
        )
        per_plugin[plugin_key] = stats
        for key in totals:
            totals[key] += int(stats.get(key, 0))

    conflicts = AssetConflictResolver().resolve()
    result: Dict[str, Any] = {
        "duration_ms": int((timezone.now() - run_started_at).total_seconds() * 1000),
        "totals": totals,
        "per_plugin": per_plugin,
    }
    for key, value in conflicts.items():
        if value:
            result[key] = value
    if run is not None:
        run.status = AssetSyncRun.Status.SUCCEEDED
        run.started_at = run.started_at or run_started_at
        run.finished_at = timezone.now()
        run.summary = result
        run.save(update_fields=["status", "started_at", "finished_at", "summary", "updated_at"])
    return result


def run_external_sync(command: str) -> Dict[str, Any]:
    args = shlex.split(command)
    timeout_value = int(os.getenv(SCRIPT_TIMEOUT_ENV, '300'))
    logger.info('Triggering asset sync script', extra={'command': command})
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_value,
            check=True,
        )
        logger.info('Asset sync script completed', extra={'stdout': completed.stdout.strip()[:500]})
        return {
            'status': 'script_triggered',
            'stdout': completed.stdout,
            'stderr': completed.stderr,
        }
    except subprocess.CalledProcessError as exc:
        logger.error('Asset sync script failed', extra={'returncode': exc.returncode, 'stderr': exc.stderr})
        raise
    except subprocess.TimeoutExpired:
        logger.error('Asset sync script timed out', extra={'timeout': timeout_value})
        raise
