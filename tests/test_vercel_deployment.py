import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy.pool import NullPool

import config
from app import create_app, db
from scripts import build_vercel

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_native_manifest_declares_all_dependencies_and_they_import():
    assert build_vercel.verify_dependencies() == 48


def test_vercel_build_rejects_a_tool_only_manifest(tmp_path):
    (tmp_path / 'pyproject.toml').write_text('[tool.vercel]\nentrypoint="run:app"\n')
    (tmp_path / 'requirements.txt').write_text('Flask==3.1.3\n')
    with pytest.raises(ValueError, match='doivent correspondre'):
        build_vercel.verify_dependencies(tmp_path)


def test_vercel_build_rejects_a_missing_runtime_import(monkeypatch):
    def missing(module):
        raise ModuleNotFoundError(module)

    monkeypatch.setattr(build_vercel.importlib, 'import_module', missing)
    with pytest.raises(RuntimeError, match='indisponible pendant le build : flask'):
        build_vercel.verify_dependencies()


@pytest.fixture
def serverless(monkeypatch, tmp_path):
    monkeypatch.setattr(config, 'load_dotenv', lambda *args: None)
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'serverless-test-only-private-session-key')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:password@database.example/app')
    monkeypatch.setenv('RATELIMIT_STORAGE_URI', 'rediss://default:password@redis.example:6379/0')
    monkeypatch.setenv('LLM_PROVIDER', 'none')
    monkeypatch.delenv('DATABASE_PASSWORD_FILE', raising=False)
    scratch = tmp_path / 'temporary-runtime'
    monkeypatch.setattr(config.tempfile, 'gettempdir', lambda: str(scratch))
    return scratch / 'autohelp'


def test_serverless_uses_temporary_paths_and_external_database_with_no_idle_pool(serverless):
    settings = config.settings()
    assert config.instance_directory() == serverless
    assert settings['MANUAL_IMPORT_LOG'] == serverless / 'manual-import.log'
    assert settings['WEB_IMPORT_LOG'] == serverless / 'web-index.log'
    assert settings['SQLALCHEMY_DATABASE_URI'].startswith('postgresql+psycopg://')
    assert settings['SQLALCHEMY_ENGINE_OPTIONS']['poolclass'] is NullPool
    assert settings['SESSION_COOKIE_SECURE'] and settings['SESSION_COOKIE_HTTPONLY']


def test_serverless_refuses_local_mode_sqlite_or_an_ephemeral_secret(serverless, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'local')
    with pytest.raises(RuntimeError, match='APP_ENV=production'):
        config.settings()
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    with pytest.raises(RuntimeError, match='PostgreSQL'):
        config.settings()
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user@database.example/app')
    monkeypatch.delenv('SECRET_KEY')
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        config.settings()
    assert not serverless.exists()


def test_serverless_factory_starts_when_source_tree_cannot_be_written(serverless, monkeypatch):
    original = Path.mkdir

    def guarded(path, *args, **kwargs):
        if ROOT == path.resolve() or ROOT in path.resolve().parents:
            raise AssertionError('Le source doit rester en lecture seule.')
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'mkdir', guarded)
    application = create_app({'TESTING': True, 'MANUALS_DIR': serverless.parent / 'no-pdfs'})
    assert Path(application.instance_path) == serverless and serverless.is_dir()
    client = application.test_client()
    assert client.get('/health', base_url='https://autohelp.example').status_code == 200
    assert client.get('/', base_url='https://autohelp.example').status_code == 200


def test_serverless_keeps_accounts_across_app_instances(serverless, tmp_path):
    from app.models import User

    overrides = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(tmp_path / 'persistence.sqlite3'),
        'MANUALS_DIR': tmp_path / 'no-pdfs',
    }
    first = create_app(overrides)
    with first.app_context():
        db.create_all()
        user = User(name='Démo', email='cold-start@example.test', role='user')
        user.set_password('Serverless-demo-only-2026!')
        db.session.add(user)
        db.session.commit()
    second = create_app(overrides)
    client = second.test_client()
    page = client.get('/login', base_url='https://autohelp.example')
    token = re.search(r'name="csrf-token" content="([^"]+)"', page.text)[1]
    response = client.post(
        '/login',
        data={
            'email': 'cold-start@example.test',
            'password': 'Serverless-demo-only-2026!',
            'csrf_token': token,
        },
        headers={'Referer': 'https://autohelp.example/login'},
        base_url='https://autohelp.example',
    )
    assert response.status_code == 302
    page = client.get('/chat', base_url='https://autohelp.example')
    assert page.status_code == 200
    token = re.search(r'name="csrf-token" content="([^"]+)"', page.text)[1]
    reply = client.post(
        '/api/chat',
        json={'message': 'Quand changer les essuie-glaces ?'},
        headers={'X-CSRFToken': token, 'Referer': 'https://autohelp.example/chat'},
        base_url='https://autohelp.example',
    )
    assert reply.status_code == 200 and reply.json['source'] == 'faq'
    third = create_app(overrides)
    resumed = third.test_client()
    cookie = client.get_cookie('session', domain='autohelp.example')
    resumed.set_cookie('session', cookie.value, domain='autohelp.example', secure=True)
    history = resumed.get('/api/conversations', base_url='https://autohelp.example')
    assert history.status_code == 200
    assert history.json['conversations'][0]['id'] == reply.json['conversation_id']
    with third.app_context():
        db.session.remove()
        db.drop_all()


def test_vercel_build_only_publishes_static_assets_and_preserves_source(tmp_path):
    source = tmp_path / 'app/static/css'
    source.mkdir(parents=True)
    (source / 'style.css').write_text('body { color: green; }')
    private = tmp_path / 'data/manuels/dacia/test/2026/manuel.pdf'
    private.parent.mkdir(parents=True)
    private.write_bytes(b'%PDF-not-for-public')
    (tmp_path / '.env').write_text('PRIVATE=do-not-publish')
    assert build_vercel.copy_static(tmp_path) == 1
    assert (tmp_path / 'public/static/css/style.css').read_bytes() == (
        source / 'style.css'
    ).read_bytes()
    assert len(list((tmp_path / 'public').rglob('*.*'))) == 1
    assert not list((tmp_path / 'public').rglob('*.pdf'))
    assert private.read_bytes() == b'%PDF-not-for-public'


def test_vercel_build_rejects_missing_or_changed_manual_before_copy(tmp_path):
    entries = []
    for number in range(8):
        path = tmp_path / f'data/manuels/dacia/test-{number}/2026/manuel.pdf'
        path.parent.mkdir(parents=True)
        content = b'%PDF-synthetic-for-build-test'
        path.write_bytes(content)
        entries.append(
            {
                'chemin': path.relative_to(tmp_path).as_posix(),
                'sha256': hashlib.sha256(content).hexdigest(),
            }
        )
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/manuels_versionnes.json').write_text(json.dumps({'manuels': entries}))
    assert build_vercel.verify_manuals(tmp_path) == (8, len(content) * 8)
    path.write_bytes(content + b'changed')
    with pytest.raises(ValueError, match='empreinte'):
        build_vercel.verify_manuals(tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match='absente'):
        build_vercel.verify_manuals(tmp_path)


def test_vercel_upload_excludes_personal_files_but_keeps_approved_pdfs(tmp_path):
    if not shutil.which('git'):
        pytest.skip('Git non installé sur ce poste')
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    shutil.copy2(ROOT / '.vercelignore', tmp_path / '.gitignore')
    paths = [
        '.env',
        '.env.vercel',
        '.work/private.txt',
        'instance/users.sqlite3',
        'data/manuels/hyundai/test/2026/manuel.pdf',
        'data/manuels/dacia/sandero/2022/manuel.pdf',
        '.vercel/project.json',
        'public/static/js/chat.js',
    ]
    for name in paths:
        assert (
            subprocess.run(['git', '-C', str(tmp_path), 'check-ignore', '-q', name]).returncode == 0
        )
    entries = json.loads((ROOT / 'config/manuels_versionnes.json').read_text())['manuels']
    for name in [
        'app/templates/chat.html',
        'scripts/build_vercel.py',
        *[e['chemin'] for e in entries],
    ]:
        assert (
            subprocess.run(['git', '-C', str(tmp_path), 'check-ignore', '-q', name]).returncode == 1
        )
