import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_asset_endpoints_present():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/assets/records' in paths, '缺少 /assets/records 接口定义'
    assert '/assets/sync' in paths, '缺少 /assets/sync 接口定义'
    assert '/assets/sync/runs' in paths, '缺少 /assets/sync/runs 接口定义'
    assert '/assets/sync/runs/{run_id}' in paths, '缺少 /assets/sync/runs/{run_id} 接口定义'

    get_operation = paths['/assets/records'].get('get')
    assert get_operation and '200' in get_operation.get('responses', {}), '资产列表需定义 200 响应'

    post_operation = paths['/assets/sync'].get('post')
    responses = (post_operation or {}).get('responses', {})
    assert '202' in responses, '资产同步需定义 202 响应'
    assert '200' in responses, '资产同步需定义 200 响应（同步模式）'
