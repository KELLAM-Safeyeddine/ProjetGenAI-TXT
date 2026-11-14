"""Initialisation mono-service avant le lancement des workers Gunicorn."""

import os
import subprocess

if os.environ.get('APP_ENV') == 'production' and not os.environ.get('SECRET_KEY', '').strip():
    raise RuntimeError('SECRET_KEY est obligatoire en production.')
subprocess.run(['flask', 'db', 'upgrade'], check=True)
port = str(int(os.environ.get('PORT') or 5000))
os.execvp(
    'gunicorn',
    [
        'gunicorn',
        '--bind',
        f'0.0.0.0:{port}',
        '--workers',
        '2',
        '--timeout',
        str(max(40, int(os.environ.get('LLM_TOTAL_TIMEOUT') or 20) + 20)),
        '--error-logfile',
        '-',
        'run:app',
    ],
)
