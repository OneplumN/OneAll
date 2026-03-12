from __future__ import annotations

from apps.probes.services import probe_task_service


def test_timeout_from_metadata_supports_nested_config():
    metadata = {"config": {"timeout_seconds": 12}}
    assert probe_task_service.timeout_from_metadata(metadata) == 12


def test_expect_status_from_metadata_supports_nested_config():
    metadata = {"config": {"expect_status": "204"}}
    assert probe_task_service.expect_status_from_metadata(metadata) == 204


def test_timeout_from_metadata_falls_back_to_default():
    metadata = {"config": {"timeout_seconds": "invalid"}}
    assert probe_task_service.timeout_from_metadata(metadata) == probe_task_service.DEFAULT_TIMEOUT_SECONDS
