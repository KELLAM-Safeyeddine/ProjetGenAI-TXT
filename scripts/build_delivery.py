"""Génère la livraison propre ; refuse un écrasement local non sauvegardé."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXPECTED = {('Dacia', model, year) for model, year in (
    ('Bigster', 2026), ('Duster', 2026), ('Jogger', 2026), ('Logan', 2026),
    ('Sandero', 2021), ('Sandero', 2026), ('Sandero Stepway', 2026), ('Spring', 2026),
)}
DIRECTORIES = ('app', 'migrations', 'data', 'tests', 'docker', 'docs', 'config', 'scripts')
FILES = ('config.py', 'run.py', 'requirements.txt', 'Dockerfile', 'docker-compose.yml',
         'docker-compose.production.yml', '.dockerignore', '.env.example', '.gitignore',
         '.gitattributes', 'README.md', 'README-livraison.md', 'CHANGEMENTS.md', 'pytest.ini')
EXCLUDED = {'__pycache__', '.pytest_cache', '.git', '.venv', 'venv', '.env', '.work',
            'A_verifier.md', 'manuels', 'reports', 'rapport_evaluation.md'}


def digest(value):
    hasher = hashlib.sha256()
    if isinstance(value, bytes):
        hasher.update(value)
    else:
        with value.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                hasher.update(block)
    return hasher.hexdigest()


def approved(path):
    return (not any(part in EXCLUDED or part.startswith('.env') for part in path.parts)
            and not path.name.startswith('rapport_')
            and path.suffix.lower() not in {'.pyc', '.pyo', '.db', '.sqlite', '.sqlite3', '.dump', '.pdf', '.part', '.log'})


def collect(root):
    from app.services.manual_inventory import read_manifest, inspect_pdf
    plan = {name: root / name for name in FILES}
    for directory in DIRECTORIES:
        for path in (root / directory).rglob('*'):
            relative = path.relative_to(root)
            if path.is_file() and approved(relative):
                if path.is_symlink():
                    raise ValueError('Lien symbolique interdit dans la livraison.')
                plan[relative.as_posix()] = path
    manual_root = root / 'data/manuels'
    entries = []
    for entry in read_manifest(manual_root)['manuels']:
        if (entry['marque'], entry['modele'], entry['annee']) not in EXPECTED:
            continue
        path = manual_root / entry['chemin']
        inspected = inspect_pdf(manual_root.resolve(), path, entry)
        if inspected['statut'] != 'valide':
            raise ValueError('Manuel non validé : ' + entry['chemin'])
        entries.append({**inspected['entry'], 'statut_import': 'a_importer', 'passages_importes': 0})
        plan['manuels/' + entry['chemin']] = path
    if len(entries) != 8 or {(e['marque'], e['modele'], e['annee']) for e in entries} != EXPECTED:
        raise ValueError('La livraison exige les huit notices validées, sans substitution.')
    metadata = (json.dumps({'manuels': entries}, ensure_ascii=False, indent=2) + '\n').encode()
    plan['manuels/index.json'] = metadata
    plan['data/manuels/index.json'] = metadata
    plan['manuels/README.md'] = ('# Notices Dacia\n\nHuit notices validées, montées en lecture seule. '
        'Documents protégés par les droits du constructeur ; ne pas redistribuer hors du cadre autorisé.\n'
        'Remplacement : conserver modèle et millésime exacts, actualiser la preuve et le SHA-256 dans '
        'index.json, puis lancer flask import-manuels --lecture-seule.\n').encode()
    plan['data/manuels/README.md'] = b'# Manuels\n\nLes PDF fournis sont dans ../../manuels/. Voir README-livraison.md.\n'
    rows = list(csv.DictReader((manual_root / 'sources.csv').read_text(encoding='utf-8-sig').splitlines()))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(r for r in rows if (r['marque'], r['modele'], int(r['annee'])) in EXPECTED)
    plan['manuels/sources.csv'] = plan['data/manuels/sources.csv'] = buffer.getvalue().encode()
    plan['docker-compose.yml'] = (root / 'docker-compose.yml').read_text(encoding='utf8').replace(
        './data/manuels:/app/data/manuels:ro', './manuels:/app/data/manuels:ro').encode()
    plan['docs/CONTENU_LIVRAISON.txt'] = ('\n'.join(sorted(set(plan) | {'docs/CONTENU_LIVRAISON.txt'})) + '\n').encode()
    return plan


def check_destination(target, plan, previous, backup=None):
    """Prévalidation complète avant la première écriture ; aucun fichier supprimé."""
    if not target.exists():
        return
    archive = zipfile.ZipFile(backup) if backup else None
    try:
        for existing in target.rglob('*'):
            if existing.is_symlink():
                raise ValueError('Lien symbolique présent dans la cible ; aucune écriture.')
            if not existing.is_file():
                continue
            name = existing.relative_to(target).as_posix()
            if name not in plan:
                raise ValueError('Fichier non géré à conserver ou retirer explicitement : ' + name)
            current_hash = digest(existing)
            if current_hash in {previous.get(name), digest(plan[name])}:
                continue
            saved = None
            if archive:
                try:
                    with archive.open('livraison/' + name) as stream:
                        hasher = hashlib.sha256()
                        for block in iter(lambda: stream.read(1024 * 1024), b''):
                            hasher.update(block)
                        saved = hasher.hexdigest()
                except KeyError:
                    pass
            if saved != current_hash:
                raise ValueError('Modification locale non sauvegardée : ' + name)
    finally:
        if archive:
            archive.close()


def build(root=ROOT, backup=None):
    root = root.resolve()
    target = root.parent / 'livraison'
    if target.resolve() != target or target == root:
        raise ValueError('Cible de livraison inattendue.')
    plan = collect(root)
    state = root / '.work/delivery-manifest.json'
    previous = json.loads(state.read_text(encoding='utf8')) if state.exists() else {}
    check_destination(target, plan, previous, backup)
    from scripts.audit_git import SECRET_PATTERNS
    for name, value in plan.items():
        if name.lower().endswith('.pdf'):
            continue
        content = value if isinstance(value, bytes) else value.read_bytes()
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            raise ValueError('Secret potentiel dans ' + name + ' ; contenu masqué.')
    target.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, value in plan.items():
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            destination.write_bytes(value)
        else:
            shutil.copy2(value, destination)
        manifest[name] = digest(destination)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    print(f'Livraison générée : {target} ({len(manifest)} fichiers, huit PDF autorisés).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup-archive', type=Path, help='ZIP contenant la copie exacte avant remplacement local.')
    args = parser.parse_args()
    build(backup=args.backup_archive)
