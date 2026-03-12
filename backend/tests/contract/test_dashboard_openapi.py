import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_dashboard_overview_endpoint_exists():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/dashboard/overview/' in paths, "Dashboard overview endpoint missing in contract"

    get_operation = paths['/dashboard/overview/'].get('get')
    assert get_operation, "GET /dashboard/overview/ operation missing"
    responses = get_operation.get('responses', {})
    assert '200' in responses, "Successful response not defined for /dashboard/overview/"


def test_dashboard_alerts_and_todos_exist():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})

    for endpoint in [
        '/dashboard/alerts-summary/',
        '/dashboard/todos/',
        '/dashboard/detection-grid/',
        '/dashboard/certificate-alerts/',
    ]:
        assert endpoint in paths, f"{endpoint} endpoint missing in contract"
        operation = paths[endpoint].get('get')
        assert operation, f"GET {endpoint} operation missing"
        responses = operation.get('responses', {})
        assert '200' in responses, f"Successful response not defined for {endpoint}"
