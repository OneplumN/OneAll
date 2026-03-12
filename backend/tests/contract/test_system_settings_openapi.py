import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_system_settings_endpoint_defined():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/settings/system' in paths, "System settings endpoint missing in contract"

    get_operation = paths['/settings/system'].get('get')
    assert get_operation, "GET /settings/system operation missing"
    put_operation = paths['/settings/system'].get('put')
    assert put_operation, "PUT /settings/system operation missing"
    for code in ('200', '204'):
        assert code in (get_operation.get('responses', {}) | put_operation.get('responses', {})), (
            f"Expected HTTP {code} response definition for /settings/system"
        )
