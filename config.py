import os
import secrets
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_dotenv(path=None):
    """Lecture simple sans exécution ; les variables du processus restent prioritaires."""
    path = Path(path or ROOT / '.env')
    if not path.is_file():
        return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key.replace('_', '').isalnum() or not key[0].isalpha():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def secret_key():
    value = os.environ.get('SECRET_KEY', '').strip()
    if value:
        if len(value) < 32:
            raise RuntimeError('SECRET_KEY doit contenir au moins 32 caractères.')
        return value
    if os.environ.get('APP_ENV') == 'production':
        raise RuntimeError('SECRET_KEY est obligatoire en production.')
    directory = Path(os.environ.get('SECRET_DIR', ROOT / 'instance'))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'session.key'
    try:
        with path.open('x', encoding='utf-8') as file:
            file.write(secrets.token_hex(32))
        path.chmod(0o600)
    except FileExistsError:
        pass
    return path.read_text(encoding='utf-8').strip()


def settings():
    load_dotenv()
    from app.services.llm_limits import limits

    url = os.environ.get('DATABASE_URL', '').strip() or 'sqlite:///' + str(
        ROOT / 'instance' / 'auto.sqlite3'
    )
    if os.environ.get('APP_ENV') == 'production' and not url.startswith(
        ('postgres://', 'postgresql://', 'postgresql+psycopg://')
    ):
        raise RuntimeError('DATABASE_URL doit désigner PostgreSQL en production.')
    if url.startswith(('postgres://', 'postgresql://')):
        url = 'postgresql+psycopg://' + url.split('://', 1)[1]
    if url.startswith('postgresql') and os.environ.get('DATABASE_PASSWORD_FILE'):
        from sqlalchemy.engine import make_url

        parsed = make_url(url)
        if not parsed.password:
            url = parsed.set(
                password=Path(os.environ['DATABASE_PASSWORD_FILE'])
                .read_text(encoding='utf-8')
                .strip()
            )
    return dict(
        **limits(),
        LLM_PROVIDER=os.environ.get('LLM_PROVIDER') or 'auto',
        DUE_SOON_DAYS=max(0, min(365, int(os.environ.get('DUE_SOON_DAYS') or 30))),
        DUE_SOON_KM=max(0, min(100000, int(os.environ.get('DUE_SOON_KM') or 1000))),
        DATA_CONTROLLER_NAME=os.environ.get('DATA_CONTROLLER_NAME', ''),
        DATA_CONTROLLER_CONTACT=os.environ.get('DATA_CONTROLLER_CONTACT', ''),
        CONVERSATION_RETENTION_DAYS=max(
            0, min(3650, int(os.environ.get('CONVERSATION_RETENTION_DAYS') or 0))
        ),
        SECRET_KEY=secret_key(),
        SQLALCHEMY_DATABASE_URI=url,
        APP_ENV=os.environ.get('APP_ENV', 'local'),
        RATELIMIT_ENABLED=True,
        RATELIMIT_STORAGE_URI=os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://',
        RATELIMIT_HEADERS_ENABLED=True,
        RATELIMIT_IN_MEMORY_FALLBACK_ENABLED=False,
        RATELIMIT_SWALLOW_ERRORS=False,
        RATELIMIT_STORAGE_OPTIONS={'wrap_exceptions': True},
        LOGIN_RATE_LIMIT=os.environ.get('LOGIN_RATE_LIMIT') or '20 per minute',
        REGISTER_RATE_LIMIT=os.environ.get('REGISTER_RATE_LIMIT') or '5 per hour',
        CHAT_RATE_LIMIT=os.environ.get('CHAT_RATE_LIMIT') or '20 per minute',
        LOGIN_MAX_FAILURES=5,
        LOGIN_FAILURE_WINDOW=900,
        LOGIN_LOCKOUT_SECONDS=900,
        MANUALS_DIR=ROOT / 'data' / 'manuels',
        MANUAL_IMPORT_LOG=ROOT / 'instance' / 'manual-import.log',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('APP_ENV') == 'production',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_REFRESH_EACH_REQUEST=False,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=os.environ.get('APP_ENV') == 'production',
        REMEMBER_COOKIE_DURATION=timedelta(days=7),
        PROXY_HOPS=int(os.environ.get('PROXY_HOPS') or 0),
        MAX_CONTENT_LENGTH=64 * 1024,
        WTF_CSRF_TIME_LIMIT=3600,
        WEB_SOURCES_PATH=ROOT / 'config/sources_fiables.json',
        WEB_IMPORT_LOG=ROOT / 'instance/web-index.log',
        DEBUG=False,
        AI_API_KEY=os.environ.get('AI_API_KEY') or None,
        **{
            name: os.environ.get(name, '').strip()
            for name in (
                'OPENAI_API_KEY',
                'OPENAI_MODEL',
                'OPENAI_BASE_URL',
                'GROQ_API_KEY',
                'GROQ_MODEL',
                'GROQ_BASE_URL',
                'SEARCH_PROVIDER',
                'SEARCH_API_KEY',
                'SEARCH_BASE_URL',
            )
        },
    )
