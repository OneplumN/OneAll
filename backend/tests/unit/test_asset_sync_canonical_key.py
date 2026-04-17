from __future__ import annotations

from typing import Any, Dict

import pytest

from apps.assets.services.sync_service import _normalize_record


def _build_cmdb_domain(domain: str) -> Dict[str, Any]:
  return {
      "source": "CMDB",
      "external_id": f"domain:{domain}",
      "name": domain,
      "metadata": {
          "asset_type": "cmdb-domain",
          "domain": domain,
      },
  }


@pytest.mark.parametrize(
    "asset_type,raw,expected_key",
    [
        ("cmdb-domain", _build_cmdb_domain("OneAll.CN"), "oneall.cn"),
        (
            "zabbix-host",
            {
                "source": "Zabbix",
                "external_id": "zbx:redis-master",
                "name": "redis-master",
                "metadata": {"asset_type": "zabbix-host", "ip": "10.0.0.5"},
            },
            "10.0.0.5",
        ),
        (
            "zabbix-host",
            {
                "source": "Zabbix",
                "external_id": "zbx:web-node-01",
                "name": "WEB-NODE-01",
                "metadata": {"asset_type": "zabbix-host", "host_name": "WEB-NODE-01"},
            },
            "web-node-01",
        ),
        (
            "ipmp-project",
            {
                "source": "IPMP",
                "external_id": "ipmp:APP-OPS-001",
                "name": "APP-OPS-001",
                "metadata": {"asset_type": "ipmp-project", "app_code": "APP-OPS-001"},
            },
            "app-ops-001",
        ),
        (
            "workorder-host",
            {
                "source": "Manual",
                "external_id": "workorder:10.30.1.5",
                "name": "payment-worker-01",
                "metadata": {"asset_type": "workorder-host", "ip": "10.30.1.5"},
            },
            "10.30.1.5",
        ),
    ],
)
@pytest.mark.django_db
def test_normalize_record_sets_canonical_key(asset_type: str, raw: Dict[str, Any], expected_key: str) -> None:
    record = _normalize_record(raw)

    assert record["asset_type"] == asset_type
    assert record["canonical_key"] == expected_key

