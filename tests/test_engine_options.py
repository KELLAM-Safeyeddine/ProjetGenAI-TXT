from app import db
from app.models import ManuelPassage, Vehicle


def test_engine_choices_are_exact_and_legacy_text_remains_compatible(app, alice):
    with app.app_context():
        for model, version in [('Bigster', 'GPL'), ('Duster', 'Diesel')]:
            db.session.add(
                ManuelPassage(
                    brand='Dacia',
                    model=model,
                    year=2026,
                    page=1,
                    position=0,
                    section='test',
                    contenu='Texte fictif',
                    search_index='',
                    source='equipe: test',
                    added_at='2026-11-14',
                    document_metadata={'versions': [version]},
                )
            )
        db.session.commit()
    data = dict(brand='Dacia', model='Bigster', year='2026', engine_version='Diesel')
    assert alice.post('/vehicles/new', data=data).status_code == 422
    data['engine_version'] = 'GPL'
    assert alice.post('/vehicles/new', data=data).status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(Vehicle)).engine_type == 'GPL'
    data.update(engine_version='', engine_type='Ancienne description conservée')
    assert alice.post('/vehicles/new', data=data).status_code == 302
    rows = alice.get('/api/vehicle-catalog').json['vehicles']
    assert next(r for r in rows if r['model'] == 'Bigster')['motorisations'] == ['GPL']
