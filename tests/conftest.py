import pytest
import os
from sqlalchemy.engine import make_url
from app import create_app, db
from app.models import User, Vehicle, Maintenance, FAQ
from datetime import date

PASSWORD = 'Essai-compte-2026!'

def test_database_url(tmp_path):
    value = os.environ.get('AUTOHELP_TEST_DATABASE_URL', '').strip()
    if not value:
        return 'sqlite:///' + str(tmp_path / 'test.sqlite3')
    url = make_url(value)
    if not url.drivername.startswith('postgresql') or not (url.database or '').endswith('_test'):
        raise ValueError('La recette exige une base PostgreSQL dédiée dont le nom finit par _test.')
    return value

@pytest.fixture
def app(tmp_path,monkeypatch):
    app = create_app({'TESTING':True, 'SQLALCHEMY_DATABASE_URI':test_database_url(tmp_path), 'WTF_CSRF_ENABLED':False, 'SECRET_KEY':'test-only-key-never-used-in-production',
        **{name:'' for name in ('OPENAI_API_KEY','GROQ_API_KEY','SEARCH_API_KEY')},
        'MANUALS_DIR':tmp_path/'catalogue-manuels', 'MANUAL_IMPORT_LOG':tmp_path/'manual-import.log'})
    from manual_fixtures import TEST_MANUALS,declare
    for brand,model,year in TEST_MANUALS:declare(app.config['MANUALS_DIR'],brand,model,year)
    from model_fixtures import CONFIG,FakeModel
    app.config.update(CONFIG)
    monkeypatch.setattr('app.services.llm_service._post',FakeModel())
    with app.app_context():
        db.create_all()
        for name in ('alice','bob'):
            user = User(name=name, email=f'{name}@example.test', role='user')
            user.set_password(PASSWORD)
            db.session.add(user)
        db.session.commit()
    result = app.test_cli_runner().invoke(args=['import-vehicules'])
    assert result.exit_code == 0, result.output
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def alice(client):
    client.post('/login',data={'email':'alice@example.test','password':PASSWORD})
    return client

@pytest.fixture
def vehicle(app):
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.name=='alice'))
        vehicle = Vehicle(user_id=user.id,brand='Dacia',model='Bigster',year=2026,engine_type='Diesel',mileage=50000)
        db.session.add(vehicle)
        db.session.commit()
        return vehicle.id

@pytest.fixture
def operation(app,vehicle):
    with app.app_context():
        op = Maintenance(vehicle_id=vehicle,type='Vidange',date=date(2025,1,2),mileage=40000,cost=200,notes='Privé')
        db.session.add(op)
        db.session.commit()
        return op.id
