from app import db
from app.models import Feedback, Message


def test_rename_delete_and_feedback_cascade_are_private(app, alice):
    data = alice.post('/api/chat', json={'message': 'Comment entretenir mes essuie-glaces ?'}).json
    cid = data['conversation_id']
    mid = data['message_id']
    assert alice.post(f'/api/messages/{mid}/feedback', json={'helpful': True}).status_code == 200
    url = f'/api/conversations/{cid}'
    assert alice.patch(url, json={'title': '   '}).status_code == 422
    assert alice.patch(url, json={'title': '  <script>titre</script>  '}).status_code == 200
    assert (
        alice.get('/api/conversations').json['conversations'][0]['title']
        == '<script>titre</script>'
    )
    bob = app.test_client()
    bob.post('/login', data={'email': 'bob@example.test', 'password': 'Essai-compte-2026!'})
    assert bob.patch(url, json={'title': 'vol'}).status_code == 404
    assert bob.delete(url).status_code == 404
    assert alice.delete(url).status_code == 200
    assert alice.get(url + '/messages').status_code == 404
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Message)) == 0
        assert db.session.scalar(db.select(db.func.count()).select_from(Feedback)) == 0
