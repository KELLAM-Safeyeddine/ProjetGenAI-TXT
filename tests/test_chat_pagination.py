from app import db
from app.models import Conversation, Message, User


def test_history_cursors_keep_order_and_never_mix_accounts(app, alice):
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.name == 'alice'))
        chats = [Conversation(user_id=user.id, title=f'Recette {i}') for i in range(55)]
        db.session.add_all(chats)
        db.session.flush()
        ident = chats[-1].id
        db.session.add_all(
            Message(conversation_id=ident, role='user', content=f'Texte {i}') for i in range(120)
        )
        db.session.commit()
    first = alice.get('/api/conversations').json
    assert len(first['conversations']) == 50
    second = alice.get(
        '/api/conversations', query_string={'before_id': first['next_before_id']}
    ).json
    assert len(second['conversations']) == 5 and not second['next_before_id']
    messages = alice.get(f'/api/conversations/{ident}/messages').json
    assert len(messages['messages']) == 100 and messages['messages'][0]['content'] == 'Texte 20'
    old = alice.get(
        f'/api/conversations/{ident}/messages',
        query_string={'before_id': messages['next_before_id']},
    ).json
    assert len(old['messages']) == 20 and old['messages'][-1]['content'] == 'Texte 19'
    assert alice.get('/api/conversations?before_id=texte').status_code == 400
    bob = app.test_client()
    bob.post('/login', data={'email': 'bob@example.test', 'password': 'Essai-compte-2026!'})
    assert bob.get(f'/api/conversations/{ident}/messages?before_id=99999').status_code == 404
