import csv
import io

from flask import Blueprint, Response, abort, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Conversation, Feedback, Message
from app.routes.admin import admin_required

bp = Blueprint('feedback', __name__)


@bp.post('/api/messages/<int:message_id>/feedback')
@login_required
def save(message_id):
    row = db.first_or_404(
        db.select(Message)
        .join(Conversation)
        .where(
            Message.id == message_id,
            Conversation.user_id == current_user.id,
            Message.role == 'assistant',
        )
    )
    data = request.get_json(silent=True)
    if (
        not isinstance(data, dict)
        or set(data) - {'helpful', 'comment'}
        or type(data.get('helpful')) is not bool
        or not isinstance(data.get('comment', ''), str)
        or len(data.get('comment', '')) > 1000
    ):
        abort(400)
    entry = row.feedback or Feedback(message_id=row.id, user_id=current_user.id)
    entry.helpful = data['helpful']
    entry.comment = data.get('comment', '').strip()
    db.session.add(entry)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(
            error='Un retour a été enregistré entre-temps. Rechargez la conversation.'
        ), 409
    return jsonify(status='ok')


def csv_text(value):
    text = str(value)
    return (
        "'" + text
        if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n'))
        else text
    )


@bp.get('/admin/retours.csv')
@admin_required
def export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['message_id', 'compte_id', 'utile', 'commentaire', 'date'])
    for row in db.session.scalars(
        db.select(Feedback).order_by(Feedback.id).execution_options(yield_per=100)
    ):
        writer.writerow(
            [
                row.message_id,
                row.user_id,
                'oui' if row.helpful else 'non',
                csv_text(row.comment),
                row.updated_at.isoformat(),
            ]
        )
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=retours-autohelp.csv'},
    )
