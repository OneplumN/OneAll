import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_monitoring_history_endpoint_defined() -> None:
    with CONTRACT_PATH.open('r', encoding='utf-8') as handle:
        spec = yaml.safe_load(handle)

    paths = spec.get('paths', {})
    assert '/monitoring/tasks/history' in paths, "GET /monitoring/tasks/history missing in OpenAPI contract"
    get_operation = paths['/monitoring/tasks/history'].get('get')
    assert get_operation, "GET operation definition missing for /monitoring/tasks/history"

    responses = get_operation.get('responses', {})
    assert '200' in responses, "Expected HTTP 200 response for /monitoring/tasks/history"
    assert responses['200'].get('content', {}).get('application/json', {}).get('schema'), (
        "GET /monitoring/tasks/history should declare JSON schema"
    )

