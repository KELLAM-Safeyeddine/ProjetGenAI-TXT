"""Génère la livraison autonome dans le dossier frère, sans fichiers locaux.

Usage depuis le projet : python scripts/build_delivery.py
La cible doit être absente ou avoir été créée par ce script (état de contrôle local).
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT.parent/'livraison'
DIRECTORIES=('app','migrations','data','tests','docker','docs','config')
FILES=('config.py','run.py','requirements.txt','Dockerfile','docker-compose.yml',
       'docker-compose.production.yml','.dockerignore','.env.example','.gitignore',
       '.gitattributes','README.md','pytest.ini')
FILES += ('scripts/download_manuals.py','data/manuels/README.md','data/manuels/index.json','data/manuels/sources.csv')
STATE=ROOT/'.work'/'delivery-manifest.json'
EXCLUDED={'__pycache__','.pytest_cache','.git','.venv','venv','.env','A_verifier.md','manuels','rapport_evaluation.md'}

def approved(path):
    return not any(part in EXCLUDED for part in path.parts) and path.suffix.lower() not in {'.pyc','.pyo','.db','.sqlite','.sqlite3','.dump','.pdf','.part'}

def build():
    target=TARGET.resolve()
    if target!=ROOT.parent.resolve()/'livraison' or target==ROOT:
        raise RuntimeError('Cible de livraison inattendue.')
    sources={Path(name):ROOT/name for name in FILES}
    for directory in DIRECTORIES:
        for path in (ROOT/directory).rglob('*'):
            relative=path.relative_to(ROOT)
            if path.is_file() and approved(relative):
                sources[relative]=path
    if target.exists() and any(target.iterdir()):
        if not STATE.is_file():
            raise RuntimeError('La cible contient des fichiers non gérés ; aucun écrasement automatique.')
        previous=json.loads(STATE.read_text(encoding='utf-8'))
        for name in previous:
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise RuntimeError('Manifeste invalide.')
            existing=(target/relative).resolve()
            if target not in existing.parents:
                raise RuntimeError('Chemin hors livraison.')
            if existing.is_file() and relative not in sources:
                existing.unlink()
    target.mkdir(parents=True,exist_ok=True)
    manifest={}
    for relative,source in sources.items():
        destination=target/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
        manifest[relative.as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Livraison générée : {target} ({len(manifest)} fichiers applicatifs).')

if __name__=='__main__':
    build()
