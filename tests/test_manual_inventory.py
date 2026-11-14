"""Découverte dynamique et diagnostic : données PDF fictives, aucun appel réseau."""

import json
from pathlib import Path

import pytest
from manual_fixtures import declare, write_pdf
from test_platform import VEHICLE

from app import create_app, db
from app.models import ManuelPassage, Vehicle
from app.services.document_tools import DocumentTools
from app.services.manual_inventory import scan_manuals


def test_new_dacia_model_discovered_imported_and_allowed_in_form(alice, app, tmp_path):
    root = tmp_path / 'nouveaux'
    declare(root, model='Lodgy', year=2020)
    (root / 'index.json').unlink()  # découverte depuis le PDF, sans préinscription
    app.config['MANUALS_DIR'] = root
    inventory = scan_manuals(root)
    assert len(inventory) == 1 and inventory[0]['statut'] == 'valide'
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0, result.output
    manifest = json.loads((root / 'index.json').read_text(encoding='utf-8'))
    assert [(e['marque'], e['modele'], e['annee']) for e in manifest['manuels']] == [
        ('Dacia', 'Lodgy', 2020)
    ]
    assert manifest['manuels'][0]['actif']
    page = alice.get('/vehicles/new').text
    assert 'value="Lodgy"' in page and 'value="Bigster"' not in page
    assert (
        alice.post('/vehicles/new', data={**VEHICLE, 'model': 'Lodgy', 'year': '2020'}).status_code
        == 302
    )
    assert (
        alice.post('/vehicles/new', data={**VEHICLE, 'model': 'Lodgy', 'year': '2021'}).status_code
        == 422
    )
    assert (
        alice.post(
            '/vehicles/new', data={**VEHICLE, 'brand': 'Renault', 'model': 'Lodgy', 'year': '2020'}
        ).status_code
        == 422
    )


def test_unidentifiable_pdf_is_reported_not_imported(app, tmp_path):
    root = tmp_path / 'inconnus'
    write_pdf(
        root / 'mystere.pdf',
        pages=['Notice\nTexte automobile sans marque, modèle ni année identifiables.'],
    )
    app.config['MANUALS_DIR'] = root
    rows = scan_manuals(root)
    assert len(rows) == 1 and rows[0]['statut'] == 'rejete' and rows[0]['raison']
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0 and 'rejeté' in result.output
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(ManuelPassage)) == 0
    listing = app.test_cli_runner().invoke(args=['lister-manuels-dacia'])
    assert listing.exit_code == 0 and 'REJETÉ mystere.pdf' in listing.output


def test_folder_year_alone_is_never_a_proof(app, tmp_path):
    root = tmp_path / 'sans-annee'
    entry = declare(root, model='Lodgy', year=2020)
    write_pdf(
        root / entry['chemin'],
        pages=['Dacia Lodgy\nNOTICE D’UTILISATION\nUn texte automobile de couverture, sans année.'],
    )
    row = scan_manuals(root)[0]
    assert row['statut'] == 'rejete' and 'Année non identifiable' in row['raison']


def test_cover_model_must_match_exactly_not_sandero_stepway_alias(tmp_path):
    root = tmp_path / 'modeles'
    entry = declare(root, model='Sandero', year=2021)
    write_pdf(
        root / entry['chemin'],
        pages=[
            'Dacia Sandero Stepway 2021\nNOTICE D’UTILISATION\nCe texte fictif est destiné au test.'
        ],
    )
    row = scan_manuals(root)[0]
    assert row['statut'] == 'rejete' and 'Modèle non identifiable' in row['raison']


def test_removing_pdf_immediately_blocks_creation_and_manual_access(alice, app, tmp_path, vehicle):
    root = tmp_path / 'disparus'
    entry = declare(root)
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    (root / entry['chemin']).unlink()
    assert alice.post('/vehicles/new', data=VEHICLE).status_code == 422
    reply = alice.post(
        '/api/chat',
        json=dict(vehicle_id=vehicle, message='Comment vérifier la pression des pneus ?'),
    ).json
    assert reply['status'] == 'manuel_absent' and not reply['references']
    assert "Je n'ai pas le manuel du Dacia Bigster 2026" in reply['reply']


def test_imported_question_cites_printed_page(alice, app, tmp_path):
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject

    root = tmp_path / 'pagination'
    entry = declare(
        root,
        model='Lodgy',
        year=2020,
        pages=[
            'Présentation\nDocument fictif de recette uniquement, jamais utilisable pour un véhicule réel.',
            'Pression des pneus\nVérifiez la pression des pneumatiques à froid et recherchez les valeurs sur l’étiquette du véhicule.',
        ],
    )
    path = root / entry['chemin']
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    page = writer.pages[1]
    stream = DecodedStreamObject()
    stream.set_data(
        page.get_contents().get_data() + b'\nBT /F1 9 Tf 40 16 Td (196 - Conseils pratiques) Tj ET'
    )
    page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(path)
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    assert (
        alice.post('/vehicles/new', data={**VEHICLE, 'model': 'Lodgy', 'year': '2020'}).status_code
        == 302
    )
    with app.app_context():
        vid = db.session.scalar(db.select(Vehicle.id))
    data = alice.post(
        '/api/chat', json=dict(vehicle_id=vid, message='Comment vérifier la pression des pneus ?')
    ).json
    assert data['source'] == 'manuel', data
    assert data['references'][0]['page_pdf'] == 2 and data['references'][0]['page_imprimee'] == 196
    assert 'page imprimée 196, page PDF 2' in data['source_line']


def test_search_excludes_contents_and_preserves_verified_reference():
    ref = dict(marque='Dacia', modele='Lodgy', annee=2020)
    rows = [
        dict(
            brand='Dacia',
            model='Lodgy',
            year=2020,
            page=2,
            page_imprimee=1,
            chapitre='Sommaire',
            section='Pression des pneus',
            contenu='Pression des pneus .......... 50\nPneumatiques .......... 49',
        ),
        dict(
            brand='Dacia',
            model='Lodgy',
            year=2020,
            page=51,
            page_imprimee=50,
            chapitre='Conseils pratiques',
            section='Pression des pneus',
            contenu='Les valeurs de pression des pneus figurent sur l’étiquette à lire en ouvrant la porte conducteur. Contrôlez la pression des pneumatiques à froid.',
        ),
    ]
    result = DocumentTools(ref, ref, lambda: rows).rechercher_manuel('pression pneus')
    assert result['statut'] == 'trouve' and {p['page_pdf'] for p in result['passages']} == {51}
    assert result['passages'][0]['page_imprimee'] == 50


def test_startup_reports_missing_configuration_without_secret(caplog, tmp_path):
    create_app(
        dict(
            TESTING=True,
            SECRET_KEY='test-only-key',
            OPENAI_API_KEY='',
            GROQ_API_KEY='',
            MANUALS_DIR=tmp_path / 'absent',
        )
    )
    assert 'aucun fournisseur configuré' in caplog.text and 'MANUALS_DIR absent' in caplog.text


def test_legacy_chapter_page_is_preserved_without_invented_offset():
    from app.services.manual_extraction import footnote

    words = [dict(text='2.56', top=823, x0=40, x1=60, bottom=833)]
    assert footnote(words, 842) == ('2.56', '2')


@pytest.mark.parametrize(
    'text,expected',
    [
        (
            'Pour Dacia Bigster 2026, ouvrez la porte conducteur pour lire l’étiquette de pression des pneus.',
            'reponse',
        ),
        (
            'Pour Dacia Bigster 2027, ouvrez la porte conducteur pour lire l’étiquette de pression des pneus.',
            'orientation',
        ),
        ('Pour Dacia Bigster 2026, la pression est de 2026 bar.', 'orientation'),
        ('La pression recommandée est 2026.', 'orientation'),
    ],
)
def test_verified_vehicle_year_is_not_a_license_to_invent_technical_numbers(text, expected):
    from model_fixtures import CONFIG, final, tool

    from app.services.answer_service import answer

    ref = dict(marque='Dacia', modele='Bigster', annee=2026)
    row = dict(
        brand='Dacia',
        model='Bigster',
        year=2026,
        page=355,
        page_imprimee=353,
        chapitre='Conseils pratiques',
        section='Pression des pneus',
        contenu='Ouvrez la porte conducteur pour lire l’étiquette de pression des pneus. Vérifiez la pression des pneumatiques à froid.',
    )

    def model(provider, payload, timeout):
        return (
            tool('rechercher_manuel', 'pression pneus')
            if payload.get('tools')
            else final(text, 'reponse', ['M1'])
        )

    result = answer(
        'Quelle est la pression des pneus ?',
        vehicle={**ref, 'manual_reference': ref},
        manual_loader=lambda: [row],
        config=CONFIG,
        transport=model,
    )
    assert result['status'] == expected
    if expected == 'orientation':
        assert not result['references']


def test_visual_reservation_is_removed_only_for_exact_verified_block():
    from app.services.manual_import import extract_manual

    root = Path(__file__).resolve().parents[1] / 'data/manuels'
    path = root / 'dacia/bigster/2026/manuel.pdf'
    if not path.exists():
        pytest.skip('PDF local volontairement absent de la livraison.')
    entry = next(
        e
        for e in json.loads((root / 'index.json').read_text(encoding='utf-8'))['manuels']
        if e['marque'] == 'Dacia' and e['modele'] == 'Bigster'
    )
    rows, _ = extract_manual({**entry, 'path': path}, page_numbers={355})
    assert sum(not r['document_metadata'].get('controle_visuel_requis') for r in rows) == 1
    bad = {
        **entry,
        'path': path,
        'passages_verifies': [{**v, 'sha256_bloc': 'f' * 64} for v in entry['passages_verifies']],
    }
    rows, _ = extract_manual(bad, page_numbers={355})
    assert all(r['document_metadata']['controle_visuel_requis'] for r in rows)
