import pytest

from apps.analytics.services.report_service import build_detection_report


def test_build_detection_report_returns_structure(mocker):
    mocker.patch('apps.analytics.services.report_service.fetch_detection_metrics', return_value=[{'target': 'example.com', 'success_rate': 0.98}])

    report = build_detection_report(days=30)

    assert 'generated_at' in report
    assert report['summary']['total_targets'] == 1
    assert report['items'][0]['target'] == 'example.com'
