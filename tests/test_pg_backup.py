import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'pg_backup', Path(__file__).resolve().parents[1] / 'docker/pg_backup.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_backup_rotation_only_touches_owned_files_and_preserves_two(tmp_path):
    for n in range(4):
        path = tmp_path / f'autohelp-{n}.dump'
        path.write_bytes(b'recette')
    extra = tmp_path / 'personnel.dump'
    extra.write_bytes(b'conserver')
    module.rotate(tmp_path, 2)
    assert len(list(tmp_path.glob('autohelp-*.dump'))) == 2 and extra.exists()
    with pytest.raises(ValueError):
        module.rotate(tmp_path, 1)
    with pytest.raises(ValueError):
        module.checked(tmp_path, tmp_path.parent / 'interdit.dump')


@pytest.mark.parametrize(
    'database', ['autohelp', 'postgres', 'x;drop database autohelp', 'autohelp_restore_test;']
)
def test_restore_cannot_target_live_database_or_sql(database):
    with pytest.raises(ValueError):
        module.restore('absent.dump', database)


def test_modified_backup_is_rejected_before_database_creation(tmp_path, monkeypatch):
    path = tmp_path / 'autohelp-test.dump'
    path.write_bytes(b'fixture de sauvegarde modifiee')
    path.with_suffix('.json').write_text('{"sha256":"invalide"}')

    def forbidden(*args, **kwargs):
        raise AssertionError('Aucun accès PostgreSQL avant contrôle de l’empreinte.')

    monkeypatch.setattr(module, 'run', forbidden)
    with pytest.raises(ValueError, match='Empreinte'):
        module.restore(path, 'recette_restore_test')
