import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_audit_log_endpoint_exists():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/audit/logs' in paths, "Audit log endpoint missing in contract"

    get_operation = paths['/audit/logs'].get('get')
    assert get_operation, "GET /audit/logs operation missing"

    responses = get_operation.get('responses', {})
    assert '200' in responses, "Successful response not defined for /audit/logs"
