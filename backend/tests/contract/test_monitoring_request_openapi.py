import pathlib

import yaml

CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[3] / 'specs/001-build-oneall-platform/contracts/openapi.yaml'


def test_monitoring_request_endpoints_defined():
    with CONTRACT_PATH.open('r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    paths = spec.get('paths', {})
    assert '/monitoring/requests' in paths, "Monitoring request endpoint missing"
    assert '/monitoring/requests/{id}' in paths, "Monitoring request detail endpoint missing"
    assert '/monitoring/requests/{id}/approve' in paths, "approve endpoint missing"
    assert '/monitoring/requests/{id}/reject' in paths, "reject endpoint missing"
    assert '/monitoring/requests/{id}/resubmit' in paths, "resubmit endpoint missing"

    post = paths['/monitoring/requests'].get('post')
    get = paths['/monitoring/requests'].get('get')
    assert post and get, "/monitoring/requests must define POST and GET"
    assert '201' in post.get('responses', {}), "POST /monitoring/requests should define 201 response"

    detail_get = paths['/monitoring/requests/{id}'].get('get')
    detail_patch = paths['/monitoring/requests/{id}'].get('patch')
    assert detail_get and detail_patch, "GET/PATCH /monitoring/requests/{id} missing"

    approve_post = paths['/monitoring/requests/{id}/approve'].get('post')
    reject_post = paths['/monitoring/requests/{id}/reject'].get('post')
    assert approve_post and reject_post, "approve/reject operations missing"
    assert '200' in approve_post.get('responses', {}), "approve should define 200 response"
    assert '200' in reject_post.get('responses', {}), "reject should define 200 response"

    resubmit_post = paths['/monitoring/requests/{id}/resubmit'].get('post')
    assert resubmit_post and '200' in resubmit_post.get('responses', {}), "resubmit should define 200 response"
