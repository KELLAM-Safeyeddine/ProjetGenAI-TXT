"""Inventaire local vérifiable, sans réseau, OCR, liste de modèles figée ni écriture.

Un répertoire nommé 2026 ne prouve pas un millésime. Il faut une année dans le
nom/couverture, ou une période officielle vérifiée liée à l'empreinte du PDF.
"""
from copy import deepcopy
from datetime import date
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from pypdf import PdfReader
from app.services.manual_policy import canonical,identity,reference_key

DEFAULT_ROOT=Path(__file__).resolve().parents[2]/'data/manuels'


def manuals_root():
    from flask import current_app,has_app_context
    return Path(current_app.config['MANUALS_DIR'] if has_app_context() else DEFAULT_ROOT).resolve()


def file_hash(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def read_manifest(root):
    path=Path(root)/'index.json'
    if not path.exists():return {'manuels':[]}
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('manuels'),list):raise ValueError('index.json doit contenir une liste « manuels ».')
    seen=set()
    for entry in data['manuels']:
        if not isinstance(entry,dict) or not isinstance(entry.get('chemin'),str):raise ValueError('Entrée de manifeste sans chemin valide.')
        relative=Path(entry['chemin']);target=(Path(root)/relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or Path(root).resolve() not in target.parents:raise ValueError('Le chemin du manifeste doit rester dans le dossier des manuels.')
        if target in seen:raise ValueError('Un PDF est déclaré plusieurs fois : identité ambiguë.')
        seen.add(target)
        if not isinstance(entry.get('marque'),str) or not isinstance(entry.get('modele'),str) or type(entry.get('annee')) is not int:raise ValueError('Identité de manifeste invalide.')
    return data


def official_year(entry,digest,year):
    proof=entry.get('preuve_identite') or {}
    if not isinstance(proof,dict):return False
    source=urlsplit(proof.get('url',''))
    if source.scheme!='https' or source.hostname not in {'www.user-manual.dacia.com','user-manual.dacia.com'} or source.username or source.password:return False
    if proof.get('sha256')!=digest or proof.get('url')!=entry.get('source') or proof.get('url_pdf')!=entry.get('url_pdf'):return False
    if proof.get('modele')!=entry.get('modele') or proof.get('annee')!=year:return False
    try:
        checked=date.fromisoformat(proof['consulte_le'])
        start=date.fromisoformat(proof['debut_validite'])
        end=date.fromisoformat(proof['fin_validite']) if proof.get('fin_validite') else checked
        return start<=end and start.year<=year<=end.year and year<=checked.year
    except (KeyError,ValueError,TypeError):return False


def inspect_pdf(root,path,entry):
    relative=path.relative_to(root).as_posix()
    row=dict(chemin=relative,statut='rejete',raison='',reference=None)
    def reject(reason):row['raison']=reason;return row
    if root not in path.resolve().parents:return reject('Chemin extérieur au dossier autorisé.')
    if entry.get('marque') and identity(entry['marque'])!='dacia':return reject('Marque déclarée non Dacia : hors périmètre.')
    if path.stat().st_size>150*1024*1024:return reject('PDF trop volumineux (>150 Mo).')
    try:
        with path.open('rb') as stream:
            if b'%PDF-' not in stream.read(1024):return reject('PDF illisible : signature absente.')
        reader=PdfReader(path)
        if reader.is_encrypted:return reject('PDF chiffré ; aucune tentative de contournement.')
        cover=reader.pages[0].extract_text() or ''
        metadata=str((reader.metadata or {}).get('/Title',''))
        pages=len(reader.pages)
    except Exception:return reject('PDF illisible ou corrompu.')
    row['pages']=pages
    if len(re.sub(r'\W','',cover))<10:return reject('Couverture sans texte identifiable (PDF scanné ou sans texte), sans OCR.')
    hint=entry.get('marque') or (path.relative_to(root).parts[0] if len(path.relative_to(root).parts)>1 else '')
    brand_evidence=cover+' '+metadata+' '+str(entry.get('source',''))+' '+path.stem
    if identity(hint)!='dacia' and not re.search(r'\bdacia(?=[\W_]|$)',brand_evidence,re.I):return reject('Marque non identifiable ou non Dacia : hors périmètre.')
    if hint and identity(hint)!='dacia':return reject('Marque déclarée non Dacia : hors périmètre.')
    # Le nom structuré est un indice, toujours confronté à la couverture.
    filename=re.search(r'(?i)\bdacia[ _-]+(.+?)[ _-]+((?:19|20)\d{2})\b',path.stem)
    parts=path.relative_to(root).parts
    model=entry.get('modele') or (filename[1].replace('_',' ').replace('-',' ') if filename else None)
    if not model and len(parts)>=4 and identity(parts[0])=='dacia':model=parts[-3].replace('-',' ').replace('_',' ').title()
    if not model:
        candidates=[]
        for line in cover.splitlines():
            line=re.sub(r'(?i)\bdacia\b|\b(?:19|20)\d{2}\b','',line).strip(' /_-')
            if line and len(line)<=60 and not re.search(r'(?i)notice|utilisation|manuel|propri.taire|copyright|édition|edition|www\.|https?:|\d',line):candidates.append(line)
        if len(candidates)==1:model=candidates[0].title()
    cover_labels=[]
    for line in re.split(r'[\n/]',cover):
        label=re.sub(r'(?i)\bdacia\b|\b(?:19|20)\d{2}\b','',line).strip(' _-')
        label=re.sub(r'(?i)\s+electric\s*$','',label)
        cover_labels.append(identity(label))
    if not model or not identity(model) or identity(model) not in cover_labels:return reject('Modèle non identifiable sur la couverture ou en conflit avec le nom déclaré.')
    # Une marque issue uniquement d'un dossier n'est pas une preuve.
    if not re.search(r'(?i)dacia',brand_evidence):
        try:brand_evidence+=' '+(reader.pages[-1].extract_text() or '')
        except Exception:pass
        if not re.search(r'(?i)dacia',brand_evidence):return reject('Marque Dacia non confirmée dans le document ou sa provenance.')
    cover_years={int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b',cover)}
    named_year=int(filename[2]) if filename else None
    year=entry.get('annee') or named_year or (next(iter(cover_years)) if len(cover_years)==1 else None)
    digest=file_hash(path)
    proven=year is not None and official_year(entry,digest,year)
    if year is None or (year not in cover_years and year!=named_year and not proven):return reject('Année non identifiable : un nom de dossier ne suffit pas ; fournir une preuve officielle liée au PDF.')
    if not proven and cover_years and year not in cover_years:return reject('Année en conflit entre le nom et la couverture.')
    reference=canonical('Dacia',model,year)
    if not reference:return reject('Identité Dacia invalide.')
    source=entry.get('source') or 'equipe: PDF local identifié par son nom et sa couverture'
    if not isinstance(source,str) or len(source)>1000 or not source.startswith(('https://','equipe:')):return reject('Source invalide : URL HTTPS ou provenance equipe: requise.')
    parsed=urlsplit(source)
    if parsed.hostname in {'manualslib.com','www.manualslib.com'} and (parsed.query or parsed.username or parsed.password or not re.fullmatch(r'/manual/[0-9]+/[^/]+\.html',parsed.path)):
        return reject('ManualsLib : page exacte du manuel requise, pas le portail.')
    added=entry.get('date_ajout') or date.today().isoformat()
    try:date.fromisoformat(added)
    except (ValueError,TypeError):return reject('Date d’ajout invalide.')
    if 'langue' in entry and (not isinstance(entry['langue'],str) or not re.fullmatch('[a-z]{2}',entry['langue'])):return reject('Code de langue invalide.')
    row.update(statut='valide',raison='Modèle confirmé en couverture ; année '+('confirmée par période officielle et empreinte PDF.' if proven else 'présente dans le nom ou la couverture.'),reference=reference)
    row['entry']={**entry,**reference,'chemin':relative,'source':source,'date_ajout':added,'sha256':digest,'pages':pages,
                  'actif':True,'pret_import':True,'identification':dict(methode='couverture_et_periode_officielle' if proven else 'nom_et_couverture',verifie_le=date.today().isoformat(),sha256=digest)}
    return row


@lru_cache(maxsize=32)
def _scan(root_string,signature):
    root=Path(root_string);manifest=read_manifest(root)
    declared={e['chemin']:e for e in manifest['manuels']}
    rows=[inspect_pdf(root,root/name,declared.get(name,{})) for name,_,_,_ in signature if name!='index.json']
    groups={}
    for row in rows:
        if row['statut']=='valide':groups.setdefault(reference_key(*row['reference'].values()),[]).append(row)
    for candidates in groups.values():
        if len(candidates)>1:
            for row in candidates:row.update(statut='rejete',raison='Plusieurs PDF pour le même modèle et la même année : choisir une édition explicitement.')
    return rows


def scan_manuals(root=None):
    root=Path(root or manuals_root()).resolve()
    paths=sorted((p for p in root.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf'),key=lambda p:p.as_posix()) if root.exists() else []
    if (root/'index.json').is_file():paths.append(root/'index.json')
    signature=tuple((p.relative_to(root).as_posix(),p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in paths)
    return deepcopy(_scan(str(root),signature))


def available_entries(root=None):
    return [r['entry'] for r in scan_manuals(root) if r['statut']=='valide']
