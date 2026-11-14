import time
from types import SimpleNamespace

import pytest
from conftest import PASSWORD

from app import create_app


@pytest.fixture
def secured(app):
    return create_app(
        {
            **app.config,
            'RATELIMIT_ENABLED': True,
            'RATELIMIT_STORAGE_URI': 'memory://',
            'LOGIN_MAX_FAILURES': 3,
            'LOGIN_LOCKOUT_SECONDS': 60,
            'LOGIN_RATE_LIMIT': '100 per minute',
            'REGISTER_RATE_LIMIT': '2 per hour',
            'CHAT_RATE_LIMIT': '2 per minute',
        }
    )


@pytest.fixture
def clock(monkeypatch):
    import limits.storage.memory as memory

    current = [time.time()]
    monkeypatch.setattr(memory, 'time', SimpleNamespace(time=lambda: current[0]))
    return current


def login(client, email='alice@example.test', password=PASSWORD):
    return client.post('/login', data={'email': email, 'password': password})


def test_account_lock_then_unlock_without_waiting(secured, clock):
    client = secured.test_client()
    for _ in range(3):
        assert login(client, password='incorrect').status_code == 422
    blocked = login(client)
    assert blocked.status_code == 429
    assert int(blocked.headers['Retry-After']) >= 1
    clock[0] += 61
    assert login(client).status_code == 302


def test_unknown_account_has_same_lock_response(secured):
    client = secured.test_client()
    for _ in range(3):
        login(client, email='unknown@example.test', password='incorrect')
    assert login(client, email='unknown@example.test').status_code == 429


def test_success_clears_previous_failures(secured):
    client = secured.test_client()
    for _ in range(2):
        login(client, password='incorrect')
    assert login(client).status_code == 302
    client.post('/logout')
    for _ in range(2):
        assert login(client, password='incorrect').status_code == 422
    assert login(client).status_code == 302


def test_chat_rate_limit_is_json_and_recovers(secured, clock):
    client = secured.test_client()
    login(client)
    for _ in range(2):
        assert (
            client.post(
                '/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}
            ).status_code
            == 200
        )
    response = client.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'})
    assert response.status_code == 429 and response.is_json
    assert 'Trop de tentatives' in response.json['error']
    clock[0] += 61
    assert (
        client.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}).status_code
        == 200
    )


def test_chat_limits_are_separate_for_two_accounts(secured):
    alice, bob = secured.test_client(), secured.test_client()
    login(alice)
    login(bob, email='bob@example.test')
    for _ in range(2):
        alice.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'})
    assert alice.post('/api/chat', json={'message': 'Bonjour'}).status_code == 429
    assert bob.post('/api/chat', json={'message': 'Bonjour'}).status_code == 200


def test_register_limit_counts_forged_posts(secured):
    client = secured.test_client()
    assert client.post('/register', data={}).status_code == 422
    assert client.post('/register', data={}).status_code == 422
    assert client.post('/register', data={}).status_code == 429


def test_login_ip_limit_counts_invalid_credentials(secured):
    secured.config['LOGIN_RATE_LIMIT'] = '2 per minute'
    client = secured.test_client()
    assert login(client, password='incorrect').status_code == 422
    assert login(client, password='incorrect').status_code == 422
    assert login(client, password='incorrect').status_code == 429


def test_production_refuses_per_worker_memory_storage(app):
    with pytest.raises(RuntimeError, match='Redis'):
        create_app({**app.config, 'APP_ENV': 'production', 'RATELIMIT_STORAGE_URI': 'memory://'})


def test_shared_storage_failure_does_not_disable_limits(secured, monkeypatch):
    from limits.errors import StorageError

    with secured.app_context():
        storage = secured.extensions['autohelp_limiter'].storage

    def unavailable(*args, **kwargs):
        raise StorageError(RuntimeError('backend indisponible'))

    monkeypatch.setattr(storage, 'incr', unavailable)
    assert login(secured.test_client()).status_code == 503
