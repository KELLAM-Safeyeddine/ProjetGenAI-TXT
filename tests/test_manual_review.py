from pathlib import Path

from app import db
from app.models import ManualReview, ManuelPassage, User
from app.services.manual_inventory import file_hash


def seed(app):
    with app.app_context():
        path = Path(app.config['MANUALS_DIR']) / 'dacia/bigster/2026/manuel.pdf'
        row = ManuelPassage(
            brand='Dacia',
            model='Bigster',
            year=2026,
            page=1,
            position=0,
            section='Pneus',
            contenu='Texte de recette : vérifier les pneumatiques à froid, sans valeur réelle.',
            search_index='',
            source='equipe: test',
            added_at='2026-11-14',
            document_metadata={'sha256': file_hash(path), 'controle_visuel_requis': True},
        )
        db.session.add(row)
        db.session.commit()
        return row.id


def promote(app):
    with app.app_context():
        db.session.scalar(db.select(User).where(User.name == 'alice')).role = 'admin'
        db.session.commit()


def test_manual_review_requires_admin_and_exact_pdf(app, alice):
    ident = seed(app)
    assert alice.get('/admin/manuels').status_code == 403
    assert alice.get(f'/admin/manuels/{ident}/page.png').status_code == 403
    promote(app)
    assert alice.get('/admin/manuels').status_code == 200
    rendered = alice.get(f'/admin/manuels/{ident}/page.png')
    assert rendered.status_code == 200 and rendered.data.startswith(b'\x89PNG')
    with app.app_context():
        row = db.session.get(ManuelPassage, ident)
        row.document_metadata = {**row.document_metadata, 'sha256': '0' * 64}
        db.session.commit()
    assert alice.get(f'/admin/manuels/{ident}/page.png').status_code == 409


def test_review_is_audited_and_stale_decision_cannot_overwrite(app, alice):
    ident = seed(app)
    promote(app)
    text = 'Texte corrigé de recette, contrôlé sur le PDF fictif uniquement, sans prescription.'
    payload = dict(
        revision='0',
        action='corriger',
        contenu=text,
        note='Lecture du rendu complet, conditions vérifiées.',
    )
    assert alice.post(f'/admin/manuels/{ident}', data=payload).status_code == 302
    assert alice.post(f'/admin/manuels/{ident}', data=payload).status_code == 409
    with app.app_context():
        row = db.session.get(ManuelPassage, ident)
        assert row.contenu == text and not row.document_metadata['controle_visuel_requis']
        log = db.session.scalar(db.select(ManualReview))
        assert log.admin_id and log.before['metadata']['controle_visuel_requis']
        assert log.after['contenu'] == text and log.identity['sha256']
