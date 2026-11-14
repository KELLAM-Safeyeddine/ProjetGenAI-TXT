import json
import logging

from app.services.observability import SafeJSONFormatter


def test_formatter_never_serializes_messages_exceptions_or_arbitrary_fields():
    record = logging.LogRecord(
        'test',
        logging.ERROR,
        'secret-path',
        1,
        'email=alice key=private message utilisateur',
        (),
        None,
    )
    record.user_content = 'private'
    record.provider = 'groq'
    record.event = 'request'
    record.status = 500
    text = SafeJSONFormatter().format(record)
    assert json.loads(text)['status'] == 500
    assert all(x not in text for x in ('private', 'alice', 'message utilisateur', 'secret-path'))


def test_readiness_separates_index_provider_and_liveness(app):
    from app import db
    from app.models import ManuelPassage

    client = app.test_client()
    assert client.get('/health').status_code == 200
    response = client.get('/ready')
    assert response.status_code == 503 and not response.json['components']['index']
    with app.app_context():
        db.session.add(
            ManuelPassage(
                brand='Dacia',
                model='Bigster',
                year=2026,
                page=1,
                position=0,
                section='test',
                contenu='recette',
                search_index='',
                source='equipe: test',
                added_at='2026-11-14',
            )
        )
        db.session.commit()
    response = client.get('/ready', headers={'X-Request-ID': 'secret-injecte'})
    assert response.status_code == 200 and len(response.headers['X-Request-ID']) == 32
    app.config['GROQ_API_KEY'] = ''
    assert client.get('/ready').status_code == 503
