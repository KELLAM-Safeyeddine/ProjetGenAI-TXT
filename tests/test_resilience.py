import re
from time import perf_counter
from app import db, create_app
from app.models import Vehicle, Maintenance, Conversation, Message
from conftest import PASSWORD

def test_session_csrf_journey(client,app):
    app.config['WTF_CSRF_ENABLED']=True
    def token(path):
        html=client.get(path).data.decode()
        return re.search(r'name="csrf-token" content="([^"]+)"',html).group(1)
    assert client.post('/login',data={'csrf_token':token('/login'),'email':'alice@example.test','password':PASSWORD}).status_code==302
    response=client.post('/api/chat',json={'message':'pression pneus'},headers={'X-CSRFToken':token('/chat')})
    assert response.status_code==200
    assert client.post('/logout',data={'csrf_token':token('/dashboard')}).status_code==302
    assert client.post('/api/chat',json={'message':'huile'}).status_code==401

def test_server_failure_atomicity(alice,app,monkeypatch):
    from app.routes import chat
    def fail(*args,**kwargs):
        raise RuntimeError('Erreur de recette simulée')
    monkeypatch.setattr(chat,'answer',fail)
    app.config['PROPAGATE_EXCEPTIONS']=False
    response=alice.post('/api/chat',json={'message':'huile'})
    assert response.status_code==500 and 'error' in response.json
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Conversation))==0
        assert db.session.scalar(db.select(db.func.count()).select_from(Message))==0

def test_restart_persistence(alice,app,vehicle,operation):
    cid=alice.post('/api/chat',json={'message':'huile'}).json['conversation_id']
    restarted=create_app(dict(TESTING=True,WTF_CSRF_ENABLED=False,SECRET_KEY=app.config['SECRET_KEY'],SQLALCHEMY_DATABASE_URI=app.config['SQLALCHEMY_DATABASE_URI']))
    client=restarted.test_client()
    assert client.post('/login',data={'email':'alice@example.test','password':PASSWORD}).status_code==302
    assert b'Dacia' in client.get('/dashboard').data
    assert len(client.get(f'/api/conversations/{cid}/messages').json['messages'])==2
    with restarted.app_context():
        assert db.session.get(Vehicle,vehicle) and db.session.get(Maintenance,operation)
        db.session.remove()
        db.engine.dispose()

def test_migrations_on_blank_database(tmp_path):
    app=create_app(dict(TESTING=True,SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'migrated.sqlite3')))
    runner=app.test_cli_runner()
    assert runner.invoke(args=['db','upgrade']).exit_code==0
    assert runner.invoke(args=['db','check']).exit_code==0
    assert app.test_client().get('/health').status_code==200
    assert app.test_client().get('/ready').status_code==200
    assert runner.invoke(args=['import-faq']).exit_code==0
    assert runner.invoke(args=['db','downgrade','base']).exit_code==0
    assert app.test_client().get('/health').status_code==200
    assert app.test_client().get('/ready').status_code==503
    assert runner.invoke(args=['db','upgrade']).exit_code==0

def test_pages_and_faq_performance(alice,app,vehicle):
    app.test_cli_runner().invoke(args=['import-faq'])
    for path in ('/','/dashboard','/vehicles','/chat',f'/vehicles/{vehicle}/maintenance'):
        start=perf_counter()
        assert alice.get(path).status_code==200
        assert perf_counter()-start<3
    start=perf_counter()
    assert alice.post('/api/chat',json={'message':'pression pneus'}).json['status']=='generale'
    assert perf_counter()-start<2

def test_counter_update_changes_due_status(alice,app,vehicle,operation):
    from test_platform import VEHICLE
    with app.app_context():
        op=db.session.get(Maintenance,operation)
        op.next_mileage=51000
        db.session.commit()
        assert op.due_status()=='future'
    alice.post(f'/vehicles/{vehicle}/edit',data={**VEHICLE,'mileage':'51000'})
    with app.app_context():
        assert db.session.get(Maintenance,operation).due_status()=='atteinte'

def test_personal_data_cascade(alice,app,vehicle,operation):
    alice.post('/api/chat',json={'message':'huile'})
    alice.post('/account/delete',data={'confirm':'y','password':PASSWORD})
    with app.app_context():
        for model in (Vehicle,Maintenance,Conversation,Message):
            assert db.session.scalar(db.select(db.func.count()).select_from(model))==0
