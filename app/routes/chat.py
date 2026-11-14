from flask import Blueprint, abort, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from app import db
from app.models import Conversation, Message, Vehicle
from app.routes.vehicles import owned_vehicle
from app.services.answer_service import answer, present_stored_reply
from app.services.chatbot_service import MAX_MESSAGE_LENGTH
from app.services.conversation_context import build_history
from app.services.manual_access import identity, query_for, reference_for, references
from app.services.manual_policy import reference_key
from app.services.vehicle_catalog import allowed_vehicles

bp = Blueprint('chat', __name__)


def owned_conversation(conversation_id):
    query = db.select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == current_user.id
    )
    if request.method in ('POST', 'PATCH', 'DELETE'):
        query = query.with_for_update()
    return db.first_or_404(query)


def resource_id(data, name):
    if name not in data or data[name] is None:
        return None
    value = data[name]
    if type(value) is not int or value < 1:
        abort(400)
    return value


@bp.get('/chat')
@login_required
def index():
    vehicles = db.session.scalars(
        db.select(Vehicle).where(Vehicle.user_id == current_user.id)
    ).all()
    known_files = {reference_key(r['brand'], r['model'], r['year']) for r in allowed_vehicles()}
    allowed = [v for v in vehicles if reference_key(v.brand, v.model, v.year) in known_files]
    outside = [v for v in vehicles if reference_key(v.brand, v.model, v.year) not in known_files]
    known = references()
    return render_template(
        'chat.html',
        vehicles=allowed,
        outside_vehicles=outside,
        manual_available={
            v.id: bool(reference_for(v.brand, v.model, v.year, known)) for v in allowed
        },
    )


def manual_query(vehicle):
    return query_for(vehicle)


@bp.get('/vehicles/<int:vehicle_id>/manuel')
@login_required
def manual_pages(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    # Une référence historique ne doit pas ouvrir le manuel d'une version modifiée.
    expected = request.args.get('version')
    if expected is not None and identity(expected) != identity(
        f'{vehicle.brand}|{vehicle.model}|{vehicle.year}'
    ):
        abort(404)
    rows = db.session.scalars(manual_query(vehicle)).all()
    pages = sorted({row.page for row in rows})
    raw = request.args.get('page', str(pages[0]) if pages else '1')
    if not raw.isascii() or not raw.isdigit() or len(raw) > 6 or int(raw) < 1:
        abort(400)
    page = int(raw)
    if pages and page not in pages:
        abort(404)
    return render_template(
        'manual.html',
        vehicle=vehicle,
        pages=pages,
        page=page,
        passages=[p for p in rows if p.page == page],
    )


@bp.post('/api/chat')
@login_required
def chat():
    if not request.is_json:
        return jsonify(error='Envoyez un objet JSON avec le champ message.'), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Le corps doit être un objet JSON valide.'), 400
    if set(data) - {'message', 'conversation_id', 'vehicle_id'}:
        return jsonify(error='Champ inconnu dans la requête.'), 400
    message = data.get('message')
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(error='Le message doit contenir de 1 à 1 000 caractères.'), 400
    conversation_id = resource_id(data, 'conversation_id')
    vehicle_id = resource_id(data, 'vehicle_id')
    vehicle = owned_vehicle(vehicle_id) if vehicle_id else None
    conversation = (
        owned_conversation(conversation_id)
        if conversation_id
        else Conversation(user_id=current_user.id)
    )
    context = None
    if vehicle:
        context = dict(
            id=vehicle.id,
            marque=vehicle.brand,
            modele=vehicle.model,
            annee=vehicle.year,
            motorisation=vehicle.engine_type,
            kilometrage=vehicle.mileage,
            manual_reference=reference_for(vehicle.brand, vehicle.model, vehicle.year),
        )
    rows = (
        list(
            db.session.scalars(
                db.select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.id.desc())
                .limit(80)
            )
        )
        if conversation.id
        else []
    )
    previous = [
        dict(role=m.role, content=m.content, vehicle=m.vehicle_context, source=m.source)
        for m in reversed(rows)
    ]
    history, summary = build_history(previous, context)

    def manual_loader():
        return (
            [row.as_passage() for row in db.session.scalars(manual_query(vehicle))]
            if vehicle
            else []
        )

    result = answer(
        message,
        vehicle=context,
        history=history,
        summary=summary,
        manual_loader=manual_loader,
        config=current_app.config,
    )
    db.session.add(conversation)
    db.session.flush()
    saved_messages = [
        Message(
            conversation_id=conversation.id,
            role='user',
            content=message.strip(),
            vehicle_context=context,
        ),
        Message(
            conversation_id=conversation.id,
            role='assistant',
            content=result['reply'],
            source=result['source'],
            references=result['references'],
            vehicle_context=context,
            source_line=result['source_line'],
        ),
    ]
    db.session.add_all(saved_messages)
    db.session.commit()
    payload = dict(
        reply=result['reply'],
        message_id=saved_messages[-1].id,
        conversation_id=conversation.id,
        source=result['source'],
        references=result['references'],
        source_line=result['source_line'],
        vehicle=context,
        status=result['status'],
        is_general=result['source'] == 'faq',
    )
    if 'score' in result:
        payload['score'] = result['score']
    if 'faq_id' in result:
        payload['faq_id'] = result['faq_id']
    return jsonify(payload)


@bp.get('/api/conversations')
@login_required
def conversations():
    preview = (
        db.select(Message.content)
        .where(Message.conversation_id == Conversation.id)
        .order_by(Message.id)
        .limit(1)
        .scalar_subquery()
    )
    query = db.select(
        Conversation.id, Conversation.created_at, Conversation.title, preview.label('preview')
    ).where(Conversation.user_id == current_user.id)
    before = before_cursor()
    if before:
        query = query.where(Conversation.id < before)
    rows = db.session.execute(query.order_by(Conversation.id.desc()).limit(51)).all()
    return jsonify(
        next_before_id=rows[49].id if len(rows) > 50 else None,
        conversations=[
            dict(
                id=c.id,
                created_at=c.created_at.isoformat(),
                title=c.title or (c.preview[:65] if c.preview else 'Conversation'),
            )
            for c in rows[:50]
        ],
    )


@bp.patch('/api/conversations/<int:conversation_id>')
@login_required
def rename(conversation_id):
    conversation = owned_conversation(conversation_id)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'title'} or not isinstance(data['title'], str):
        abort(400)
    title = ' '.join(data['title'].split())
    if not 1 <= len(title) <= 80:
        return jsonify(error='Le titre doit contenir entre 1 et 80 caractères.'), 422
    conversation.title = title
    db.session.commit()
    return jsonify(status='ok', title=title)


@bp.delete('/api/conversations/<int:conversation_id>')
@login_required
def delete_conversation(conversation_id):
    conversation = owned_conversation(conversation_id)
    db.session.delete(conversation)
    db.session.commit()
    return jsonify(status='ok')


@bp.get('/api/conversations/<int:conversation_id>/messages')
@login_required
def messages(conversation_id):
    from sqlalchemy.orm import selectinload

    conversation = owned_conversation(conversation_id)
    query = db.select(Message).where(Message.conversation_id == conversation.id)
    before = before_cursor()
    if before:
        query = query.where(Message.id < before)
    rows = db.session.scalars(
        query.options(selectinload(Message.feedback)).order_by(Message.id.desc()).limit(101)
    ).all()
    return jsonify(
        conversation_id=conversation.id,
        next_before_id=rows[99].id if len(rows) > 100 else None,
        messages=[public_message(m) for m in reversed(rows[:100])],
    )


def before_cursor():
    raw = request.args.get('before_id')
    if raw is None:
        return None
    if not raw.isascii() or not raw.isdigit() or len(raw) > 18 or int(raw) < 1:
        abort(400)
    return int(raw)


def public_message(message):
    content = message.content
    line = message.source_line or ''
    references = message.references or []
    # Aucun historique n'est réécrit en base et aucune référence n'est créée ici.
    if message.role == 'assistant':
        content, line = present_stored_reply(content, message.source, line)
    return dict(
        id=message.id,
        role=message.role,
        content=content,
        created_at=message.created_at.isoformat(),
        source=message.source,
        source_line=line,
        references=references,
        vehicle=message.vehicle_context,
        feedback=dict(helpful=message.feedback.helpful, comment=message.feedback.comment)
        if message.feedback
        else None,
    )
