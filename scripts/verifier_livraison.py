"""Contrôle du paquet avant partage, sans écrire de base, clé ou cache local."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.dont_write_bytecode=True
EXPECTED={('Dacia',m,y) for m,y in (
    ('Bigster',2026),('Duster',2026),('Jogger',2026),('Logan',2026),
    ('Sandero',2021),('Sandero',2026),('Sandero Stepway',2026),('Spring',2026))}


def verify():
    from app.services.manual_inventory import read_manifest,inspect_pdf
    from pypdf import PdfReader
    root=ROOT/'manuels';entries=read_manifest(root)['manuels']
    identities={(e['marque'],e['modele'],e['annee']) for e in entries}
    if identities!=EXPECTED or len(entries)!=8:raise ValueError('Le manifeste ne correspond pas aux huit versions validées.')
    expected_paths={(root/e['chemin']).resolve() for e in entries}
    actual={p.resolve() for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf'}
    if expected_paths!=actual:raise ValueError('PDF manquant ou PDF supplémentaire hors périmètre.')
    for entry in sorted(entries,key=lambda e:(e['modele'],e['annee'])):
        path=(root/entry['chemin']).resolve()
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry.get('sha256'):raise ValueError('Empreinte non conforme : '+entry['chemin'])
        inspected=inspect_pdf(root.resolve(),path,entry)
        if inspected['statut']!='valide':raise ValueError(entry['chemin']+' : '+inspected['raison'])
        reader=PdfReader(path)
        if reader.is_encrypted:raise ValueError('PDF chiffré : '+entry['chemin'])
        samples={0,len(reader.pages)//2,len(reader.pages)-1}
        if max(len((reader.pages[i].extract_text() or '').strip()) for i in samples)<100:raise ValueError('Texte non extractible : '+entry['chemin'])
        print(f"OK {entry['marque']} {entry['modele']} {entry['annee']} : {len(reader.pages)} pages, {path.relative_to(ROOT).as_posix()}")
    forbidden={'.git','.venv','venv','__pycache__','.pytest_cache','uploads','.work','instance','logs','backups'}
    secret=re.compile(r'gsk_[A-Za-z0-9]{24,}|sk-(?:proj-)?[A-Za-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
    for path in ROOT.rglob('*'):
        relative=path.relative_to(ROOT)
        if any(part in forbidden for part in relative.parts):raise ValueError('Élément exclu : '+relative.as_posix())
        if path.is_file():
            name=path.name.lower()
            if name=='.env' or (name.startswith('.env.') and name!='.env.example') or path.suffix.lower() in {'.db','.sqlite','.sqlite3','.log','.pyc','.pyo'}:
                raise ValueError('Fichier privé ou temporaire : '+relative.as_posix())
            if path.suffix.lower()!='.pdf' and secret.search(path.read_text(encoding='utf8')):raise ValueError('Secret potentiel détecté, contenu non affiché : '+relative.as_posix())
    example=(ROOT/'.env.example').read_text(encoding='utf8')
    if any(line and not line.startswith('#') and (not line.endswith('=') or line.count('=')!=1) for line in example.splitlines()):raise ValueError('Le modèle .env.example doit rester vide.')
    print('Paquet vérifié : huit PDF attendus, signatures et texte valides, aucun fichier privé ou temporaire détecté.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT if (ROOT/'manuels').is_dir() else ROOT.parent/'livraison')
    ROOT=parser.parse_args().root.resolve()
    try:verify()
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('ÉCHEC : '+str(error),file=sys.stderr)
        sys.exit(1)
