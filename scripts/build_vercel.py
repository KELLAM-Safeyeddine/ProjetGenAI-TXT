"""Prépare uniquement les ressources publiques et vérifie les huit notices du paquet."""

import hashlib
import importlib
import json
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_dependencies(root=ROOT):
    root = Path(root)
    manifest = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))
    declared = manifest.get('project', {}).get('dependencies', [])
    expected = [
        line.strip()
        for line in (root / 'requirements.txt').read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    ]
    if not declared or sorted(declared) != sorted(expected):
        raise ValueError('Les dépendances pyproject.toml et requirements.txt doivent correspondre.')
    # Aucun démarrage Flask, accès base, secret ni appel distant pendant le build.
    for module in ('flask', 'sqlalchemy', 'redis', 'psycopg', 'sklearn', 'pdfplumber'):
        try:
            importlib.import_module(module)
        except ImportError:
            raise RuntimeError(
                f'Dépendance Python indisponible pendant le build : {module}'
            ) from None
    return len(declared)


def verify_manuals(root=ROOT):
    root = Path(root).resolve()
    entries = json.loads((root / 'config/manuels_versionnes.json').read_text(encoding='utf-8'))[
        'manuels'
    ]
    if len(entries) != 8:
        raise ValueError('Le paquet doit contenir les huit notices Dacia validées.')
    total = 0
    for row in entries:
        path = root / row['chemin']
        if (
            path.is_symlink()
            or root / 'data/manuels/dacia' not in path.resolve().parents
            or not path.is_file()
        ):
            raise ValueError('Une notice Dacia validée est absente ou son chemin est invalide.')
        with path.open('rb') as stream:
            if stream.read(5) != b'%PDF-':
                raise ValueError('Signature PDF invalide dans les notices Dacia.')
            stream.seek(0)
            if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
                raise ValueError('Une notice Dacia diffère de son empreinte vérifiée.')
        total += path.stat().st_size
    return len(entries), total


def copy_static(root=ROOT):
    root = Path(root).resolve()
    source = root / 'app/static'
    public = root / 'public'
    target = public / 'static'
    if any(path.is_symlink() for path in (source, public, target)):
        raise ValueError('Lien symbolique interdit pour les ressources publiques.')
    if root not in target.resolve().parents or not source.is_dir():
        raise ValueError('Répertoire statique absent ou destination invalide.')
    for directory in (source, target):
        if directory.exists() and any(path.is_symlink() for path in directory.rglob('*')):
            raise ValueError('Lien symbolique interdit dans les ressources statiques.')
    shutil.copytree(source, target, dirs_exist_ok=True)
    return sum(path.is_file() for path in target.rglob('*'))


def main():
    dependencies = verify_dependencies()
    count, size = verify_manuals()
    assets = copy_static()
    print(
        f'Build Vercel : {dependencies} dépendances déclarées et imports vérifiés ; '
        f'{count} notices vérifiées ({size} octets), {assets} ressources statiques.'
    )


if __name__ == '__main__':
    main()
