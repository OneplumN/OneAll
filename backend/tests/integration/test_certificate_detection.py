from datetime import datetime, timedelta

from apps.monitoring.services import detection_certificate


def test_certificate_valid(monkeypatch):
    fake_cert = {
        'notAfter': (datetime.utcnow() + timedelta(days=30)).strftime('%b %d %H:%M:%S %Y GMT'),
        'issuer': ((('commonName', 'Test CA'),),),
        'subject': ((('commonName', 'example.com'),),),
    }

    monkeypatch.setattr(
        detection_certificate,
        'fetch_certificate_info',
        lambda target: fake_cert,
    )

    report = detection_certificate.analyze_certificate('https://example.com')

    assert report.status == detection_certificate.CertificateStatus.VALID
    assert report.days_until_expiry == 30
    assert report.issuer == 'Test CA'


def test_certificate_expired(monkeypatch):
    fake_cert = {
        'notAfter': (datetime.utcnow() - timedelta(days=1)).strftime('%b %d %H:%M:%S %Y GMT'),
        'issuer': ((('commonName', 'Test CA'),),),
        'subject': ((('commonName', 'expired.com'),),),
    }

    monkeypatch.setattr(
        detection_certificate,
        'fetch_certificate_info',
        lambda target: fake_cert,
    )

    report = detection_certificate.analyze_certificate('https://expired.com')

    assert report.status == detection_certificate.CertificateStatus.EXPIRED
    assert report.days_until_expiry == -1
