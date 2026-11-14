from pathlib import Path
from app import db
from app.models import ManuelPassage
from manual_fixtures import declare

ROOT=Path(__file__).resolve().parents[1]


def test_health_does_not_query_database(app,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('La vivacité ne doit pas accéder à la base.')
    monkeypatch.setattr(db.session,'execute',forbidden)
    response=app.test_client().get('/health')
    assert response.status_code==200 and response.json=={'status':'ok'}
    assert app.test_client().get('/ready').status_code==503


def test_read_only_manual_import_preserves_files_and_indexes_passages(app,tmp_path,monkeypatch):
    root=tmp_path/'pdfs';declare(root)
    app.config['MANUALS_DIR']=root
    original=(root/'index.json').read_bytes()
    write_text=Path.write_text
    def guard(path,*args,**kwargs):
        if path.resolve()==root.resolve() or root.resolve() in path.resolve().parents:
            raise PermissionError('Montage PDF en lecture seule.')
        return write_text(path,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',guard)
    result=app.test_cli_runner().invoke(args=['import-manuels','--lecture-seule'])
    assert result.exit_code==0,result.output
    assert 'lecture seule' in result.output
    assert (root/'index.json').read_bytes()==original and not (root/'index.json.tmp').exists()
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(ManuelPassage).where(ManuelPassage.active.is_(True)))>0
    again=app.test_cli_runner().invoke(args=['import-manuels','--lecture-seule'])
    assert again.exit_code==0 and (root/'index.json').read_bytes()==original


def test_delivery_configuration_has_no_secret_values_and_read_only_mount():
    for line in (ROOT/'.env.example').read_text().splitlines():
        if line and not line.startswith('#'):assert line.endswith('=') and line.count('=')==1
    compose=(ROOT/'docker-compose.yml').read_text()
    assert any(mount in compose for mount in ('./manuels:/app/data/manuels:ro','./data/manuels:/app/data/manuels:ro'))
    assert 'autohelp_data:/app/instance' in compose and 'sqlite:////app/instance/autohelp.db' in compose
    dockerfile=(ROOT/'Dockerfile').read_text()
    assert 'USER auto' in dockerfile and 'EXPOSE 5000' in dockerfile and 'COPY . .' not in dockerfile
    assert 'COPY manuels' not in dockerfile and '--no-cache-dir' in dockerfile
    assert 'manuels/' not in [line.strip() for line in (ROOT/'.dockerignore').read_text().splitlines()]
