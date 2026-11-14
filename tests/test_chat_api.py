from conftest import PASSWORD

from app import db
from app.models import FAQ, Conversation, Message, User


def test_api_and_persistent_history(alice, app, vehicle):
    assert app.test_cli_runner().invoke(args=['import-faq']).exit_code == 0
    response = alice.post(
        '/api/chat', json={'message': 'Quelle pression pour mes pneus ?', 'vehicle_id': vehicle}
    )
    assert response.status_code == 200
    assert response.json['source'] == 'aucune'
    assert (
        response.json['source_line'] == ''
        and 'manuel du Dacia Bigster 2026' in response.json['reply']
    )
    assert (
        'Sécurité :' not in response.json['reply']
        and 'Ne roulez pas' in response.json['reply']
        and 'professionnel' in response.json['reply']
    )
    cid = response.json['conversation_id']
    assert (
        alice.post(
            '/api/chat',
            json={'message': 'Merci, mais parlons de chocolat.', 'conversation_id': cid},
        ).json['status']
        == 'hors_sujet'
    )
    alice.post('/logout')
    assert alice.get('/api/conversations').status_code == 401
    assert alice.post('/api/chat', json={'message': 'Bonjour'}).status_code == 401
    alice.post('/login', data={'email': 'alice@example.test', 'password': PASSWORD})
    assert alice.get('/api/conversations').json['conversations'][0]['id'] == cid
    assert len(alice.get(f'/api/conversations/{cid}/messages').json['messages']) == 4
    assert alice.get('/chat').status_code == 200


def test_chat_isolation(alice, app, vehicle):
    cid = alice.post('/api/chat', json={'message': 'batterie'}).json['conversation_id']
    alice.post('/logout')
    alice.post('/login', data={'email': 'bob@example.test', 'password': PASSWORD})
    assert alice.get('/api/conversations').json == {'conversations': []}
    assert alice.get(f'/api/conversations/{cid}/messages').status_code == 404
    assert (
        alice.post('/api/chat', json={'message': 'huile', 'conversation_id': cid}).status_code
        == 404
    )
    assert (
        alice.post('/api/chat', json={'message': 'huile', 'vehicle_id': vehicle}).status_code == 404
    )
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Conversation)) == 1
        assert db.session.scalar(db.select(db.func.count()).select_from(Message)) == 2


def test_api_validation(alice, app):
    for value in (
        None,
        [],
        'string',
        2,
        {},
        {'message': ''},
        {'message': ' ' * 5},
        {'message': 12},
        {'message': 'x' * 1001},
        {'message': 'test', 'conversation_id': True},
        {'message': 'test', 'vehicle_id': '1'},
        {'message': 'test', 'vehicle_id': -1},
        {'message': 'test', 'extra': 'x'},
    ):
        assert alice.post('/api/chat', json=value).status_code in (400, 415)
    assert (
        alice.post('/api/chat', data='{not json', content_type='application/json').status_code
        == 400
    )
    assert alice.post('/api/chat', data='text').status_code == 415
    assert (
        alice.post('/api/chat', json={'message': 'huile', 'conversation_id': 999}).status_code
        == 404
    )
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Conversation)) == 0


def test_chat_csrf_xss(alice, app):
    app.config['WTF_CSRF_ENABLED'] = True
    assert alice.post('/api/chat', json={'message': 'huile'}).status_code == 400
    import re

    page = alice.get('/chat').data.decode()
    token = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
    content = '<img src=x onerror=alert(1)>'
    response = alice.post('/api/chat', json={'message': content}, headers={'X-CSRFToken': token})
    assert response.status_code == 200
    cid = response.json['conversation_id']
    assert alice.get(f'/api/conversations/{cid}/messages').json['messages'][0]['content'] == content


def test_archived_faq_changes_do_not_affect_chat(alice, app):
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.name == 'alice'))
        user.role = 'admin'
        db.session.commit()
    data = dict(
        category='batterie',
        question='Que veut dire essaiunique ?',
        variants='batterie essaiunique',
        keywords='batterie essaiunique',
        answer='Voici la première réponse de contrôle.',
        risk_level='faible',
    )
    assert alice.post('/admin/faq/new', data=data).status_code == 302
    assert (
        'première'
        not in alice.post('/api/chat', json={'message': 'batterie essaiunique'}).json['reply']
    )
    with app.app_context():
        fid = db.session.scalar(db.select(FAQ.id))
    alice.post(
        f'/admin/faq/{fid}/edit', data={**data, 'answer': 'Voici la seconde réponse de contrôle.'}
    )
    assert (
        'seconde'
        not in alice.post('/api/chat', json={'message': 'batterie essaiunique'}).json['reply']
    )
    alice.post(f'/admin/faq/{fid}/delete', data={'confirm': 'y'})
    assert (
        alice.post('/api/chat', json={'message': 'batterie essaiunique'}).json['status']
        == 'sans_reponse_generale'
    )


def test_full_journey(client, app):
    from test_platform import MAINTENANCE, VEHICLE

    app.test_cli_runner().invoke(args=['import-faq'])
    assert (
        client.post(
            '/register',
            data=dict(
                name='Parcours', email='parcours@example.test', password=PASSWORD, confirm=PASSWORD
            ),
        ).status_code
        == 302
    )
    assert client.post('/vehicles/new', data=VEHICLE).status_code == 302
    from app.models import Vehicle

    with app.app_context():
        vid = db.session.scalar(db.select(Vehicle.id))
    assert client.post(f'/vehicles/{vid}/maintenance/new', data=MAINTENANCE).status_code == 302
    response = client.post('/api/chat', json={'message': 'pression pneus', 'vehicle_id': vid})
    assert response.json['status'] == 'manuel_absent' and not response.json['references']
    cid = response.json['conversation_id']
    client.post('/logout')
    client.post('/login', data={'email': 'parcours@example.test', 'password': PASSWORD})
    assert b'Dacia' in client.get('/dashboard').data
    assert b'350.50' in client.get(f'/vehicles/{vid}/maintenance').data
    assert len(client.get(f'/api/conversations/{cid}/messages').json['messages']) == 2
