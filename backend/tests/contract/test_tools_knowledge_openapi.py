import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_tools_and_knowledge_endpoints_present():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})

    # Tool endpoints
    assert '/tools/definitions' in paths
    assert '/tools/definitions/{id}/versions' in paths
    assert '/tools/definitions/{id}/execute' in paths
    assert '/tools/executions' in paths

    # Knowledge endpoints
    assert '/knowledge/articles' in paths
    assert '/knowledge/articles/{slug}' in paths
