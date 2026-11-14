import pytest

from conftest import test_database_url as database_url


def test_default_database_is_ephemeral_sqlite(tmp_path, monkeypatch):
    monkeypatch.delenv('AUTOHELP_TEST_DATABASE_URL', raising=False)
    assert database_url(tmp_path).startswith('sqlite:///')


def test_test_runner_refuses_a_production_database(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTOHELP_TEST_DATABASE_URL', 'postgresql+psycopg://auto@db/production')
    with pytest.raises(ValueError, match='dédiée'):
        database_url(tmp_path)


def test_test_runner_accepts_a_dedicated_postgresql_database(tmp_path, monkeypatch):
    url = 'postgresql+psycopg://auto@db-test/autohelp_test'
    monkeypatch.setenv('AUTOHELP_TEST_DATABASE_URL', url)
    assert database_url(tmp_path) == url
