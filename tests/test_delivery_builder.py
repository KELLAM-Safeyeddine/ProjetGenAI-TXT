import zipfile

import pytest

from scripts.build_delivery import check_destination, digest


def test_builder_refuses_local_change_before_writing(tmp_path):
    target = tmp_path / 'livraison'
    target.mkdir()
    path = target / 'README.md'
    path.write_bytes(b'modification locale')
    with pytest.raises(ValueError, match='non sauvegardée'):
        check_destination(target, {'README.md': b'nouvelle version'}, {})
    assert path.read_bytes() == b'modification locale'


def test_builder_can_adopt_only_exact_backup(tmp_path):
    target = tmp_path / 'livraison'
    target.mkdir()
    (target / 'README.md').write_bytes(b'modification locale')
    archive = tmp_path / 'backup.zip'
    with zipfile.ZipFile(archive, 'w') as stream:
        stream.writestr('livraison/README.md', b'modification locale')
    check_destination(target, {'README.md': b'nouveau'}, {}, archive)
    (target / 'README.md').write_bytes(b'autre modification')
    with pytest.raises(ValueError, match='non sauvegardée'):
        check_destination(target, {'README.md': b'nouveau'}, {}, archive)


def test_builder_keeps_unknown_files_without_deleting_them(tmp_path):
    target = tmp_path / 'livraison'
    target.mkdir()
    path = target / '.env'
    path.write_bytes(b'configuration privee')
    with pytest.raises(ValueError, match='non géré'):
        check_destination(target, {}, {})
    assert path.exists()


def test_builder_accepts_previously_generated_version(tmp_path):
    target = tmp_path / 'livraison'
    target.mkdir()
    (target / 'README.md').write_bytes(b'ancienne version')
    check_destination(target, {'README.md': b'nouveau'}, {'README.md': digest(b'ancienne version')})
