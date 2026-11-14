import json
from html.parser import HTMLParser

import pytest
from manual_fixtures import TEST_MANUALS
from test_platform import VEHICLE

from app import db
from app.models import Vehicle, VehicleCatalog
from app.services.vehicle_catalog import load_catalog


class Selects(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.current = None
        self.fields = {}
        self.attributes = {}
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'select':
            self.current = attrs.get('name')
            self.fields[self.current] = []
            self.attributes[self.current] = attrs
        if tag == 'option' and self.current:
            self.fields[self.current].append(attrs.get('value'))

    def handle_endtag(self, tag):
        if tag == 'select':
            self.current = None


def test_source_dataset_has_no_fabricated_ranges():
    data = load_catalog()
    assert set(data['marques']) == {'Dacia', 'Renault', 'Hyundai', 'Peugeot', 'Volkswagen'}
    assert {row['annee'] for row in data['vehicules']} == set(range(2021, 2027))
    assert all(row['intervalle_entretien'] is None for row in data['vehicules'])
    assert all(row['source'] and row['preuve_annee'] for row in data['vehicules'])


def test_import_is_idempotent_and_does_not_modify_private_vehicles(app, vehicle):
    runner = app.test_cli_runner()
    for _ in range(2):
        result = runner.invoke(args=['import-vehicules'])
        assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(VehicleCatalog)) == len(
            load_catalog()['vehicules']
        )
        assert db.session.get(Vehicle, vehicle).model == 'Bigster'


@pytest.mark.parametrize('brand,model,year', TEST_MANUALS)
def test_all_allowed_combinations_are_accepted(alice, app, brand, model, year):
    assert (
        alice.post(
            '/vehicles/new', data={**VEHICLE, 'brand': brand, 'model': model, 'year': str(year)}
        ).status_code
        == 302
    )
    with app.app_context():
        car = db.session.scalar(db.select(Vehicle))
        assert (car.brand, car.model, car.year) == (brand, model, year)


@pytest.mark.parametrize(
    'changes',
    [
        {'brand': 'Lexus'},
        {'brand': 'Renault', 'model': 'Clio', 'year': '2026'},
        {'model': 'Sandero', 'year': '2022'},
        {'model': 'Sandero Stepway', 'year': '2021'},
        {'model': 'Sandero Stepway X'},
        {'year': '1949'},
        {'year': '9999'},
        {'year': 'abc'},
        {'year': '2026.5'},
        {'brand': ''},
        {'model': ''},
        {'brand': '<script>alert(1)</script>'},
    ],
)
def test_forged_outside_combination_is_rejected_without_write(alice, app, vehicle, changes):
    for path in ('/vehicles/new', f'/vehicles/{vehicle}/edit'):
        response = alice.post(path, data={**VEHICLE, **changes})
        assert response.status_code == 422
        assert 'autoris' in response.text or 'obligatoire' in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Vehicle)) == 1
        car = db.session.get(Vehicle, vehicle)
        assert (car.brand, car.model, car.year) == ('Dacia', 'Bigster', 2026)


def test_optional_fields_and_missing_manual(alice, app):
    assert (
        alice.post(
            '/vehicles/new',
            data=dict(brand='Dacia', model='Sandero', year='2021', engine_type='', mileage=''),
        ).status_code
        == 302
    )
    with app.app_context():
        car = db.session.scalar(db.select(Vehicle))
        assert (car.brand, car.model, car.year, car.mileage) == ('Dacia', 'Sandero', 2021, None)
        assert not car.manual_reference
    assert 'Compteur non renseigné' in alice.get('/vehicles').text


def test_manual_link_normalizes_to_canonical_choice(alice, app, tmp_path):
    from manual_fixtures import declare

    root = tmp_path / 'manuels'
    declare(root)
    app.config['MANUALS_DIR'] = root
    assert app.test_cli_runner().invoke(args=['import-manuels']).exit_code == 0
    data = dict(brand='  DÁ CIA ', model=' BÍG   STER ', year='2026', mileage='', engine_type='')
    assert alice.post('/vehicles/new', data=data).status_code == 302
    with app.app_context():
        car = db.session.scalar(db.select(Vehicle))
        assert car.brand == 'Dacia' and car.model == 'Bigster'
        assert car.manual_reference == dict(marque='Dacia', modele='Bigster', annee=2026)
        vid = car.id
    response = alice.post('/api/chat', json=dict(message='pression pneus', vehicle_id=vid)).json
    assert response['source'] == 'manuel' and response['references'][0]['modele'] == 'Bigster'


def test_form_and_catalog_use_only_shared_allowlist(alice):
    rows = alice.get('/api/vehicle-catalog').json['vehicles']
    assert {(r['brand'], r['model'], r['year']) for r in rows} == set(TEST_MANUALS)
    html = alice.get('/vehicles/new').text
    parsed = Selects(html)
    selects = parsed.fields
    assert selects['brand'] == ['Dacia']
    assert set(selects['model']) == {'', *dict.fromkeys(m for _, m, _ in TEST_MANUALS)}
    assert 'disabled' in parsed.attributes['brand']
    assert '<datalist id="brand-suggestions"' not in html
    assert '<datalist id="model-suggestions"' not in html
    assert 'Lexus' not in html and 'Renault' not in html
    alice.post('/logout')
    assert alice.get('/api/vehicle-catalog').status_code == 401


def test_server_year_choices_follow_model_on_edit_and_errors(alice, app, vehicle):
    for model, year, expected in [
        ('Sandero', 2021, ['2021', '2026']),
        ('Bigster', 2026, ['2026']),
        ('Sandero Stepway', 2026, ['2026']),
    ]:
        with app.app_context():
            car = db.session.get(Vehicle, vehicle)
            car.model = model
            car.year = year
            db.session.commit()
        html = alice.get(f'/vehicles/{vehicle}/edit').text
        assert Selects(html).fields['year'] == expected
        invalid = alice.post('/vehicles/new', data={**VEHICLE, 'model': model, 'year': '2022'})
        assert invalid.status_code == 422
        assert Selects(invalid.text).fields['year'] == expected


def test_old_outside_vehicle_is_preserved_until_valid_resubmission(alice, app, vehicle):
    with app.app_context():
        car = db.session.get(Vehicle, vehicle)
        car.brand = 'Lexus'
        car.model = '<b>RX</b>'
        car.year = 1950
        db.session.commit()
    page = alice.get(f'/vehicles/{vehicle}/edit')
    assert page.status_code == 200 and 'hors liste' in page.text
    assert '&lt;b&gt;RX&lt;/b&gt;' in page.text and '<b>RX</b>' not in page.text
    with app.app_context():
        assert db.session.get(Vehicle, vehicle).brand == 'Lexus'
    assert (
        alice.post(
            f'/vehicles/{vehicle}/edit',
            data={**VEHICLE, 'brand': 'Lexus', 'model': '<b>RX</b>', 'year': '1950'},
        ).status_code
        == 422
    )
    with app.app_context():
        assert db.session.get(Vehicle, vehicle).brand == 'Lexus'
    assert alice.post(f'/vehicles/{vehicle}/edit', data=VEHICLE).status_code == 302
    with app.app_context():
        assert db.session.get(Vehicle, vehicle).brand == 'Dacia'


def test_cli_lists_only_outside_vehicles_without_modification(app, vehicle):
    with app.app_context():
        valid = db.session.get(Vehicle, vehicle)
        old = Vehicle(user_id=valid.user_id, brand='Renault', model='Clio', year=2026)
        db.session.add(old)
        db.session.commit()
        old_id = old.id
    result = app.test_cli_runner().invoke(args=['lister-vehicules-hors-liste'])
    assert result.exit_code == 0, result.output
    assert f'ID {old_id} |' in result.output and 'Renault | Clio | 2026' in result.output
    assert f'ID {vehicle} |' not in result.output and '1 véhicule(s) hors liste' in result.output
    with app.app_context():
        assert db.session.get(Vehicle, old_id).brand == 'Renault'


def test_chat_selector_excludes_outside_but_api_announces_no_manual(alice, app, vehicle):
    with app.app_context():
        valid = db.session.get(Vehicle, vehicle)
        outside = Vehicle(user_id=valid.user_id, brand='Renault', model='Clio', year=2026)
        db.session.add(outside)
        db.session.commit()
        outside_id = outside.id
    html = alice.get('/chat').text
    selector = html.split('id="vehicle-select"', 1)[1].split('</select>', 1)[0]
    assert f'value="{vehicle}"' in selector and f'value="{outside_id}"' not in selector
    assert 'aucun manuel disponible' in html and 'Renault Clio 2026' in html
    response = alice.post(
        '/api/chat', json=dict(message='Quelle huile pour le moteur ?', vehicle_id=outside_id)
    ).json
    assert response['status'] == 'hors_perimetre' and not response['references']
    assert "Je n'ai pas le manuel du Renault Clio 2026" in response['reply']


def test_invalid_import_does_not_empty_catalog(app, tmp_path, monkeypatch):
    from app.services import vehicle_catalog

    data = load_catalog()
    data['vehicules'][0]['annee'] = 1900
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    monkeypatch.setattr(vehicle_catalog, 'CATALOG_PATH', path)
    result = app.test_cli_runner().invoke(args=['import-vehicules'])
    assert result.exit_code != 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(VehicleCatalog)) > 0


def test_cascade_javascript_updates_years_on_model_change(alice):
    # Exécution du vrai script avec un petit DOM de listes ; Node reste facultatif.
    import re
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which('node')
    if not node:
        pytest.skip('Node absent ; les choix serveur restent couverts par pytest.')
    html = alice.get('/vehicles/new').text
    rows = json.loads(
        re.search(
            r'<script id="allowed-vehicles" type="application/json">(.*?)</script>', html
        ).group(1)
    )
    source = (Path(__file__).resolve().parents[1] / 'app/static/js/vehicles.js').read_text(
        encoding='utf-8'
    )
    runner = r"""
const fs=require('fs'),assert=require('assert/strict');
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const model={value:'',addEventListener(event,fn){assert.equal(event,'change');this.change=fn;}};
const year={options:[],value:'',addEventListener(event,fn){this.change=fn;},replaceChildren(){this.options=[];this.value='';},append(option){this.options.push(option);if(this.options.length===1)this.value=option.value;}};
const engine_version={options:[],value:'',replaceChildren(){this.options=[];},append(option){this.options.push(option);}};
    global.document={getElementById(id){return id==='vehicle-form'?{elements:{model,year,engine_version}}:{textContent:JSON.stringify(data.rows)};},createElement(){return {value:'',textContent:''};}};
eval(data.source);
model.value='Sandero';model.change();assert.deepEqual(year.options.map(o=>o.value),['2021','2026']);
year.value='2021';model.value='Bigster';model.change();assert.deepEqual(year.options.map(o=>o.value),['2026']);assert.equal(year.value,'2026');
model.value='Sandero Stepway';model.change();assert.deepEqual(year.options.map(o=>o.value),['2026']);
model.value='';model.change();assert.deepEqual(year.options.map(o=>o.value),['']);
"""
    result = subprocess.run(
        [node, '-e', runner],
        input=json.dumps(dict(rows=rows, source=source)),
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


def test_vehicle_creation_still_requires_csrf(alice, app):
    app.config['WTF_CSRF_ENABLED'] = True
    assert alice.post('/vehicles/new', data=VEHICLE).status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Vehicle)) == 0
