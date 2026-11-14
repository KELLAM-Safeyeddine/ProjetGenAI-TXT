from app import db
from app.models import Feedback, User


def test_feedback_is_owned_validated_persistent_and_admin_csv_is_safe(app, alice):
    result = alice.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}).json
    mid = result['message_id']
    path = f'/api/messages/{mid}/feedback'
    assert alice.post(path, json={'helpful': 'oui'}).status_code == 400
    assert alice.post(path, json={'helpful': False, 'comment': '=FORMULE()'}).status_code == 200
    assert alice.get('/admin/retours.csv').status_code == 403
    bob = app.test_client()
    bob.post('/login', data={'email': 'bob@example.test', 'password': 'Essai-compte-2026!'})
    assert bob.post(path, json={'helpful': True}).status_code == 404
    rows = alice.get(f'/api/conversations/{result["conversation_id"]}/messages').json['messages']
    assert rows[-1]['feedback'] == {'helpful': False, 'comment': '=FORMULE()'}
    with app.app_context():
        db.session.scalar(db.select(User).where(User.name == 'alice')).role = 'admin'
        db.session.commit()
        assert db.session.scalar(db.select(Feedback)).comment == '=FORMULE()'
    csv = alice.get('/admin/retours.csv')
    assert csv.status_code == 200 and "'=FORMULE()" in csv.text
