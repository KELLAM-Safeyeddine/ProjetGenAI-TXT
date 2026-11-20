"""Vérifie l'index Git avant commit, sans afficher de secret ni modifier le dépôt."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

APPROVED_MANUALS = {
    row['chemin']: row['sha256']
    for row in json.loads(
        (Path(__file__).resolve().parents[1] / 'config/manuels_versionnes.json').read_text(
            encoding='utf-8'
        )
    )['manuels']
}

PRIVATE_PARTS = {
    '.work',
    '.venv',
    'venv',
    '__pycache__',
    '.pytest_cache',
    '.ruff_cache',
    '.mypy_cache',
    'instance',
    'uploads',
    'backups',
    'livraison',
    'videoiscreenshots-demo',
    'node_modules',
}
PRIVATE_SUFFIXES = {
    '.pdf',
    '.db',
    '.sqlite',
    '.sqlite3',
    '.pyc',
    '.pyo',
    '.log',
    '.dump',
    '.key',
    '.pem',
    '.p12',
    '.bak',
    '.part',
    '.mp4',
    '.webm',
}
SECRET_PATTERNS = (
    re.compile(rb'(?:gsk_|sk-(?:proj-|svcacct-)?)[A-Za-z0-9_-]{24,}'),
    re.compile(rb'AKIA[A-Z0-9]{16}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
)


def git(repo, *args):
    return subprocess.run(
        ['git', '-C', str(repo), *args],
        check=True,
        capture_output=True,
    ).stdout


def forbidden_path(name):
    path = PurePosixPath(name)
    parts = {part.lower() for part in path.parts}
    filename = path.name.lower()
    if parts & PRIVATE_PARTS:
        return True
    if filename.startswith('.env') and filename != '.env.example':
        return True
    if path.suffix.lower() in PRIVATE_SUFFIXES and not (
        path.suffix.lower() == '.pdf' and name in APPROVED_MANUALS
    ):
        return True
    if re.search(r'\.(?:db|sqlite3?)-(?:wal|shm|journal)$', filename):
        return True
    if name.startswith('data/rapport_') or filename == 'a_verifier.md':
        return True
    return False


def audit_index(repo):
    """Analyse les blobs indexés, même si une autre version existe sur disque."""
    names = [
        name.decode('utf-8')
        for name in git(repo, 'ls-files', '-z', '--cached').split(b'\0')
        if name
    ]
    failures = []
    for name in names:
        if forbidden_path(name):
            failures.append((name, 'fichier privé, généré ou PDF interdit'))
            continue
        content = git(repo, 'show', ':' + name)
        if name in APPROVED_MANUALS and (
            not content.startswith(b'%PDF-')
            or hashlib.sha256(content).hexdigest() != APPROVED_MANUALS[name]
        ):
            failures.append((name, 'notice différente du PDF Dacia validé (empreinte SHA-256)'))
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            failures.append((name, 'secret potentiel détecté (contenu masqué)'))
        if PurePosixPath(name).name == '.env.example':
            lines = content.decode('utf-8-sig').splitlines()
            if any(
                line.strip()
                and not line.lstrip().startswith('#')
                and not re.fullmatch(r'[A-Z][A-Z0-9_]*=', line.strip())
                for line in lines
            ):
                failures.append((name, 'les variables du modèle doivent être vides'))
    return len(names), failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        count, failures = audit_index(args.repo)
    except (subprocess.CalledProcessError, UnicodeError):
        print('ÉCHEC : index Git illisible ; aucun contenu affiché.', file=sys.stderr)
        return 2
    for path, reason in failures:
        print(f'ÉCHEC : {path} : {reason}', file=sys.stderr)
    if failures:
        return 1
    print(f'Index Git vérifié : {count} fichiers, aucun élément interdit ni secret reconnu.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
