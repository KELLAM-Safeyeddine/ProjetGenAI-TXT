"""Démarrage Render : migrations puis Gunicorn ; aucun import PDF au redémarrage."""

import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def server_command(environ):
    try:
        port = int(environ.get('PORT') or 10000)
        total = float(environ.get('LLM_TOTAL_TIMEOUT') or 20)
        if not 1 <= port <= 65535 or not math.isfinite(total) or not 5 <= total <= 90:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('PORT ou LLM_TOTAL_TIMEOUT invalide ; valeurs non affichées.') from None
    return [
        'gunicorn',
        '--bind',
        f'0.0.0.0:{port}',
        '--workers',
        '1',
        '--threads',
        '2',
        '--timeout',
        str(max(40, math.ceil(total) + 20)),
        '--error-logfile',
        '-',
        'run:app',
    ]


def main():
    environ = os.environ.copy()
    if environ.get('APP_ENV') != 'production':
        raise ValueError('Ce démarrage Render exige APP_ENV=production.')
    command = server_command(environ)
    environ['FLASK_SKIP_DOTENV'] = '1'
    for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        environ.setdefault(variable, '1')
    os.chdir(ROOT)
    subprocess.run(
        [sys.executable, '-m', 'flask', '--app', 'run', 'db', 'upgrade'],
        env=environ,
        check=True,
    )
    os.execvpe('gunicorn', command, environ)


if __name__ == '__main__':
    main()
