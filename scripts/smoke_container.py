"""Recette isolée dans le conteneur : vrai PDF, transport simulé, aucun appel distant.

Lancer sur un volume de recette : docker compose exec web python scripts/smoke_container.py
"""
import json
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import User, Vehicle
from app.services.evaluation_model import CONFIG, FakeModel
from app.services import llm_service


def main():
    app = create_app()
    email = 'recette-' + secrets.token_hex(8) + '@example.test'
    password = secrets.token_urlsafe(24)
    runner = app.test_cli_runner()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        original = Path(app.config['MANUALS_DIR'])
        entry = next(e for e in json.loads((original / 'index.json').read_text())['manuels']
                     if (e['marque'], e['modele'], e['annee']) == ('Dacia', 'Bigster', 2026))
        destination = root / entry['chemin']
        destination.parent.mkdir(parents=True)
        shutil.copy2(original / entry['chemin'], destination)
        (root / 'index.json').write_text(json.dumps({'manuels': [entry]}))
        app.config.update(MANUALS_DIR=root, MANUAL_IMPORT_LOG=root / 'import.log')
        imported = runner.invoke(args=['import-manuels', '--lecture-seule'])
        assert imported.exit_code == 0, 'Échec import réel : consulter le journal interne.'
        print('Notice Bigster complète importée avec montage source en lecture seule.', flush=True)
        admin = runner.invoke(args=['create-admin', '--name', 'Recette temporaire', '--email', email],
                              input=password + '\n' + password + '\n')
        assert admin.exit_code == 0, 'Échec création CLI administrateur.'
        try:
            client = app.test_client()
            def csrf(path):
                return re.search(r'name="csrf-token" content="([^"]+)"', client.get(path).text)[1]
            assert client.post('/login', data={'email': email, 'password': password, 'csrf_token': csrf('/login')}).status_code == 302
            with app.app_context():
                user = db.session.scalar(db.select(User).where(User.email == email))
                vehicle = Vehicle(user_id=user.id, brand='Dacia', model='Bigster', year=2026, mileage=50000)
                db.session.add(vehicle)
                db.session.commit()
                vehicle_id = vehicle.id
            app.config.update(OPENAI_API_KEY='', GROQ_API_KEY='')
            response = client.post('/api/chat', json={'message': 'Comment contrôler le niveau d’huile moteur ?', 'vehicle_id': vehicle_id}, headers={'X-CSRFToken': csrf('/chat')})
            assert response.status_code == 200 and response.json['status'] == 'indisponible'
            app.config.update(CONFIG)
            llm_service._post = FakeModel()
            response = client.post('/api/chat', json={'message': 'Comment contrôler le niveau d’huile moteur ?', 'vehicle_id': vehicle_id}, headers={'X-CSRFToken': csrf('/chat')})
            assert response.status_code == 200, response.status_code
            data = response.json
            assert data['source'] == 'manuel' and data['references'], data['status']
            assert data['reply'].splitlines()[-1].startswith('Source : manuel Dacia Bigster 2026')
            print(json.dumps({'administrateur_cli': 'ok', 'csrf': 'actif', 'sans_cle': 'indisponibilite attendue',
                              'transport': 'factice, aucun réseau', 'source': data['source'], 'references': len(data['references'])}), flush=True)
        finally:
            with app.app_context():
                user = db.session.scalar(db.select(User).where(User.email == email))
                if user:
                    db.session.delete(user)
                    db.session.commit()
            print('Compte temporaire et données liées supprimés.', flush=True)


if __name__ == '__main__':
    main()
