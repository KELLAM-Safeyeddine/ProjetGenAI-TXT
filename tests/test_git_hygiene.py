"""L'audit porte sur ce qui sera commité, jamais seulement sur le disque."""
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.audit_git import audit_index


@pytest.fixture
def repository(tmp_path):
    if not shutil.which('git'):
        pytest.skip('Git non installé sur ce poste')
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    source = Path(__file__).resolve().parents[1] / '.gitignore'
    shutil.copy2(source, tmp_path / '.gitignore')
    return tmp_path


def stage(repo, name, content, force=False):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    subprocess.run(['git', '-C', str(repo), 'add', *(['-f'] if force else []), '--', name], check=True, capture_output=True)
    return path


def test_private_files_are_ignored_and_metadata_can_be_shared(repository):
    private = ['.env', '.env.production', '.work/private.txt', 'instance/db.sqlite3',
               'data/manuels/dacia/modele/2026/manuel.PDF', 'ailleurs/notice.pdf',
               'backup.db-wal', 'journal.log', 'data/rapport_evaluation.md',
               'VideoIScreenshots-demo/video.mp4']
    for name in private:
        result = subprocess.run(['git', '-C', str(repository), 'check-ignore', '-q', '--', name])
        assert result.returncode == 0, name
    for name in ['.env.example', 'data/manuels/README.md', 'data/manuels/index.json', 'data/manuels/sources.csv']:
        result = subprocess.run(['git', '-C', str(repository), 'check-ignore', '-q', '--', name])
        assert result.returncode == 1, name


@pytest.mark.parametrize('name', ['manuel.PDF', '.env', 'private.sqlite3', 'private.db-wal'])
def test_forced_private_addition_is_rejected(repository, name):
    stage(repository, name, 'données privées de test', force=True)
    count, failures = audit_index(repository)
    assert count == 1
    assert failures and failures[0][0] == name


def test_secret_is_checked_in_staged_version_even_if_worktree_was_cleaned(repository):
    fake_key = 'gsk_' + 'x' * 32
    path = stage(repository, 'settings.txt', fake_key)
    path.write_text('version nettoyée mais non indexée', encoding='utf-8')
    _, failures = audit_index(repository)
    assert failures and 'secret potentiel' in failures[0][1]
    assert fake_key not in str(failures)


def test_clean_code_and_empty_configuration_are_accepted(repository):
    stage(repository, 'run.py', 'print("AutoHELP")\n')
    stage(repository, '.env.example', '# configuration privée\nGROQ_API_KEY=\nPORT=\n')
    assert audit_index(repository) == (2, [])


def test_configuration_example_must_not_contain_values(repository):
    stage(repository, '.env.example', 'GROQ_API_KEY=valeur-indésirable\n')
    _, failures = audit_index(repository)
    assert failures and 'vides' in failures[0][1]
