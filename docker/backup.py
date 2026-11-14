"""Copie binaire pg_dump/pg_restore sans redirection dépendante du shell hôte.

Usage : python docker/backup.py backup fichier.dump
        python docker/backup.py restore fichier.dump base_separee
"""

import re
import subprocess
import sys
from pathlib import Path


def run(args, **kwargs):
    return subprocess.run(['docker', 'compose', 'exec', '-T', 'db', *args], check=True, **kwargs)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'backup':
        path = Path(sys.argv[2])
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb') as stream:
            run(['pg_dump', '-U', 'auto', '-d', 'auto', '-Fc'], stdout=stream)
        print('Sauvegarde créée.')
    elif len(sys.argv) == 4 and sys.argv[1] == 'restore':
        target = sys.argv[3]
        if target == 'auto' or not re.fullmatch(r'[a-z][a-z0-9_]{0,40}', target):
            raise SystemExit('Utilisez une nouvelle base séparée, nom simple en minuscules.')
        run(['createdb', '-U', 'auto', target])
        with Path(sys.argv[2]).open('rb') as stream:
            run(
                ['pg_restore', '-U', 'auto', '--exit-on-error', '--no-owner', '-d', target],
                stdin=stream,
            )
        print('Restauration dans la base séparée terminée.')
    else:
        raise SystemExit(__doc__)
