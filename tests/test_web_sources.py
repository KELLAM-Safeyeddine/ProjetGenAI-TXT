"""Contrat public actuel, sans appels payants ni pages externes durant pytest."""
import json,logging
from pathlib import Path
from urllib.error import HTTPError,URLError
import pytest
from app import db
from app.models import WebPassage,Message
from app.services.answer_service import BANNED,normalize
from app.services.llm_service import choose_provider
from app.services.web_sources import load_sources,index_pages,search_web,VisibleText
from app.services.chatbot_evaluation import fixture_passages

ROOT=Path(__file__).resolve().parents[1]
URL='https://www.ademe.fr/recette-automobile'
ALLOWED=[dict(url=URL,nom='ADEME',region='International',type='conseil',date_verification='2026-10-17')]
CONTENT='Le covoiturage automobile réduit le nombre de voitures en circulation. Organisez les trajets et les horaires avec les passagers avant le départ. Choisissez un point de rencontre qui permet un arrêt en sécurité.'
WEB=dict(url=URL,site_name='ADEME',title='Covoiturage automobile',content=CONTENT,region='International',kind='conseil',consulted_at='2026-10-17',position=1)
CONFIG=dict(GROQ_API_KEY='cle-de-recette-privee',GROQ_MODEL='simulation',GROQ_BASE_URL='https://example.invalid/v1')
OILWEB={**WEB,'title':'Fréquence de vidange moteur','content':'La fréquence de vidange moteur dépend de son utilisation. Comparez la date et le kilométrage de la dernière opération au programme du véhicule. Une intervention adaptée doit utiliser un produit homologué et récupérer les déchets.'}
VEHICLE=dict(marque='Renault',modele='Clio',annee=2026,motorisation='Diesel')

def test_french_regulations_never_apply_to_morocco():
    allowed=[{**ALLOWED[0],'region':'France','type':'reglementation'}]
    assert search_web('covoiturage automobile au Maroc',[WEB],allowed) is None



def test_robots_spacing_and_inaccessible_nonfatal():
    calls=[];delays=[]
    def getter(url):
        calls.append(url)
        if url.endswith('robots.txt'):return 'User-agent: *\nDisallow: /bloque\nCrawl-delay: 3','text/plain'
        return '<html><title>Automobile</title><nav>secret navigation</nav><p>'+CONTENT+'</p><script>secret script</script></html>','text/html'
    sources=[{**ALLOWED[0],'url':'https://www.ademe.fr/bloque'},ALLOWED[0]]
    rows,journal=index_pages(sources,getter=getter,sleep=delays.append,clock=lambda:0)
    assert calls==['https://www.ademe.fr/robots.txt',URL] and delays==[3]
    assert len(rows)==1 and 'secret' not in rows[0]['content']
    assert 'interdit' in journal[0]
    def fail(url):raise HTTPError(url,403,'blocked',{},None)
    rows,journal=index_pages(ALLOWED,getter=fail,sleep=lambda _:None)
    assert not rows and 'robots.txt inaccessible' in journal[0]



def test_import_only_registry_pages_and_idempotent(app,tmp_path,monkeypatch):
    path=tmp_path/'sources.json';path.write_text(json.dumps(ALLOWED),encoding='utf-8')
    app.config.update(WEB_SOURCES_PATH=path,WEB_IMPORT_LOG=tmp_path/'web.log')
    monkeypatch.setattr('app.services.web_sources.index_pages',lambda sources:([WEB],['import fictif']))
    runner=app.test_cli_runner()
    assert runner.invoke(args=['indexer-sources-web']).exit_code==0
    assert runner.invoke(args=['indexer-sources-web']).exit_code==0
    with app.app_context():assert db.session.scalar(db.select(db.func.count(WebPassage.id)))==1
    assert (tmp_path/'web.log').is_file()



def test_registry_real_pages_and_no_secrets_in_source():
    registry=load_sources(ROOT/'config/sources_fiables.json')
    assert len(registry)>=10 and len({r['url'] for r in registry})==len(registry)
    assert all(r['date_verification']=='2026-10-17' for r in registry if r['type']!='bibliotheque_manuels')
    manuals=next(r for r in registry if r['nom'].startswith('ManualsLib'))
    assert manuals['date_verification']=='2026-10-18' and manuals['acces_automatise'] is False
    env=(ROOT/'.env.example').read_text(encoding='utf-8').splitlines()
    assert all(not line.split('=',1)[1] for line in env if '=' in line)
    service=(ROOT/'app/services/llm_service.py').read_text(encoding='utf-8')
    assert 'api.groq.com' not in service and 'llama-' not in service

def test_manualslib_is_not_fetched_or_used_as_generic_web_content():
    source=next(r for r in load_sources(ROOT/'config/sources_fiables.json') if r['nom'].startswith('ManualsLib'))
    def forbidden(*args):pytest.fail('Aucune requête automatique vers ManualsLib.')
    rows,journal=index_pages([source],getter=forbidden)
    assert not rows and 'consultation manuelle' in journal[0]
    cached={**WEB,'url':source['url']}
    assert search_web('covoiturage automobile',[cached],[source]) is None

def test_disabled_source_is_purged_from_cached_web_index(app,tmp_path,monkeypatch):
    source=next(r for r in load_sources(ROOT/'config/sources_fiables.json') if r['nom'].startswith('ManualsLib'))
    path=tmp_path/'sources.json';path.write_text(json.dumps([source]),encoding='utf-8')
    app.config.update(WEB_SOURCES_PATH=path,WEB_IMPORT_LOG=tmp_path/'web.log')
    with app.app_context():db.session.add(WebPassage(**{**WEB,'url':source['url']}));db.session.commit()
    monkeypatch.setattr('app.services.web_sources.index_pages',lambda sources:([],['consultation manuelle']))
    assert app.test_cli_runner().invoke(args=['indexer-sources-web']).exit_code==0
    with app.app_context():assert db.session.scalar(db.select(db.func.count(WebPassage.id)))==0
