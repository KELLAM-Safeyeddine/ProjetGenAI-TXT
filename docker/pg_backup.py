"""Sauvegardes atomiques ; restauration seulement dans une nouvelle base de recette."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


def environment():
    env = os.environ.copy()
    if env.get('PGPASSWORD_FILE'):
        env['PGPASSWORD'] = Path(env['PGPASSWORD_FILE']).read_text().strip()
    return env


def run(args, **kwargs):
    # Les diagnostics distants pourraient contenir des informations privées.
    result = subprocess.run(args, env=environment(), stderr=subprocess.PIPE, timeout=300, **kwargs)
    if result.returncode:
        raise RuntimeError('Commande PostgreSQL en échec ; aucun détail privé affiché.')
    return result


def checked(root, path):
    root = Path(root).resolve()
    path = Path(path)
    if path.is_symlink() or path.resolve().parent != root:
        raise ValueError('Chemin extérieur au volume de sauvegarde.')
    return path


def rotate(root, keep):
    if keep < 2:
        raise ValueError('Conserver au moins deux sauvegardes.')
    files = [
        p
        for p in Path(root).glob('autohelp-*.dump')
        if not p.is_symlink() and p.resolve().parent == Path(root).resolve()
    ]
    for path in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[keep:]:
        checked(root, path).unlink()
        sidecar = checked(root, path.with_suffix('.json'))
        if sidecar.exists():
            sidecar.unlink()


def backup(root, keep=7):
    os.umask(0o077)
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    name = (
        'autohelp-'
        + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        + '-'
        + uuid.uuid4().hex[:8]
    )
    target = checked(root, root / (name + '.dump'))
    temporary = checked(root, root / (name + '.part'))
    try:
        # -f évite toute altération binaire par le shell hôte.
        run(['pg_dump', '--format=custom', '--no-owner', '--no-acl', '--file', str(temporary)])
        run(['pg_restore', '--list', str(temporary)], stdout=subprocess.DEVNULL)
        temporary.replace(target)
        with target.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        target.with_suffix('.json').write_text(
            json.dumps(
                dict(
                    fichier=target.name,
                    sha256=digest,
                    octets=target.stat().st_size,
                    date=datetime.now(timezone.utc).isoformat(),
                )
            )
        )
        rotate(root, keep)
        print(
            json.dumps(dict(event='backup', status='ok', fichier=target.name, sha256=digest)),
            flush=True,
        )
        return target
    finally:
        if temporary.exists():
            checked(root, temporary).unlink()


def restore(path, database):
    if not re.fullmatch(
        r'[a-z][a-z0-9_]{0,40}_restore_test', database
    ) or database == os.environ.get('PGDATABASE'):
        raise ValueError('La restauration exige une nouvelle base nommée *_restore_test.')
    path = Path(path)
    metadata = json.loads(path.with_suffix('.json').read_text())
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if metadata['sha256'] != digest:
        raise ValueError('Empreinte de sauvegarde différente.')
    run(['createdb', database])
    run(
        [
            'pg_restore',
            '--exit-on-error',
            '--no-owner',
            '--no-acl',
            '--dbname',
            database,
            str(path),
        ],
        stdout=subprocess.DEVNULL,
    )
    print(json.dumps(dict(event='restore', status='ok', base=database)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loop', action='store_true')
    parser.add_argument('--restore', type=Path)
    parser.add_argument('--database')
    args = parser.parse_args()
    if args.restore:
        restore(args.restore, args.database or '')
        return
    interval = int(os.environ.get('BACKUP_INTERVAL_SECONDS') or 86400)
    keep = int(os.environ.get('BACKUP_KEEP') or 7)
    if not 60 <= interval <= 604800 or not 2 <= keep <= 365:
        raise ValueError('Intervalle ou rotation hors plage.')
    while True:
        try:
            backup(os.environ.get('BACKUP_DIR') or '/backups', keep)
        except Exception:
            print(json.dumps(dict(event='backup', status='error')), flush=True)
            if not args.loop:
                raise SystemExit(1) from None
        if not args.loop:
            return
        time.sleep(interval)


if __name__ == '__main__':
    main()
