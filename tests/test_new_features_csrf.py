import re


def test_new_write_routes_keep_csrf_required(app, alice, vehicle):
    result = alice.post('/api/chat', json={'message': 'Quand changer les essuie-glaces ?'}).json
    app.config['WTF_CSRF_ENABLED'] = True
    cid = result['conversation_id']
    mid = result['message_id']
    assert alice.patch(f'/api/conversations/{cid}', json={'title': 'essai'}).status_code == 400
    assert alice.delete(f'/api/conversations/{cid}').status_code == 400
    assert alice.post(f'/api/messages/{mid}/feedback', json={'helpful': True}).status_code == 400
    assert alice.post(f'/vehicles/{vehicle}/mileage', data={'mileage': 50001}).status_code == 400
    token = re.search(r'name="csrf-token" content="([^"]+)"', alice.get('/chat').text)[1]
    assert (
        alice.patch(
            f'/api/conversations/{cid}',
            json={'title': 'Mon entretien'},
            headers={'X-CSRFToken': token},
        ).status_code
        == 200
    )
