import importlib.util
import json
from pathlib import Path

import pytest
from manual_fixtures import declare, write_pdf

from app import db
from app.models import ManuelPassage
from app.services.chatbot_service import repondre_depuis_manuel

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'manual_downloader', ROOT / 'scripts/download_manuals.py'
)
downloader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader)


def test_source_registry_matches_initial_catalog():
    catalog = json.loads((ROOT / 'data/vehicules_maroc.json').read_text(encoding='utf-8'))
    registry = json.loads((ROOT / 'data/manual_sources.json').read_text(encoding='utf-8'))
    keys = {(r['marque'], r['modele'], r['annee']) for r in catalog['vehicules']}
    rows = registry['manuels']
    assert len(rows) == len(keys) == 66
    assert {(r['marque'], r['modele'], r['annee']) for r in rows} == keys
    assert all(type(r['manuel_indisponible']) is bool for r in catalog['vehicules'])
    for row in rows:
        downloader.official(row['url_source'])
        if row['url_pdf']:
            downloader.official(row['url_pdf'])
            assert row['langue'] in ('fr', 'en') and row['periode']
        assert row['date_consultation']


def test_manualslib_local_manual_is_indexed_scoped_and_attributed(app, tmp_path):
    from model_fixtures import CONFIG, FakeModel

    from app.services.answer_service import answer

    root = tmp_path / 'manuels'
    entry = declare(root)
    # PDF entièrement fictif : cette URL ne prouve aucune attribution réelle à 2026.
    entry['source'] = 'https://www.manualslib.com/manual/3549447/Renault-Clio.html'
    (root / 'index.json').write_text(json.dumps({'manuels': [entry]}), encoding='utf-8')
    app.config['MANUALS_DIR'] = root
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0, result.output
    with app.app_context():
        rows = [p.as_passage() for p in db.session.scalars(db.select(ManuelPassage))]
    ref = dict(marque='Dacia', modele='Bigster', annee=2026)
    reply = answer(
        'Comment vérifier le niveau huile moteur ?',
        vehicle={**ref, 'manual_reference': ref},
        manual_loader=lambda: rows,
        config=CONFIG,
        transport=FakeModel(),
    )
    assert reply['source'] == 'manuel' and 'ManualsLib.com' in reply['source_line']
    assert entry['source'] in reply['source_line'] and reply['references'][0]['page'] == 3
    assert all(r['annee'] == 2026 and r['modele'] == 'Bigster' for r in reply['references'])
    with pytest.raises(ValueError):
        downloader.official(entry['source'])


@pytest.mark.parametrize(
    'source',
    ['https://www.manualslib.com/', 'https://www.manualslib.com/brand/renault/automobile.html'],
)
def test_manualslib_requires_exact_document_page(app, tmp_path, source):
    root = tmp_path / 'manuels'
    entry = declare(root)
    entry['source'] = source
    (root / 'index.json').write_text(json.dumps({'manuels': [entry]}), encoding='utf-8')
    app.config['MANUALS_DIR'] = root
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0 and 'page exacte' in result.output
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(ManuelPassage)) == 0


def test_only_observed_links_accepted():
    base = 'https://www.user-manual.dacia.com/fr/notice/123/pdf'
    pdf = 'https://www.user-manual.dacia.com/sites/dacia/files/manual.pdf'
    assert downloader.linked_pdf(
        '<iframe src="/sites/dacia/files/manual.pdf#page=1"></iframe>', base, pdf
    )
    assert not downloader.linked_pdf('<p>Connectez-vous.</p>', base, pdf)
    assert downloader.linked_pdf(
        '{"pdf":"/test/notice française.pdf"}',
        base,
        'https://www.user-manual.dacia.com/test/notice%20fran%C3%A7aise.pdf',
    )
    for invalid in [
        'http://www.hyundai.com/test.pdf',
        'https://example.org/manuel.pdf',
        'https://localhost/test.pdf',
        'file:///private.pdf',
    ]:
        with pytest.raises(ValueError):
            downloader.official(invalid)


def test_download_rejects_html_scan_and_preserves_unknown_local_pdf(tmp_path):
    path = tmp_path / 'fake.pdf'
    path.write_bytes(b'<html>login</html>' * 100)
    with pytest.raises(ValueError, match='pas un PDF'):
        downloader.inspect_pdf(path)
    write_pdf(path, pages=[''] * 15)
    with pytest.raises(ValueError, match='scanné'):
        downloader.inspect_pdf(path)
    write_pdf(path)
    assert downloader.inspect_pdf(path)['pages'] == 3
    with pytest.raises(ValueError, match='aucun écrasement'):
        downloader.obtain(
            {
                'url_source': 'https://www.hyundai.com/',
                'url_pdf': 'https://www.hyundai.com/manuel.pdf',
            },
            path,
            offline=True,
        )


def test_encrypted_pdf_dependency_is_reported_without_decryption(tmp_path, monkeypatch):
    path = tmp_path / 'encrypted.pdf'
    path.write_bytes(b'%PDF-' + b' ' * 2000)

    def encrypted(*args, **kwargs):
        raise downloader.DependencyError('cryptography>=3.1 is required for AES algorithm')

    monkeypatch.setattr(downloader, 'PdfReader', encrypted)
    with pytest.raises(ValueError, match='chiffré.*accès restreint'):
        downloader.inspect_pdf(path)


def test_language_and_period_are_persisted_and_reported(app, tmp_path):
    root = tmp_path / 'manuels'
    entry = declare(
        root,
        pages=[
            'Tyre pressure\nCheck the tyre pressure when the tyres are cold.\nThe vehicle must be parked safely before checking the tyres.'
        ],
    )
    entry.update(
        langue='en',
        periode='2024 à aujourd’hui',
        marche_document='Royaume-Uni',
        url_pdf='https://www.hyundai.com/example.pdf',
    )
    (root / 'index.json').write_text(json.dumps({'manuels': [entry]}), encoding='utf-8')
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    with app.app_context():
        rows = [p.as_passage() for p in db.session.scalars(db.select(ManuelPassage))]
    result = repondre_depuis_manuel('pression pneus froid', 'Dacia', 'Bigster', 2026, passages=rows)
    assert result['status'] == 'reponse'
    assert 'anglais' in result['reply'] and 'aucune traduction automatique' in result['reply']
    assert '2024 à aujourd’hui' in result['reply'] and 'Royaume-Uni' in result['reply']
    assert result['references'][0]['langue'] == 'en'


def test_numbered_sections_and_tyre_synonym():
    rows = [
        dict(
            brand='Dacia',
            model='Duster',
            year=2026,
            page=page,
            section=f'Pression pneumatiques ({page}/2)',
            contenu=text,
            source='equipe: recette',
        )
        for page, text in [
            (1, 'Vérifiez la pression des pneumatiques à froid.'),
            (2, 'Le contrôle de la pression des pneumatiques concerne aussi la roue de secours.'),
        ]
    ]
    result = repondre_depuis_manuel('pression pneus', 'Dacia', 'Duster', 2026, passages=rows)
    assert result['status'] == 'reponse' and {r['page'] for r in result['references']} == {1, 2}


def test_unavailable_manual_keeps_vehicle_in_form(alice, app):
    data = alice.get('/api/vehicle-catalog').json['vehicles']
    missing = next(row for row in data if row['model'] == 'Duster')
    assert missing['manual_indexed'] is False
    response = alice.post(
        '/vehicles/new',
        data=dict(
            brand=missing['brand'],
            model=missing['model'],
            year=missing['year'],
            engine_type='',
            mileage=0,
        ),
    )
    assert response.status_code == 302


def test_download_pipeline_records_success_and_missing_without_network(tmp_path, monkeypatch):
    (tmp_path / 'data').mkdir()
    catalog = {
        'vehicules': [
            dict(marque='Dacia', modele='Sandero', annee=2026),
            dict(marque='Dacia', modele='Duster', annee=2026),
        ]
    }
    (tmp_path / 'data/vehicules_maroc.json').write_text(json.dumps(catalog))
    manual = tmp_path / 'fixture.pdf'
    write_pdf(manual)
    payload = manual.read_bytes()
    pdf_url = 'https://www.hyundai.com/fixture.pdf'
    source = 'https://www.hyundai.com/manuals'
    registry = {
        'manuels': [
            dict(
                marque='Dacia',
                modele='Sandero',
                annee=2026,
                url_source=source,
                url_pdf=pdf_url,
                langue='fr',
                periode='2026',
            ),
            dict(
                marque='Dacia',
                modele='Duster',
                annee=2026,
                url_source=source,
                url_pdf='',
                statut_source='introuvable',
                commentaire='Année non documentée.',
            ),
        ]
    }
    registry_path = tmp_path / 'registry.json'
    registry_path.write_text(json.dumps(registry))
    monkeypatch.setattr(downloader, 'ROOT', tmp_path)
    monkeypatch.setattr(
        downloader,
        'read_url',
        lambda url, *args: payload if url == pdf_url else f'<a href="{pdf_url}">PDF</a>'.encode(),
    )
    reports = downloader.download(
        registry_path, root=tmp_path / 'data/manuels', update_catalog=True, delay=0
    )
    assert [r['statut'] for r in reports] == ['telecharge', 'introuvable']
    data = json.loads((tmp_path / 'data/vehicules_maroc.json').read_text(encoding='utf-8'))
    assert [r['manuel_indisponible'] for r in data['vehicules']] == [False, True]
    entries = json.loads((tmp_path / 'data/manuels/index.json').read_text(encoding='utf-8'))[
        'manuels'
    ]
    assert len(entries) == 1 and entries[0]['pages'] == 3 and entries[0]['url_pdf'] == pdf_url
    import csv

    with (tmp_path / 'data/manuels/sources.csv').open(encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == list(downloader.CSV_COLUMNS) and len(list(reader)) == 2
