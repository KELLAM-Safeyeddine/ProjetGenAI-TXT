"""Téléchargements séquentiels depuis le registre vérifié, sans recherche de liens.

python scripts/download_manuals.py [--update-catalog] [--offline]
Les PDF et le journal restent exclusivement dans data/manuels/ (ignoré).
"""
import argparse
import csv
from datetime import date
import gzip
import hashlib
from html import unescape
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urldefrag, unquote
from urllib.request import Request, urlopen
from pypdf import PdfReader
from pypdf.errors import DependencyError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT/'data/manual_sources.json'
MAX_BYTES = 100 * 1024 * 1024
CSV_COLUMNS = ('marque', 'modele', 'annee', 'url_source', 'url_pdf', 'date_consultation', 'statut', 'commentaire')
OFFICIAL_HOSTS = {'www.user-manual.dacia.com', 'www.user-manual.renault.com',
    'public.servicebox.peugeot.com', 'ownersmanual.hyundai.com', 'www.hyundai.com',
    'dmassets.hyundai.com', 'www.hyundaicanada.com', 'www.volkswagen.fr',
    'www.volkswagen-vans.co.uk',
    'cdn.group.renault.com', 'fr.e-guide.renault.com'}

def slug(value):
    import re
    value = ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))
    return '-'.join(re.findall('[a-z0-9]+', value))

def official(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in OFFICIAL_HOSTS or parsed.username or parsed.password:
        raise ValueError('URL hors de la liste des domaines officiels vérifiés.')
    return url

class SourceLinks(HTMLParser):
    def __init__(self, html, base):
        super().__init__()
        self.urls = set()
        self.base = base
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src', 'data') and value:
                self.urls.add(urldefrag(urljoin(self.base, unescape(value)))[0])

def linked_pdf(text, source, pdf):
    """URL issue d'un lien/iframe HTML ou d'un champ JSON public, jamais devinée."""
    urls = SourceLinks(text, source).urls
    try:
        data = json.loads(text)
        def visit(value):
            if isinstance(value, dict):
                for child in value.values(): visit(child)
            elif isinstance(value, list):
                for child in value: visit(child)
            elif isinstance(value, str) and value.startswith(('https://', '/')):
                urls.add(urldefrag(urljoin(source, value))[0])
        visit(data)
    except ValueError:
        pass
    return unquote(urldefrag(pdf)[0]) in {unquote(url) for url in urls}

def read_url(url, limit=MAX_BYTES):
    official(url)
    request = Request(url, headers={'User-Agent':'AutoHELP-manual-downloader/1.0', 'Accept-Encoding':'identity'})
    with urlopen(request, timeout=60) as response:
        official(response.url)
        length = response.headers.get('Content-Length')
        if length and int(length) > limit:
            raise ValueError('Fichier au-delà de la limite de taille autorisée.')
        raw = response.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('Fichier trop volumineux.')
        if raw.startswith(b'\x1f\x8b'):
            raw = gzip.GzipFile(fileobj=BytesIO(raw)).read(limit + 1)
            if len(raw) > limit:
                raise ValueError('Contenu décompressé trop volumineux.')
        return raw

def inspect_pdf(path):
    if not 1024 <= path.stat().st_size <= MAX_BYTES:
        raise ValueError('Taille de PDF non raisonnable (1 Ko à 100 Mo).')
    with path.open('rb') as file:
        if file.read(5) != b'%PDF-':
            raise ValueError('La réponse reçue n’est pas un PDF.')
    try:
        reader = PdfReader(path)
    except DependencyError as error:
        # Pypdf peut détecter AES dès l'ouverture, avant is_encrypted.
        # Ne pas ajouter un déchiffreur pour contourner cette restriction.
        raise ValueError('PDF chiffré (AES) : accès restreint ; aucun déchiffrement effectué.') from error
    if reader.is_encrypted:
        raise ValueError('PDF chiffré, accès restreint.')
    if not reader.pages:
        raise ValueError('PDF vide.')
    # Couverture et pages réparties : l'import contrôlera ensuite chaque page.
    sample = sorted(set(range(min(8, len(reader.pages)))) | {len(reader.pages)//2, len(reader.pages)-1})
    letters = sum(sum(char.isalpha() for char in (reader.pages[i].extract_text() or '')) for i in sample)
    if letters < 100:
        raise ValueError('PDF scanné ou sans texte extractible ; aucun OCR effectué.')
    return dict(pages=len(reader.pages), taille_octets=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def write_index(path, entries):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps({'manuels':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)

def obtain(row, target, *, cached=None, offline=False, pages=None, pause=None):
    if target.exists():
        # Ne réutiliser un PDF antérieur que si sa provenance et son empreinte sont connues.
        if cached and cached.get('url_pdf') == row['url_pdf']:
            info = inspect_pdf(target)
            if info['sha256'] == cached.get('sha256'):
                return info
        raise ValueError('Un PDF local non reconnu existe déjà ; aucun écrasement automatique.')
    if offline:
        raise ValueError('PDF absent localement (mode hors ligne).')
    source, pdf = official(row['url_source']), official(row['url_pdf'])
    if source not in pages:
        pause()
        pages[source] = read_url(source, 5*1024*1024).decode('utf-8', errors='replace')
    if not linked_pdf(pages[source], source, pdf):
        raise ValueError('Le lien PDF ne figure plus dans la source consultée ; relecture requise.')
    pause()
    payload = read_url(pdf)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.pdf.part')
    try:
        temporary.write_bytes(payload)
        info = inspect_pdf(temporary)
        temporary.replace(target)
        return info
    finally:
        temporary.unlink(missing_ok=True)

def download(registry_path=REGISTRY, root=None, *, offline=False, update_catalog=False, delay=2.0):
    registry_path = Path(registry_path)
    root = Path(root or ROOT/'data/manuels').resolve()
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    catalog_path = ROOT/'data/vehicules_maroc.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    expected = {(r['marque'], r['modele'], r['annee']) for r in catalog['vehicules']}
    rows = registry['manuels']
    keys = [(r['marque'], r['modele'], r['annee']) for r in rows]
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError('Le registre doit couvrir exactement les versions du catalogue initial.')
    root.mkdir(parents=True, exist_ok=True)
    index_path = root/'index.json'
    old = json.loads(index_path.read_text(encoding='utf-8')).get('manuels', []) if index_path.exists() else []
    old_by_key = {(r['marque'], r['modele'], r['annee']):r for r in old}
    # Les entrées fournies manuellement par l'équipe sont conservées hors du périmètre automatique.
    index = [r for r in old if r.get('gestion') != 'sources_officielles']
    csv_rows, successes, downloaded = [], {}, {}
    pages, last_request, paused_hosts = {}, [0.0], set()
    def pause():
        wait = delay - (time.monotonic() - last_request[0])
        if wait > 0: time.sleep(wait)
        last_request[0] = time.monotonic()
    for row in rows:
        key = (row['marque'], row['modele'], row['annee'])
        report = {name:row.get(name, '') for name in CSV_COLUMNS}
        report['date_consultation'] = row.get('date_consultation', str(date.today()))
        report['statut'] = row.get('statut_source', 'introuvable')
        relative = Path(slug(row['marque']))/slug(row['modele'])/str(row['annee'])/'manuel.pdf'
        target = root/relative
        if root not in target.resolve().parents:
            raise ValueError('Chemin de PDF hors du dossier des manuels (lien symbolique refusé).')
        if row.get('url_pdf') and row.get('statut_source') != 'acces_restreint':
            try:
                if any(urlsplit(row[name]).hostname in paused_hosts for name in ('url_source','url_pdf')):
                    raise HTTPError(row['url_pdf'],429,'Hôte suspendu après limitation de requêtes ; réessayer plus tard.',{},None)
                if row['url_pdf'] in downloaded and not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(downloaded[row['url_pdf']], target)
                    info = inspect_pdf(target)
                else:
                    info = obtain(row, target, cached=old_by_key.get(key), offline=offline, pages=pages, pause=pause)
                downloaded[row['url_pdf']] = target
                report['statut'] = 'telecharge' if row.get('langue', 'fr') == 'fr' else 'langue_non_francaise'
                entry = {k:v for k,v in row.items() if k not in ('statut_source',)}
                entry.update(chemin=relative.as_posix(), source=row['url_source'], date_ajout=str(date.today()), gestion='sources_officielles', **info)
                # La collecte ne doit jamais réactiver un document : validation
                # humaine et politique d'import restent distinctes du téléchargement.
                prior=old_by_key.get(key,{})
                entry.update(actif=prior.get('actif',False),pret_import=prior.get('pret_import',False))
                index = [r for r in index if (r['marque'],r['modele'],r['annee']) != key]
                index.append(entry)
                successes[key] = report['statut']
                report['commentaire'] = (row.get('commentaire','') + f" PDF vérifié : {info['pages']} pages, {info['taille_octets']} octets ; texte extractible. " + row.get('periode','')).strip()
            except Exception as error:
                code = getattr(error, 'code', None)
                if code == 429:
                    paused_hosts.add(urlsplit(error.url).hostname)
                report['statut'] = 'acces_restreint' if code in (401,403,429) or 'chiffré' in str(error) else 'introuvable'
                report['commentaire'] = (row.get('commentaire','') + ' Téléchargement non retenu : ' + str(error)).strip()
        csv_rows.append(report)
        print(f"{row['marque']} {row['modele']} {row['annee']} : {report['statut']}", flush=True)
        # Point de reprise après chaque document, sans distribuer le contenu des PDF.
        write_index(index_path,index)
    with (root/'sources.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=CSV_COLUMNS);writer.writeheader();writer.writerows(csv_rows)
    if update_catalog:
        for row in catalog['vehicules']:
            key=(row['marque'],row['modele'],row['annee'])
            row['manuel_indisponible'] = key not in successes
        catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    hashes = {r.get('sha256') for r in index if (r['marque'],r['modele'],r['annee']) in successes}
    print(f'{len(successes)} versions vérifiées ; {len(hashes)} PDF distincts par empreinte ; {len(rows)-len(successes)} versions sans PDF vérifié.')
    return csv_rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true',help='Contrôler les PDF déjà présents, sans réseau.')
    parser.add_argument('--update-catalog',action='store_true',help='Actualiser manuel_indisponible dans le dataset source.')
    parser.add_argument('--directory',type=Path,help='Dossier local des PDF et métadonnées ; défaut : data/manuels.')
    args=parser.parse_args()
    download(root=args.directory,offline=args.offline,update_catalog=args.update_catalog)

if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as error:
        sys.exit(f'Import des sources impossible : {error}')
