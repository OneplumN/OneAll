from pathlib import Path

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


def test_collect_sources_ipmp_requires_explicit_file(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    sample_path = repo_root / "backend" / "src" / "integrations" / "assets_sync" / "samples" / "ipmp_projects.json"
    assert sample_path.exists(), "expected bundled ipmp_projects.json sample file"
    monkeypatch.setenv("ASSET_SYNC_IPMP_FILE", str(sample_path))
    ipmp_records = collect_sources(["IPMP"])
    assert ipmp_records, "IPMP records should be loaded when ASSET_SYNC_IPMP_FILE is set"
    assert all(record["source"] == "IPMP" for record in ipmp_records)
