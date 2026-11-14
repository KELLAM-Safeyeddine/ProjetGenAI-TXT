from datetime import date, timedelta

from app import db
from app.models import Maintenance, Vehicle


def test_due_soon_and_quick_mileage_are_owned_and_recomputed(app, alice, vehicle, operation):
    with app.app_context():
        op = db.session.get(Maintenance, operation)
        op.next_date = date.today() + timedelta(days=15)
        op.next_mileage = None
        assert op.is_due_soon(days=30) and not op.is_due_soon(days=10)
        op.next_date = None
        op.next_mileage = 50500
        assert op.is_due_soon(kilometres=1000)
        db.session.commit()
    assert 'À prévoir' in alice.get('/dashboard').text
    assert alice.post(f'/vehicles/{vehicle}/mileage', data={'mileage': -1}).status_code == 422
    assert alice.post(f'/vehicles/{vehicle}/mileage', data={'mileage': 49999}).status_code == 422
    assert alice.post(f'/vehicles/{vehicle}/mileage', data={'mileage': 50500}).status_code == 302
    with app.app_context():
        assert db.session.get(Vehicle, vehicle).mileage == 50500
        assert db.session.get(Maintenance, operation).due_status() == 'atteinte'
    bob = app.test_client()
    bob.post('/login', data={'email': 'bob@example.test', 'password': 'Essai-compte-2026!'})
    assert bob.post(f'/vehicles/{vehicle}/mileage', data={'mileage': 50600}).status_code == 404
