import json
import pytest
from app import db
from app.models import ManuelPassage, Vehicle, User
from app.services.chatbot_service import repondre_depuis_manuel, NO_MANUAL, THRESHOLD, search_response
from app.services.manual_import import extract_manual, chunk_text
from manual_fixtures import declare
from conftest import PASSWORD

@pytest.fixture
def manuals(app, tmp_path):
    root = tmp_path / 'manuels'
    app.config['MANUALS_DIR'] = root
    declare(root)
    declare(root, 'Dacia', 'Duster', 2026, ['Entretien du pare-brise\nLe nettoyage du pare-brise se fait avec un chiffon doux.\nLe produit fictif BETA208 est réservé à ce document de test.'])
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0, result.output
    return root

def test_import_retrieval_and_history(alice, app, vehicle, manuals):
    response = alice.post('/api/chat', json=dict(message='Quelle pression pour mes pneus à froid ?', vehicle_id=vehicle))
    assert response.status_code == 200
    data = response.json
    assert data['source'] == 'manuel' and data['status'] == 'reponse'
    assert data['references'][0]['page'] == 1 and data['references'][0]['section'] == 'Pression des pneus'
    assert all(word in data['reply'] for word in ('2,1 bar', '2,3 bar', 'essence', 'diesel', 'Ne roulez pas'))
    cid = data['conversation_id']
    alice.post('/logout')
    alice.post('/login', data={'email':'alice@example.test', 'password':PASSWORD})
    saved = alice.get(f'/api/conversations/{cid}/messages').json['messages'][-1]
    assert saved['references'] == data['references'] and saved['vehicle'] == data['vehicle']
    assert saved['source'] == 'manuel'
    page = alice.get(f'/vehicles/{vehicle}/manuel?page=1')
    assert page.status_code == 200 and b'2,3 bar' in page.data
    assert alice.get(f'/vehicles/{vehicle}/manuel?page=99').status_code == 404
    assert alice.get(f'/vehicles/{vehicle}/manuel?page=nope').status_code == 400
    assert alice.get(f'/vehicles/{vehicle}/manuel?page=1&version=Renault|Megane|2026').status_code == 404

def test_missing_manual_never_borrows(alice, app, vehicle, manuals):
    with app.app_context():
        car = db.session.get(Vehicle, vehicle)
        car.year = 2025
        db.session.commit()
    data = alice.post('/api/chat', json=dict(message='pression pneus', vehicle_id=vehicle)).json
    assert data['status']=='manuel_absent' and data['source_line']==''
    assert data['references'] == [] and '2,3' not in data['reply']
    assert NO_MANUAL.encode() in alice.get(f'/vehicles/{vehicle}/manuel').data

def test_model_and_brand_isolation_and_switch(alice, app, vehicle, manuals):
    with app.app_context():
        uid = db.session.scalar(db.select(User.id).where(User.name == 'alice'))
        car = Vehicle(user_id=uid, brand='Dacia', model='Duster', year=2026, engine_type='Essence', mileage=0)
        db.session.add(car)
        db.session.commit()
        other = car.id
    first = alice.post('/api/chat', json=dict(message='pression pneus', vehicle_id=vehicle)).json
    second = alice.post('/api/chat', json=dict(message='nettoyage pare-brise', vehicle_id=other, conversation_id=first['conversation_id'])).json
    assert second['references'][0]['marque'] == 'Dacia' and 'BETA208' in second['reply']
    assert '2,3' not in second['reply']
    wrong = alice.post('/api/chat', json=dict(message='nettoyage pare-brise', vehicle_id=vehicle, conversation_id=first['conversation_id'])).json
    assert wrong['status'] == 'orientation' and 'BETA208' not in wrong['reply']
    with app.app_context():
        injected = [row.as_passage() for row in db.session.scalars(db.select(ManuelPassage))]
    # Défense dans le service pur lui-même, y compris modèle de même marque.
    for brand, model, year in [('Renault','Megane',2026), ('Dacia','Clio',2026), ('Dacia','Bigster',2024)]:
        assert repondre_depuis_manuel('pression pneus', brand, model, year, passages=injected)['status'] == 'manuel_absent'

def test_owner_and_escaped_manual(alice, app, vehicle, manuals):
    with app.app_context():
        row = db.session.scalar(db.select(ManuelPassage).where(ManuelPassage.page == 1))
        row.contenu = '<script>alert(1)</script>'
        db.session.commit()
    page = alice.get(f'/vehicles/{vehicle}/manuel').data
    assert b'&lt;script&gt;' in page and b'<script>alert(1)</script>' not in page
    alice.post('/logout')
    alice.post('/login', data={'email':'bob@example.test', 'password':PASSWORD})
    assert alice.post('/api/chat', json=dict(message='pression pneus', vehicle_id=vehicle)).status_code == 404
    assert alice.get(f'/vehicles/{vehicle}/manuel').status_code == 404

@pytest.mark.parametrize('question', ['bonjour', 'huile', 'Quel film au cinéma ce soir ?', 'problème bizarre', 'pression de ma pizza'])
def test_ambiguous_or_unrelated(alice, vehicle, manuals, question):
    data = alice.post('/api/chat', json=dict(message=question, vehicle_id=vehicle)).json
    assert data['status'] == ('hors_sujet' if 'cinéma' in question or 'pizza' in question else 'politesse' if question=='bonjour' else 'clarification')
    assert data['references'] == []
    assert data['source_line']==''

def test_scanned_corrupt_missing_and_unlisted_nonfatal(app, tmp_path):
    root = tmp_path / 'manuels'
    app.config['MANUALS_DIR'] = root
    declare(root, pages=[''])
    declare(root, 'Dacia', 'Duster', pages=['Texte valide\nLe nettoyage du pare-brise de contrôle utilise un chiffon doux.'])
    declare(root, 'Dacia', 'Sandero')
    (root/'dacia/sandero/2026/manuel.pdf').write_bytes(b'not a PDF')
    declare(root, 'Renault', 'Megane')
    (root/'renault/megane/2026/manuel.pdf').unlink()
    (root/'non-declare.pdf').write_bytes(b'ignored')
    result = app.test_cli_runner().invoke(args=['import-manuels'])
    assert result.exit_code == 0, result.output
    assert all(word in result.output for word in ('sans texte', 'illisible', 'non-declare.pdf', 'PDF rejeté'))
    with app.app_context():
        rows = db.session.scalars(db.select(ManuelPassage)).all()
        assert len(rows) == 1 and rows[0].brand == 'Dacia'

def test_import_idempotent_prunes_and_bad_index_preserves(app, manuals):
    runner = app.test_cli_runner()
    assert runner.invoke(args=['import-manuels']).exit_code == 0
    with app.app_context():
        before = db.session.scalar(db.select(db.func.count()).select_from(ManuelPassage))
        assert before >= 4
    manifest = manuals/'index.json'
    data = json.loads(manifest.read_text())
    data['manuels'][0]['chemin'] = '../../../../outside.pdf'
    manifest.write_text(json.dumps(data))
    assert runner.invoke(args=['import-manuels']).exit_code == 1
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(ManuelPassage)) == before
    manifest.write_text('{"manuels":[]}')
    assert runner.invoke(args=['import-manuels']).exit_code == 0
    assert '2 manuels indexés' in runner.invoke(args=['list-manuels']).output  # découverte autonome
    for path in manuals.rglob('*.pdf'):path.unlink()
    assert runner.invoke(args=['import-manuels']).exit_code == 0
    assert '0 manuels indexés' in runner.invoke(args=['list-manuels']).output

def test_no_vehicle_uses_general_faq(alice, app, manuals):
    app.test_cli_runner().invoke(args=['import-faq'])
    data = alice.post('/api/chat', json={'message':'pression pneus'}).json
    assert data['status'] == 'generale' and data['source']=='faq' and data['vehicle'] is None
    assert all('page' not in ref and 'modele' not in ref for ref in data['references'])
    assert data['source_line']=='' and '2,3 bar' not in data['reply']

def test_chunk_boundaries():
    chunks = list(chunk_text(' '.join(['exemple'] * 400)))
    assert all(1 <= len(chunk) <= 700 for chunk in chunks)
    assert len(chunks) > 2 and chunks[0][-60:] in chunks[1]

def test_alternative_engine_values_across_pages(app, tmp_path):
    root = tmp_path/'manuels'
    app.config['MANUALS_DIR'] = root
    declare(root, pages=['Pression des pneus\nVersion essence : pression de recette 2,1 bar.',
                         'Pression des pneus\nVersion diesel : pression de recette 2,3 bar.'])
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    with app.app_context():
        rows = [p.as_passage() for p in db.session.scalars(db.select(ManuelPassage))]
    result = repondre_depuis_manuel('pression pneus', 'Dacia', 'Bigster', 2026, passages=rows, motorisation='Diesel')
    assert '2,1 bar' in result['reply'] and '2,3 bar' in result['reply']
    assert {r['page'] for r in result['references']} == {1, 2}

def test_long_section_still_provides_sourced_content(app, tmp_path):
    root = tmp_path/'manuels'
    declare(root, pages=['Pression des pneus\nVérifiez la pression des pneus à froid.\n' +
        '\n'.join(f'La remarque annexe de recette numéro {i} concerne uniquement ce document fictif.' for i in range(30))])
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    with app.app_context():
        rows = [p.as_passage() for p in db.session.scalars(db.select(ManuelPassage))]
    result = repondre_depuis_manuel('pression pneus froid', 'Dacia', 'Bigster', 2026, passages=rows)
    assert 'Il faut vérifier la pression des pneus à froid.' in result['reply']
    assert result['references'][0]['page'] == 1

@pytest.mark.parametrize('topic', ['freins', 'pneus', 'voyant rouge', 'direction', 'airbags'])
def test_safety_without_manual(topic):
    result = repondre_depuis_manuel(topic, 'Dacia', 'Bigster', 2026)
    assert NO_MANUAL in result['reply'] and 'garage' in result['reply']

def test_manual_question_set(app, manuals):
    with app.app_context():
        passages = [row.as_passage() for row in db.session.scalars(db.select(ManuelPassage))]
    cases = json.loads((__import__('pathlib').Path(__file__).parent/'data/questions_manuels.json').read_text(encoding='utf-8'))
    passed = 0
    for case in cases:
        result = repondre_depuis_manuel(case['question'], 'Dacia', 'Bigster', 2026, passages=passages)
        passed += result['status'] == case['status'] and (not case.get('page') or result['references'][0]['page'] == case['page'])
    assert passed / len(cases) >= .8, f'{passed}/{len(cases)} ; seuil partagé FAQ/manuels = {THRESHOLD}'
    # Le seuil commun ne modifie pas le contrat historique de la FAQ.
    assert search_response('pression pneus')['source'] == 'faq'
