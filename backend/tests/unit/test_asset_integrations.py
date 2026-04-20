from pathlib import Path

import pytest

from integrations.assets_sync import collect_all_sources, collect_sources


def test_collect_all_sources_returns_sample_data():
    records = collect_all_sources()
    assert records, "expected sample asset records"

    sources = {record['source'] for record in records}
    # 未显式配置的外部资产源不应回退到 demo 数据。
    assert {'CMDB', 'Manual'}.issubset(sources)
    assert 'Zabbix' not in sources
    assert 'IPMP' not in sources

    # Every record should contain metadata with asset_type for front-end mapping
    assert all(record.get('metadata', {}).get('asset_type') for record in records)


def test_collect_sources_filters_by_source():
    cmdb_records = collect_sources(['asset_cmdb_domain'])
    assert cmdb_records, "CMDB sample records should be returned when filtering by plugin key"
    assert all(record['source'] == 'CMDB' for record in cmdb_records)


def test_collect_sources_zabbix_requires_explicit_file(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    sample_path = repo_root / "data" / "zabbix_hosts.json"
    assert sample_path.exists(), "expected sanitized zabbix_hosts.json sample file"
    monkeypatch.setenv("ASSET_SYNC_ZABBIX_FILE", str(sample_path))
    zabbix_records = collect_sources(["Zabbix"])
    assert zabbix_records, "Zabbix records should be loaded when ASSET_SYNC_ZABBIX_FILE is set"
    assert all(record["source"] == "Zabbix" for record in zabbix_records)


def test_collect_sources_zabbix_prefers_api_when_configured(monkeypatch):
    monkeypatch.setenv("ZABBIX_API_URL", "http://zabbix.example.com/api_jsonrpc.php")
    monkeypatch.setenv("ZABBIX_API_TOKEN", "zabbix-token")
    monkeypatch.setenv("ZABBIX_VERIFY_TLS", "false")

    captured = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "result": [
                    {
                        "hostid": "10001",
                        "host": "web-node-01",
                        "name": "Web Node 01",
                        "description": "门户系统",
                        "status": "0",
                        "available": "1",
                        "maintenanceid": "0",
                        "maintenance_status": "0",
                        "proxy_hostid": "20001",
                        "groups": [{"name": "web"}],
                        "interfaces": [
                            {
                                "interfaceid": "30001",
                                "ip": "192.0.2.10",
                                "available": "1",
                                "type": "1",
                                "port": "10050",
                            }
                        ],
                    }
                ]
            }

    def fake_post(url, json=None, timeout=None, verify=None, headers=None):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        captured["verify"] = verify
        captured["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr("integrations.assets_sync.sources.zabbix.requests.post", fake_post)

    zabbix_records = collect_sources(["Zabbix"])

    assert zabbix_records, "Zabbix API records should be returned when API config is set"
    assert zabbix_records[0]["source"] == "Zabbix"
    assert zabbix_records[0]["name"] == "Web Node 01"
    assert zabbix_records[0]["metadata"]["ip"] == "192.0.2.10"
    assert zabbix_records[0]["metadata"]["host_groups"] == ["web"]
    assert captured["url"] == "http://zabbix.example.com/api_jsonrpc.php"
    assert captured["payload"]["method"] == "host.get"
    assert captured["timeout"] == 15
    assert captured["verify"] is False
    assert captured["headers"]["Content-Type"] == "application/json-rpc"


def test_collect_sources_zabbix_falls_back_to_file_when_api_call_fails(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    sample_path = repo_root / "data" / "zabbix_hosts.json"
    monkeypatch.setenv("ZABBIX_API_URL", "http://zabbix.example.com/api_jsonrpc.php")
    monkeypatch.setenv("ZABBIX_API_TOKEN", "zabbix-token")
    monkeypatch.setenv("ASSET_SYNC_ZABBIX_FILE", str(sample_path))

    def fake_post(*args, **kwargs):
        raise RuntimeError("network failed")

    monkeypatch.setattr("integrations.assets_sync.sources.zabbix.requests.post", fake_post)

    zabbix_records = collect_sources(["Zabbix"])

    assert zabbix_records, "Zabbix file records should be used as fallback when API fails"
    assert all(record["source"] == "Zabbix" for record in zabbix_records)


def test_collect_sources_ipmp_requires_explicit_file(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    sample_path = repo_root / "backend" / "src" / "integrations" / "assets_sync" / "samples" / "ipmp_projects.json"
    assert sample_path.exists(), "expected bundled ipmp_projects.json sample file"
    monkeypatch.setenv("ASSET_SYNC_IPMP_FILE", str(sample_path))
    ipmp_records = collect_sources(["IPMP"])
    assert ipmp_records, "IPMP records should be loaded when ASSET_SYNC_IPMP_FILE is set"
    assert all(record["source"] == "IPMP" for record in ipmp_records)
