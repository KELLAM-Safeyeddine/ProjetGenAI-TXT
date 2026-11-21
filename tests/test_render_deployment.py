import os
import subprocess
import sys

import pytest

from scripts import render_manage, start_render


@pytest.fixture
def private_config(tmp_path):
    path = tmp_path / '.env.render'
    path.write_text(
        'APP_ENV=production\nSECRET_KEY='
        + 'x' * 48
        + '\nDATABASE_URL=postgresql+psycopg://operator:password@neon.example/autohelp?sslmode=require'
        + '\nRATELIMIT_STORAGE_URI=rediss://default:password@redis.example:6379/0\n',
        encoding='utf-8',
    )
    return path


def test_render_operator_uses_only_private_target_and_cannot_inherit_local_keys(private_config):
    source = {
        'DATABASE_URL': 'sqlite:///personal.sqlite3',
        'GROQ_API_KEY': 'local-provider-secret',
        'OPENAI_API_KEY': 'other-local-secret',
        'SEARCH_API_KEY': 'search-local-secret',
        'AI_API_KEY': 'old-local-secret',
        'DATABASE_PASSWORD_FILE': '/private/password',
        'PATH': os.environ.get('PATH', ''),
    }
    environ = render_manage.environment_from_file(private_config, source)
    assert environ['DATABASE_URL'].startswith('postgresql+psycopg://')
    assert all(
        secret not in str(environ) for secret in ('local-provider-secret', 'other-local-secret')
    )
    assert environ['LLM_PROVIDER'] == 'none' and environ['FLASK_SKIP_DOTENV'] == '1'
    assert not environ['DATABASE_PASSWORD_FILE'] and not environ['AI_API_KEY']
    assert source['GROQ_API_KEY'] == 'local-provider-secret'


def test_flask_settings_cannot_fall_back_to_personal_dotenv(private_config, monkeypatch, tmp_path):
    import config

    (tmp_path / '.env').write_text(
        'DATABASE_URL=sqlite:///personal.sqlite3\nGROQ_API_KEY=personal-provider-secret\n'
    )
    environ = render_manage.environment_from_file(private_config)
    names = {
        line.split('=', 1)[0]
        for line in (render_manage.ROOT / '.env.example').read_text().splitlines()
        if line and not line.startswith('#')
    }
    for name in names:
        monkeypatch.setenv(name, environ[name])
    monkeypatch.setattr(config, 'ROOT', tmp_path)
    settings = config.settings()
    assert settings['SQLALCHEMY_DATABASE_URI'].startswith('postgresql+psycopg://')
    assert not settings['GROQ_API_KEY'] and settings['LLM_PROVIDER'] == 'none'


@pytest.mark.parametrize(
    ('before', 'after'),
    [
        ('APP_ENV=production', 'APP_ENV=local'),
        ('postgresql+psycopg://', 'sqlite://'),
        ('rediss://', 'redis://'),
        (':6379/0', ':invalid/0'),
        ('SECRET_KEY=' + 'x' * 48, 'SECRET_KEY=short'),
    ],
)
def test_render_operator_rejects_incomplete_or_unsafe_private_configuration(
    private_config, before, after
):
    private_config.write_text(private_config.read_text().replace(before, after))
    with pytest.raises(ValueError):
        render_manage.environment_from_file(private_config)


def test_render_operator_does_not_execute_text_and_masks_invalid_config(private_config, capsys):
    private_config.write_text(private_config.read_text() + 'UNKNOWN=very-private-value\n')
    assert render_manage.main(['verifier', '--env-file', str(private_config)]) == 2
    assert 'very-private-value' not in capsys.readouterr().err
    private_config.write_text(private_config.read_text().replace('UNKNOWN', 'DATA_CONTROLLER_NAME'))
    marker = '$(touch should-never-exist)'
    private_config.write_text(private_config.read_text().replace('very-private-value', marker))
    assert render_manage.environment_from_file(private_config)['DATA_CONTROLLER_NAME'] == marker


def test_render_operator_initializes_schema_then_read_only_manual_import(
    private_config, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        render_manage.subprocess, 'run', lambda args, **kwargs: calls.append((args, kwargs))
    )
    assert render_manage.main(['initialiser', '--env-file', str(private_config)]) == 0
    assert [args[5:] for args, _ in calls] == [
        ['db', 'upgrade'],
        ['import-manuels', '--lecture-seule'],
    ]
    assert all(args[:5] == [sys.executable, '-m', 'flask', '--app', 'run'] for args, _ in calls)
    assert all(kwargs['check'] and kwargs['env']['LLM_PROVIDER'] == 'none' for _, kwargs in calls)
    assert all('shell' not in kwargs for _, kwargs in calls)


def test_render_operator_stops_before_import_when_migration_fails(private_config, monkeypatch):
    calls = []

    def fail(args, **kwargs):
        calls.append(args)
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(render_manage.subprocess, 'run', fail)
    assert render_manage.main(['initialiser', '--env-file', str(private_config)]) == 1
    assert len(calls) == 1


def test_render_operator_admin_creation_keeps_existing_hidden_cli(private_config, monkeypatch):
    calls = []
    monkeypatch.setattr(render_manage.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    assert render_manage.main(['creer-admin', '--env-file', str(private_config)]) == 0
    assert calls[0][5:] == ['create-admin']


def test_render_start_binds_assigned_port_and_limits_workers():
    args = start_render.server_command({'PORT': '15432', 'LLM_TOTAL_TIMEOUT': '90'})
    assert args[args.index('--bind') + 1] == '0.0.0.0:15432'
    assert args[args.index('--workers') + 1] == '1'
    assert args[args.index('--threads') + 1] == '2'
    assert int(args[args.index('--timeout') + 1]) > 90
    assert args[-1] == 'run:app'


@pytest.mark.parametrize('value', ['invalid-private-value', '0', '70000'])
def test_render_start_refuses_invalid_port_without_echoing_value(value):
    with pytest.raises(ValueError) as error:
        start_render.server_command({'PORT': value})
    assert value not in str(error.value)


def test_render_start_never_reindexes_pdfs_on_restart(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('PORT', '10000')
    calls = []
    monkeypatch.setattr(start_render.os, 'chdir', lambda path: None)
    monkeypatch.setattr(start_render.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    monkeypatch.setattr(start_render.os, 'execvpe', lambda name, args, env: calls.append(args))
    start_render.main()
    assert calls[0] == [sys.executable, '-m', 'flask', '--app', 'run', 'db', 'upgrade']
    assert calls[1][0] == 'gunicorn'
    assert 'import-manuels' not in str(calls)
