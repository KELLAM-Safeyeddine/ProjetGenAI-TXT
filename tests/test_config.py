import pytest

from config import settings


def test_production_requires_postgresql(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'test-fixture-config-not-a-production-secret')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    with pytest.raises(RuntimeError, match='PostgreSQL'):
        settings()


def test_production_requires_private_secret(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://auto@db/auto')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('DATABASE_PASSWORD_FILE', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        settings()


def test_postgresql_url_and_secure_cookies(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', 'postgres://auto@db/auto')
    monkeypatch.setenv('SECRET_KEY', 'test-fixture-config-not-a-production-secret')
    monkeypatch.delenv('DATABASE_PASSWORD_FILE', raising=False)
    config = settings()
    assert config['SQLALCHEMY_DATABASE_URI'] == 'postgresql+psycopg://auto@db/auto'
    assert config['SESSION_COOKIE_SECURE'] is True


def test_postgresql_password_file(monkeypatch, tmp_path):
    monkeypatch.delenv('APP_ENV', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://auto@db/auto')
    monkeypatch.setenv('SECRET_KEY', 'test-fixture-config-not-a-production-secret')
    path = tmp_path / 'password'
    path.write_text('test-fixture-db-secret', encoding='utf-8')
    monkeypatch.setenv('DATABASE_PASSWORD_FILE', str(path))
    assert settings()['SQLALCHEMY_DATABASE_URI'].password == 'test-fixture-db-secret'
