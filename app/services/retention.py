from datetime import datetime, timedelta, timezone

from app import db
from app.models import Conversation, Message


def expired_query(days, now=None):
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    latest = (
        db.select(Message.conversation_id, db.func.max(Message.created_at).label('last'))
        .group_by(Message.conversation_id)
        .subquery()
    )
    return (
        db.select(Conversation)
        .outerjoin(latest, Conversation.id == latest.c.conversation_id)
        .where(db.func.coalesce(latest.c.last, Conversation.created_at) < cutoff)
        .with_for_update(of=Conversation)
    )
