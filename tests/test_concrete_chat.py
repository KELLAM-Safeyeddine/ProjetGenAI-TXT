import json
import re
from pathlib import Path

import pytest
from manual_fixtures import declare

from app import db
from app.models import FAQ
from app.services.chatbot_service import THRESHOLD, load_faq, respond

ROOT = Path(__file__).resolve().parents[1]


def test_enriched_faq_has_eighty_new_complete_sourced_entries():
    entries = load_faq()
    legacy = json.loads((ROOT / 'data/faq_legacy_hashes.json').read_text())
    assert len(entries) == 120 and sum(e['slug'] not in legacy for e in entries) >= 80
    assert len({e['slug'] for e in entries}) == len(entries)
    for entry in entries:
        assert all(
            entry.get(k)
            for k in (
                'question',
                'variantes',
                'mots_cles',
                'reponse',
                'categorie',
                'niveau_risque',
                'source',
            )
        )
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', entry['reponse']) if s.strip()]
        assert 3 <= len(sentences) <= 6, (entry['slug'], len(sentences))
        assert not re.search(r'\d', entry['reponse']), entry[
            'slug'
        ]  # Pas de valeur technique universelle.


@pytest.fixture
def knowledge(app, tmp_path):
    assert app.test_cli_runner().invoke(args=['import-faq']).exit_code == 0
    root = tmp_path / 'manual'
    fixture = json.loads((ROOT / 'tests/data/manuel_evaluation.json').read_text(encoding='utf-8'))
    declare(root, pages=fixture['pages'])
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0


def test_oil_change_manual_is_concrete_sourced_and_private(alice, vehicle, knowledge):
    data = alice.post(
        '/api/chat',
        json=dict(message='Comment procéder pour la vidange moteur ?', vehicle_id=vehicle),
    ).json
    assert data['source'] == 'manuel' and data['status'] == 'reponse'
    assert 'huile' in data['reply'] and 'atelier' in data['reply']
    assert any(r['page'] == 1 and r['section'] == 'Vidange moteur' for r in data['references'])
    assert 'score' not in data and len(data['reply']) > 150
    assert (
        'Source : manuel Dacia Bigster 2026' in data['source_line']
        and 'PDF 1' in data['source_line']
    )


def test_absent_manual_has_announced_concrete_general_answer(alice, app, vehicle):
    app.test_cli_runner().invoke(args=['import-faq'])
    data = alice.post(
        '/api/chat', json=dict(message='Quelle est la fréquence de vidange ?', vehicle_id=vehicle)
    ).json
    assert data['status'] == 'manuel_absent' and 'manuel du Dacia Bigster 2026' in data['reply']
    assert data['source_line'] == '' and not data['references']
    assert not data['references'] and 'pas encore le manuel' not in data['reply']


def test_indexed_manual_missing_topic_falls_back_without_false_reference(alice, vehicle, knowledge):
    data = alice.post(
        '/api/chat', json=dict(message='La climatisation ne refroidit plus.', vehicle_id=vehicle)
    ).json
    assert data['status'] == 'orientation' and not data['references']
    assert data['source_line'] == ''
    assert (
        'mécanicien' not in data['reply'] and 'précisez' in data['reply'] and not data['references']
    )
    assert 'knowledge_sources' not in data


def test_vague_noise_asks_location_moment_and_speed(alice, vehicle, knowledge):
    data = alice.post(
        '/api/chat', json=dict(message='Ma voiture fait un bruit.', vehicle_id=vehicle)
    ).json
    assert (
        data['status'] == 'clarification'
        and data['reply'].count('?') == 1
        and data['source_line'] == ''
    )
    assert not data['references']


@pytest.mark.parametrize(
    'message', ['Une recette de tajine ?', 'Quelle météo demain à Rabat ?', 'Quel film au cinéma ?']
)
def test_off_topic_is_explicit_and_polite(alice, message):
    data = alice.post('/api/chat', json={'message': message}).json
    assert (
        data['status'] == 'hors_sujet'
        and 'automobile' in data['reply']
        and data['source_line'] == ''
    )


@pytest.mark.parametrize(
    'message',
    [
        'Comment vérifier le niveau d’huile ?',
        'La clim souffle du chaud.',
        'frin grince',
        'Ma voiture fait un bruit.',
    ],
)
def test_reply_is_never_a_bare_manual_redirect(message):
    data = respond(message)
    assert len(data['reply']) > 80
    assert data['reply'].strip().casefold() not in {
        'consultez le manuel',
        'consultez le manuel.',
        'je ne sais pas',
        'je ne sais pas.',
    }


def test_both_search_scores_and_darija_are_available():
    result = respond('Bghit ndir vidanj dyal tomobil, imta ?')
    assert result['source'] == 'faq' and result['faq_id'] == 'huile_intervalle'
    assert (
        result['keyword_score'] > 0 and result['tfidf_score'] > 0 and result['score'] >= THRESHOLD
    )


def test_manual_never_confuses_oil_with_brake_fluid_or_drops_condition():
    vehicle = dict(marque='Renault', modele='Clio', annee=2026)
    common = dict(brand='Renault', model='Clio', year=2026, source='equipe: document fictif')
    rows = [
        dict(
            common,
            page=1,
            section='Lecture du niveau d’huile',
            contenu='Lecture du niveau d’huile\nLe niveau d’huile se lit avec la jauge sur un sol horizontal.',
        ),
        dict(
            common,
            page=2,
            section='Le contrôle du niveau se fait moteur à',
            contenu='Le contrôle du niveau se fait moteur à\nl’arrêt sur un sol horizontal. Liquide de frein : faites contrôler le circuit au garage.',
        ),
    ]
    result = respond('Comment vérifier le niveau d’huile moteur ?', vehicle=vehicle, passages=rows)
    assert result['source'] == 'manuel' and {r['page'] for r in result['references']} == {1}
    assert 'jauge' in result['reply'] and 'liquide de frein' not in result['reply']
    rows = [
        dict(
            common,
            page=3,
            section='Au cas où la vérification de la pression',
            contenu='Au cas où la vérification de la pression\nne peut être réalisée sur les pneus froids, demandez au garage les consignes adaptées.',
        )
    ]
    result = respond('vérification pression pneus froids', vehicle=vehicle, passages=rows)
    assert result['source'] == 'manuel' and 'au cas où' in result['reply'].lower()


def test_only_referral_in_manual_uses_concrete_faq_instead():
    result = respond(
        'Quelle fréquence pour la vidange ?',
        vehicle=dict(marque='Renault', modele='Clio', annee=2026),
        passages=[
            dict(
                brand='Renault',
                model='Clio',
                year=2026,
                page=1,
                section='Fréquence vidange',
                contenu='Fréquence vidange\nConsultez le document d’entretien du véhicule pour la fréquence de vidange.',
                source='equipe: recette',
            )
        ],
    )
    assert result['source'] == 'faq' and not result['references']
    assert 'date' in result['reply'] and 'réponse générale' in result['reply']


def test_import_is_idempotent_and_preserves_admin_answer_and_source(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=['import-faq']).exit_code == 0
    with app.app_context():
        row = db.session.scalar(db.select(FAQ).where(FAQ.slug == 'huile_intervalle'))
        row.answer = 'Réponse personnelle validée par administrateur.'
        row.source = 'equipe: source personnelle validée'
        db.session.commit()
    assert runner.invoke(args=['import-faq']).exit_code == 0
    with app.app_context():
        row = db.session.scalar(db.select(FAQ).where(FAQ.slug == 'huile_intervalle'))
        assert (
            row.answer.startswith('Réponse personnelle')
            and row.source == 'equipe: source personnelle validée'
        )
        assert db.session.scalar(db.select(db.func.count(FAQ.id))) == 120


def test_legacy_deletion_is_preserved_during_docker_upgrade(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=['import-faq', '--conserver-suppressions-anciennes']).exit_code == 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(FAQ.id))) == 80
        assert db.session.scalar(db.select(FAQ).where(FAQ.slug == 'huile_intervalle')) is None


def test_evaluation_cli_writes_scores_to_requested_report(app, tmp_path):
    target = tmp_path / 'rapport.md'
    result = app.test_cli_runner().invoke(
        args=['evaluer-chatbot', '--faq-fichier', '--rapport', str(target)]
    )
    assert result.exit_code == 0, result.output
    assert 'appels=' in result.output and '/78' in result.output
    report = target.read_text(encoding='utf-8')
    assert 'SHA-256' in report and 'Échecs restants' in report and 'Appels modèle' in report
