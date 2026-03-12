import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_detection_one_off_endpoint_defined():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/detection/one-off' in paths, "POST /detection/one-off missing in OpenAPI contract"
    post_operation = paths['/detection/one-off'].get('post')
    assert post_operation, "POST operation definition missing for /detection/one-off"

    responses = post_operation.get('responses', {})
    assert '202' in responses, "Expected HTTP 202 response for /detection/one-off"


def test_detection_task_detail_endpoint_defined():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/detection/tasks/{id}' in paths, "GET /detection/tasks/{id} missing in OpenAPI contract"
    get_operation = paths['/detection/tasks/{id}'].get('get')
    assert get_operation, "GET operation definition missing for /detection/tasks/{id}"
    responses = get_operation.get('responses', {})
    assert '200' in responses, "Expected HTTP 200 response for /detection/tasks/{id}"
