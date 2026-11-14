"""Initialisation mono-service avant le lancement des workers Gunicorn."""
import os
from pathlib import Path
import subprocess

if os.environ.get('APP_ENV') == 'production' and not os.environ.get('SECRET_KEY', '').strip():
    raise RuntimeError('SECRET_KEY est obligatoire en production.')
subprocess.run(['flask','db','upgrade'],check=True)
subprocess.run(['flask','import-vehicules'],check=True)
directory=Path(os.environ.get('SECRET_DIR','instance'))
marker = directory / 'faq-120-v2-imported'
if not marker.exists():
    command=['flask','import-faq']
    if (directory/'faq-imported').exists():command.append('--conserver-suppressions-anciennes')
    subprocess.run(command,check=True)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
port = str(int(os.environ.get('PORT') or 5000))
os.execvp('gunicorn',['gunicorn','--bind',f'0.0.0.0:{port}','--workers','2','--timeout','40','--access-logfile','-','--error-logfile','-','run:app'])
