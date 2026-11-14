from flask import Blueprint, jsonify, make_response, render_template
from flask_login import current_user, login_required

from app import db
from app.models import Conversation, Feedback, Vehicle

bp = Blueprint('privacy', __name__)


@bp.get('/confidentialite')
def policy():
    return render_template('privacy.html')


@bp.get('/conditions')
def terms():
    return render_template('terms.html')


@bp.get('/account/export')
@login_required
def export():
    cars = db.session.scalars(db.select(Vehicle).where(Vehicle.user_id == current_user.id)).all()
    chats = db.session.scalars(
        db.select(Conversation).where(Conversation.user_id == current_user.id)
    ).all()
    feedback = db.session.scalars(
        db.select(Feedback).where(Feedback.user_id == current_user.id)
    ).all()
    data = dict(
        compte=dict(nom=current_user.name, email=current_user.email),
        vehicules=[
            dict(
                id=v.id,
                marque=v.brand,
                modele=v.model,
                annee=v.year,
                motorisation=v.engine_type,
                kilometrage=v.mileage,
                entretiens=[
                    dict(
                        type=m.type,
                        date=m.date.isoformat(),
                        kilometrage=m.mileage,
                        cout_mad=str(m.cost),
                        notes=m.notes,
                        prochaine_date=m.next_date.isoformat() if m.next_date else None,
                        prochain_kilometrage=m.next_mileage,
                    )
                    for m in v.maintenance
                ],
            )
            for v in cars
        ],
        conversations=[
            dict(
                id=c.id,
                titre=c.title,
                date=c.created_at.isoformat(),
                messages=[
                    dict(
                        role=m.role,
                        contenu=m.content,
                        date=m.created_at.isoformat(),
                        vehicule=m.vehicle_context,
                        references=m.references,
                    )
                    for m in c.messages
                ],
            )
            for c in chats
        ],
        retours=[
            dict(message_id=f.message_id, utile=f.helpful, commentaire=f.comment) for f in feedback
        ],
    )
    response = make_response(jsonify(data))
    response.headers['Content-Disposition'] = 'attachment; filename=mes-donnees-autohelp.json'
    return response
