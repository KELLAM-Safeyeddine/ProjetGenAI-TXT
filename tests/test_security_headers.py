from datetime import timedelta

import pytest
from flask import jsonify, request

from app import create_app
from conftest import PASSWORD


@pytest.mark.parametrize('path', ['/', '/login', '/register', '/health', '/chat'])
def test_security_headers_cover_public_and_private_responses(client, path):
    response = client.get(path)
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    policy = response.headers['Content-Security-Policy']
    assert "default-src 'self'" in policy and "frame-ancestors 'none'" in policy
    assert "object-src 'none'" in policy
    assert 'unsafe-inline' not in policy and 'unsafe-eval' not in policy


def test_login_sets_expiring_httponly_samesite_cookie(client, app):
    response = client.post('/login', data={'email': 'alice@example.test', 'password': PASSWORD})
    cookie = response.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie and 'Expires=' in cookie
    assert app.config['PERMANENT_SESSION_LIFETIME'] == timedelta(hours=8)
    assert app.config['SESSION_REFRESH_EACH_REQUEST'] is False


def test_https_cookie_and_hsts_and_remember_configuration(app):
    secure = create_app({**app.config, 'SESSION_COOKIE_SECURE': True, 'REMEMBER_COOKIE_SECURE': True})
    response = secure.test_client().post('/login', data={'email': 'alice@example.test', 'password': PASSWORD}, base_url='https://localhost')
    assert 'Secure' in response.headers['Set-Cookie']
    assert response.headers['Strict-Transport-Security'] == 'max-age=31536000'
    assert secure.config['REMEMBER_COOKIE_HTTPONLY'] is True
    assert secure.config['REMEMBER_COOKIE_SAMESITE'] == 'Lax'
    assert 'Strict-Transport-Security' not in app.test_client().get('/').headers


@pytest.mark.parametrize('hops,expected_ip,expected_scheme', [(0, '127.0.0.1', 'http'), (1, '198.51.100.8', 'https')])
def test_forwarded_headers_are_trusted_only_when_configured(app, hops, expected_ip, expected_scheme):
    proxied = create_app({**app.config, 'PROXY_HOPS': hops})
    @proxied.get('/test-proxy')
    def probe():
        return jsonify(ip=request.remote_addr, scheme=request.scheme, host=request.host)
    response = proxied.test_client().get('/test-proxy', headers={
        'X-Forwarded-For': '198.51.100.8', 'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'untrusted.invalid'})
    assert response.json == {'ip': expected_ip, 'scheme': expected_scheme, 'host': 'localhost'}


def test_invalid_proxy_chain_is_rejected(app):
    with pytest.raises(RuntimeError, match='PROXY_HOPS'):
        create_app({**app.config, 'PROXY_HOPS': 99})
