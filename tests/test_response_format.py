import re

import pytest
from model_fixtures import CONFIG, FakeModel, final, tool

from app import db
from app.models import Message
from app.services.answer_service import FORBIDDEN_LABELS, answer, has_forbidden_label
from app.services.general_faq_service import MECHANIC_END, load_general_faq

REF = dict(marque='Dacia', modele='Bigster', annee=2026)
VEHICLE = {**REF, 'manual_reference': REF}
PASSAGE = dict(
    brand='Dacia',
    model='Bigster',
    year=2026,
    page=198,
    page_imprimee=196,
    chapitre='Entretien',
    section='Pression des pneus',
    contenu='Contrôlez la pression des pneus à froid. Les indications de gonflage figurent sur l’étiquette de la porte du véhicule. Vérifiez les pneus avant le trajet et recherchez un dommage visible.',
)


@pytest.mark.parametrize('entry', load_general_faq(), ids=lambda e: e['identifiant'])
def test_each_faq_question_has_detailed_plain_answer_and_one_final_sentence(entry):
    result = answer(entry['question'], config={})
    assert result['source'] == 'faq' and result['faq_id'] == entry['identifiant'], result
    assert 150 <= len(result['reply'].split()) <= 300
    assert result['reply'].endswith(MECHANIC_END) and result['reply'].count(MECHANIC_END) == 1
    assert not result['source_line'] and 'Source :' not in result['reply']
    assert not has_forbidden_label(result['reply'])


def test_verified_manual_source_is_last_without_duplicate_or_mechanic_footer():
    result = answer(
        'Comment contrôler la pression des pneus ?',
        vehicle=VEHICLE,
        manual_loader=lambda: [PASSAGE],
        config=CONFIG,
        transport=FakeModel(),
    )
    assert result['source'] == 'manuel' and result['status'] == 'reponse'
    assert result['reply'].endswith(result['source_line'])
    assert result['reply'].count('Source :') == 1
    assert all(
        part in result['source_line']
        for part in (
            'manuel Dacia Bigster 2026',
            'page imprimée 196',
            'page PDF 198',
            'chapitre Entretien',
        )
    )
    assert not has_forbidden_label(result['reply']) and MECHANIC_END not in result['reply']
    assert 'ne roulez pas' in result['reply'].lower() and 'professionnel' in result['reply']


def test_manual_informative_mechanic_closing_is_removed_but_actions_preserved():
    def model(provider, payload, timeout):
        if payload.get('tools'):
            return tool('rechercher_manuel', 'pression pneus')
        return final(PASSAGE['contenu'] + ' ' + MECHANIC_END, ids=['M1'])

    result = answer(
        'Comment contrôler la pression des pneus ?',
        vehicle=VEHICLE,
        manual_loader=lambda: [PASSAGE],
        config=CONFIG,
        transport=model,
    )
    assert result['source'] == 'manuel' and MECHANIC_END not in result['reply']
    assert 'à froid' in result['reply'] and result['reply'].endswith(result['source_line'])


@pytest.mark.parametrize('label', FORBIDDEN_LABELS)
def test_manual_mode_boilerplate_from_model_is_rejected(label):
    def model(provider, payload, timeout):
        if payload.get('tools'):
            return tool('rechercher_manuel', 'pression pneus')
        return final(label + '. ' + PASSAGE['contenu'], ids=['M1'])

    result = answer(
        'Comment contrôler la pression des pneus ?',
        vehicle=VEHICLE,
        manual_loader=lambda: [PASSAGE],
        config=CONFIG,
        transport=model,
    )
    assert result['status'] == 'orientation' and not result['references']
    assert not has_forbidden_label(result['reply']) and not result['source_line']


@pytest.mark.parametrize('vehicle', [None, VEHICLE])
def test_off_topic_is_one_sentence_even_without_provider(vehicle):
    result = answer('Quelle recette de tajine ?', vehicle=vehicle, config={})
    assert result['status'] == 'hors_sujet' and 'automobile' in result['reply']
    assert len(re.findall(r'[.!?]', result['reply'])) == 1
    assert not result['source_line'] and not has_forbidden_label(result['reply'])


@pytest.mark.parametrize(
    'question',
    [
        'Mes freins grincent.',
        'La direction devient dure.',
        'Un pneu est déchiré.',
        'Le voyant rouge s’allume en roulant.',
        'Un airbag est endommagé.',
        'Une fuite d’essence sent fort.',
    ],
)
@pytest.mark.parametrize('vehicle', [None, VEHICLE])
def test_risk_actions_survive_without_banner_or_evidence(question, vehicle):
    result = answer(question, vehicle=vehicle, config={}, manual_loader=lambda: [])
    text = result['reply'].lower()
    assert not has_forbidden_label(result['reply'])
    assert re.search(r'arrête|immobil|ne roulez|n’intervenez|ne reprenez', text)
    assert re.search(r'vérifi|contrôl|professionnel', text)
    if vehicle is None:
        assert result['reply'].endswith(MECHANIC_END)
    else:
        assert MECHANIC_END not in result['reply']


def test_chat_does_not_render_old_banners_and_keeps_selector_position(alice, app):
    data = alice.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}).json
    cid = data['conversation_id']
    old = 'Réponse générale, sans véhicule sélectionné.\n\nLes balais usés doivent être contrôlés.\n\nSécurité : ne reprenez pas la route avant une vérification par un professionnel.'
    with app.app_context():
        message = db.session.scalar(
            db.select(Message).where(Message.conversation_id == cid, Message.role == 'assistant')
        )
        mid = message.id
        message.content = old
        message.source_line = 'Source : FAQ générale — essuie_glaces.'
        db.session.commit()
    displayed = alice.get(f'/api/conversations/{cid}/messages').json['messages'][-1]
    assert not has_forbidden_label(displayed['content']) and displayed['content'].endswith(
        MECHANIC_END
    )
    assert (
        'vérification par un professionnel' in displayed['content']
        and displayed['source_line'] == ''
    )
    with app.app_context():
        assert db.session.get(Message, mid).content == old
    html = alice.get('/chat').text
    assert (
        html.index('class="chat-controls"')
        < html.index('id="vehicle-select"')
        < html.index('id="chat-input"')
    )
    assert not has_forbidden_label(html) and 'safety-note' not in html
    assert 'Conseils généraux, sans diagnostic' not in html
