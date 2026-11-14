import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'init_production', ROOT / 'scripts/init_production.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_production_secrets_are_generated_privately_and_never_overwritten(tmp_path):
    module.initialize(tmp_path, 'autohelp.example')
    assert (tmp_path / 'secrets/postgres_password').stat().st_size > 40
    assert 'OPENAI_API_KEY=\n' in (tmp_path / '.env').read_text()
    before = (tmp_path / '.env').read_bytes()
    with pytest.raises(ValueError):
        module.initialize(tmp_path, 'autre.example')
    assert (tmp_path / '.env').read_bytes() == before
    with pytest.raises(ValueError):
        module.initialize(tmp_path / 'autre', 'https://interdit.example')


def test_production_only_publishes_proxy_and_keeps_database_private():
    text = (ROOT / 'docker-compose.production.yml').read_text(encoding='utf8')
    assert text.count('ports:') == 1 and 'internal: true' in text
    assert 'PROXY_HOPS: "1"' in text and 'POSTGRES_PASSWORD_FILE' in text
    assert 'backups:/backups' in text and 'postgres_data:/var/lib/postgresql/data' in text
