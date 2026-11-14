from datetime import date, timedelta
import pytest
from app import db
from app.models import User, Vehicle, Maintenance, FAQ
from conftest import PASSWORD

VEHICLE = dict(brand='Dacia',model='Bigster',year='2026',engine_type='Essence',mileage='50000')
MAINTENANCE = dict(type='Vidange',date='2025-01-01',mileage='35000',cost='350.50',notes='Huile adaptée',next_date='',next_mileage='60000')

def test_registration_auth_hash_uniqueness(client, app):
    data = dict(name='Camille',email='CAMILLE@example.test',password=PASSWORD,confirm=PASSWORD,role='admin')
    assert client.post('/register',data=data).status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email=='camille@example.test'))
        assert user.password_hash != PASSWORD and user.check_password(PASSWORD)
        assert user.role == 'user'
    client.post('/logout')
    assert client.post('/register',data=data).status_code == 422
    assert client.post('/logout').status_code == 302
    assert client.get('/dashboard').status_code == 302
    assert client.post('/login',data={'email':'camille@example.test','password':'wrong'}).status_code == 422
    assert client.post('/login',data={'email':'camille@example.test','password':PASSWORD}).status_code == 302
    assert client.get('/logout').status_code == 405

def test_vehicle_crud(alice, app):
    assert alice.post('/vehicles/new',data=VEHICLE).status_code == 302
    with app.app_context():
        vehicle = db.session.scalar(db.select(Vehicle))
        vid = vehicle.id
    assert b'Dacia' in alice.get('/vehicles').data
    assert alice.post(f'/vehicles/{vid}/edit',data={**VEHICLE,'mileage':'55000'}).status_code == 302
    with app.app_context():
        assert db.session.get(Vehicle,vid).mileage == 55000
    assert alice.get(f'/vehicles/{vid}/delete').status_code == 200
    assert alice.post(f'/vehicles/{vid}/delete',data={}).status_code == 422
    assert alice.post(f'/vehicles/{vid}/delete',data={'confirm':'y'}).status_code == 302
    with app.app_context():
        assert db.session.get(Vehicle,vid) is None

def test_maintenance_crud_and_cascade(alice,vehicle,app):
    assert alice.post(f'/vehicles/{vehicle}/maintenance/new',data=MAINTENANCE).status_code == 302
    with app.app_context():
        mid = db.session.scalar(db.select(Maintenance.id))
    assert b'350.50' in alice.get(f'/vehicles/{vehicle}/maintenance').data
    assert alice.post(f'/maintenance/{mid}/edit',data={**MAINTENANCE,'cost':'400'}).status_code == 302
    assert alice.post(f'/maintenance/{mid}/delete',data={'confirm':'y'}).status_code == 302
    assert alice.post(f'/vehicles/{vehicle}/maintenance/new',data=MAINTENANCE).status_code == 302
    assert alice.post(f'/vehicles/{vehicle}/delete',data={'confirm':'y'}).status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Maintenance)) == 0

def test_account_isolation(alice,app,vehicle,operation):
    alice.post('/logout')
    alice.post('/login',data={'email':'bob@example.test','password':PASSWORD})
    assert b'Renault' not in alice.get('/vehicles').data
    paths = [f'/vehicles/{vehicle}/edit',f'/vehicles/{vehicle}/delete',f'/vehicles/{vehicle}/maintenance',f'/vehicles/{vehicle}/maintenance/new',f'/maintenance/{operation}/edit',f'/maintenance/{operation}/delete']
    for path in paths:
        assert alice.get(path).status_code == 404
        if not path.endswith('/maintenance'):
            assert alice.post(path,data={**VEHICLE,**MAINTENANCE,'confirm':'y'}).status_code == 404
    with app.app_context():
        assert db.session.get(Vehicle,vehicle).brand == 'Dacia'
        assert db.session.get(Maintenance,operation).notes == 'Privé'

@pytest.mark.parametrize('field,value',[('brand',''),('brand',' '*5),('model','x'*81),('year','1800'),('year','9999'),('year','abc'),('mileage','-1'),('mileage','2.3')])
def test_vehicle_validation(alice,field,value):
    assert alice.post('/vehicles/new',data={**VEHICLE,field:value}).status_code == 422

@pytest.mark.parametrize('field,value',[('date','2099-01-01'),('date','incorrect'),('mileage','-1'),('mileage','50001'),('cost','-3'),('cost','NaN'),('next_date','2024-01-01'),('next_mileage','35000'),('type','inconnu'),('notes','x'*3001)])
def test_maintenance_validation(alice,vehicle,field,value):
    assert alice.post(f'/vehicles/{vehicle}/maintenance/new',data={**MAINTENANCE,field:value}).status_code == 422

@pytest.mark.parametrize('days,next_km,expected', [(-1,None,'dépassée'),(0,None,'atteinte'),(1,None,'future'),(None,49999,'dépassée'),(None,50000,'atteinte'),(None,50001,'future'),(None,None,'absente'),(1,49999,'dépassée'),(-1,50001,'dépassée')])
def test_due_dates(app,vehicle,days,next_km,expected):
    today = date(2026,10,17)
    with app.app_context():
        op = Maintenance(vehicle=db.session.get(Vehicle,vehicle),next_date=today+timedelta(days=days) if days is not None else None,next_mileage=next_km)
        assert op.due_status(today)==expected

def test_mileage_chronology(alice,vehicle,operation):
    assert alice.post(f'/vehicles/{vehicle}/maintenance/new',data={**MAINTENANCE,'date':'2025-02-01','mileage':'39000'}).status_code == 422
    assert alice.post(f'/vehicles/{vehicle}/maintenance/new',data={**MAINTENANCE,'date':'2025-01-01','mileage':'41000'}).status_code == 422
    assert alice.post(f'/vehicles/{vehicle}/edit',data={**VEHICLE,'mileage':'39999'}).status_code == 422

def test_admin_and_import(alice,app):
    for path in ('/admin/faq','/admin/faq/new','/admin/faq/1/edit','/admin/faq/1/delete'):
        assert alice.get(path).status_code == 403
        if path != '/admin/faq':
            assert alice.post(path,data={}).status_code == 403
    runner = app.test_cli_runner()
    assert runner.invoke(args=['import-faq']).exit_code == 0
    assert runner.invoke(args=['import-faq']).output.startswith('0 ')
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.name=='alice'))
        user.role = 'admin'
        db.session.commit()
    assert alice.get('/admin/faq').status_code == 200
    data = dict(category='batterie',question='Ma question de recette originale ?',variants='essai original',keywords='recettefaq',answer='Réponse contrôlée pour la recette.',risk_level='modere')
    assert alice.post('/admin/faq/new',data=data).status_code == 302
    with app.app_context():
        fid = db.session.scalar(db.select(FAQ.id).where(FAQ.question == data['question']))
    assert alice.post(f'/admin/faq/{fid}/edit',data={**data,'answer':'Nouvelle réponse de recette.'}).status_code == 302
    assert alice.post(f'/admin/faq/{fid}/delete',data={'confirm':'y'}).status_code == 302

def test_delete_account(alice,vehicle,operation,app):
    assert alice.post('/account/delete',data={'confirm':'y','password':'wrong'}).status_code == 422
    assert alice.post('/account/delete',data={'confirm':'y','password':PASSWORD}).status_code == 302
    with app.app_context():
        assert db.session.get(Vehicle,vehicle) is None
        assert db.session.get(Maintenance,operation) is None
        assert db.session.scalar(db.select(User).where(User.name=='alice')) is None

def test_csrf_and_xss(alice,app,vehicle):
    assert alice.post(f'/vehicles/{vehicle}/edit',data={**VEHICLE,'brand':'<script>alert(1)</script>'}).status_code == 422
    with app.app_context():
        db.session.get(Vehicle,vehicle).brand = '<script>alert(1)</script>'
        db.session.commit()
    page = alice.get('/vehicles').data
    assert b'&lt;script&gt;' in page and b'<script>alert' not in page
    app.config['WTF_CSRF_ENABLED'] = True
    assert alice.post('/logout').status_code == 400

def test_health_and_cli(app,client):
    assert client.get('/health').json == {'status':'ok'}
    runner = app.test_cli_runner()
    result = runner.invoke(args=['create-admin','--name','Admin','--email','admin@example.test','--password',PASSWORD])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.email=='admin@example.test')).role == 'admin'
