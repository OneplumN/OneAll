import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_code_repository_paths_exist():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/tools/repository/upload' in paths
    assert '/tools/repository/rollback' in paths

    upload_post = paths['/tools/repository/upload'].get('post')
    assert upload_post, 'POST /tools/repository/upload missing'

    rollback_post = paths['/tools/repository/rollback'].get('post')
    assert rollback_post, 'POST /tools/repository/rollback missing'
