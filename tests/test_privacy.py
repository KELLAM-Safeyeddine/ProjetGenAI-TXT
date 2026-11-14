from datetime import datetime, timedelta, timezone

from app import db
from app.models import Conversation, Feedback, Message


def test_account_export_is_owned_and_excludes_authentication_secrets(app, alice, vehicle):
    alice.post('/api/chat', json={'message': 'Comment protéger mes pneus ?'})
    export = alice.get('/account/export')
    assert export.status_code == 200 and 'attachment' in export.headers['Content-Disposition']
    assert export.json['compte']['email'] == 'alice@example.test'
    assert 'password_hash' not in export.text and 'auth_version' not in export.text
    bob = app.test_client()
    bob.post('/login', data={'email': 'bob@example.test', 'password': 'Essai-compte-2026!'})
    assert bob.get('/account/export').json['vehicules'] == []
    assert bob.get('/account/export').json['conversations'] == []
    assert app.test_client().get('/account/export').status_code == 302
    assert app.test_client().get('/confidentialite').status_code == 200


def test_retention_uses_last_message_and_dry_run_preserves_data(app, alice):
    result = alice.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}).json
    with app.app_context():
        c = db.session.get(Conversation, result['conversation_id'])
        c.created_at = datetime.now(timezone.utc) - timedelta(days=100)
        for m in c.messages:
            m.created_at = c.created_at
        db.session.add(
            Feedback(
                message_id=c.messages[-1].id, user_id=c.user_id, helpful=False, comment='recette'
            )
        )
        db.session.commit()
    app.config['CONVERSATION_RETENTION_DAYS'] = 30
    runner = app.test_cli_runner()
    assert 'aucune suppression' in runner.invoke(args=['purger-conversations']).output
    with app.app_context():
        assert db.session.get(Conversation, result['conversation_id'])
    assert runner.invoke(args=['purger-conversations', '--appliquer']).exit_code == 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Message)) == 0
        assert db.session.scalar(db.select(db.func.count()).select_from(Feedback)) == 0
