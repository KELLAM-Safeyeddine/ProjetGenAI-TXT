"""Application de charge éphémère, refusée hors activation explicite de recette."""

import importlib
import os
import sys
import tempfile
from pathlib import Path


def build_app():
    if os.environ.get('AUTOHELP_LOAD_TEST') != '1':
        raise RuntimeError('Cette application est exclusivement réservée à une recette isolée.')

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / 'tests'))
    from manual_fixtures import declare

    from app import create_app, db
    from app.models import ManuelPassage, User, Vehicle
    from app.services.evaluation_model import CONFIG, FakeModel
    from app.services.manual_access import link_manual
    from app.services.manual_import import extract_manual, load_index

    directory = Path(tempfile.mkdtemp(prefix='autohelp-charge-'))
    declare(directory / 'manuels')
    app = create_app(
        dict(
            TESTING=True,
            SECRET_KEY='fixture-charge-isolee-uniquement',
            SQLALCHEMY_DATABASE_URI='sqlite:///' + str(directory / 'charge.sqlite3'),
            MANUALS_DIR=directory / 'manuels',
            MANUAL_IMPORT_LOG=directory / 'import.log',
            **CONFIG,
        )
    )
    # Le transport factice n'effectue aucun appel réseau et ne diagnostique rien.

    importlib.import_module('app.services.llm_service')._post = FakeModel()
    with app.app_context():
        db.create_all()
        user = User(name='Recette charge', email='charge@example.test')
        user.set_password('Recette-charge-isolee-2026!')
        db.session.add(user)
        entries, _ = load_index(directory / 'manuels')
        rows, _ = extract_manual(entries[0])
        db.session.add_all(ManuelPassage(**r) for r in rows)
        db.session.flush()
        car = Vehicle(user_id=user.id, brand='Dacia', model='Bigster', year=2026, mileage=0)
        link_manual(car)
        db.session.add(car)
        db.session.commit()

    return app


app = build_app()
