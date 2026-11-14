from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.legacy.models import FAQ as FAQ
from app.legacy.models import VehicleCatalog as VehicleCatalog
from app.legacy.models import WebPassage as WebPassage


def now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default='user')
    auth_version = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    vehicles = db.relationship('Vehicle', backref='owner', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='owner', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.auth_version = (self.auth_version or 0) + 1

    def get_id(self):
        return f'{self.id}:{self.auth_version}'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    __table_args__ = (db.CheckConstraint('mileage >= 0', name='vehicle_mileage_nonnegative'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    engine_type = db.Column(db.Text, nullable=True)
    mileage = db.Column(db.BigInteger, nullable=True)
    manual_reference = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    maintenance = db.relationship('Maintenance', backref='vehicle', cascade='all, delete-orphan')


class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    __table_args__ = (
        db.CheckConstraint('mileage >= 0 AND cost >= 0', name='maintenance_nonnegative'),
    )
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False)
    date = db.Column(db.Date, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text, nullable=False, default='')
    next_date = db.Column(db.Date)
    next_mileage = db.Column(db.Integer)

    def due_status(self, today=None):
        today = today or date.today()
        if self.next_date is None and self.next_mileage is None:
            return 'absente'
        if (self.next_date is not None and self.next_date < today) or (
            self.next_mileage is not None
            and self.vehicle.mileage is not None
            and self.vehicle.mileage > self.next_mileage
        ):
            return 'dépassée'
        if self.next_date == today or (
            self.next_mileage is not None
            and self.vehicle.mileage is not None
            and self.next_mileage == self.vehicle.mileage
        ):
            return 'atteinte'
        return 'future'

    def is_due_soon(self, today=None, days=30, kilometres=1000):
        from datetime import timedelta

        today = today or date.today()
        if self.due_status(today) != 'future':
            return False
        return bool(
            self.next_date
            and self.next_date <= today + timedelta(days=days)
            or self.next_mileage is not None
            and self.vehicle.mileage is not None
            and self.next_mileage - self.vehicle.mileage <= kilometres
        )


class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    messages = db.relationship(
        'Message', backref='conversation', cascade='all, delete-orphan', order_by='Message.id'
    )


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True
    )
    role = db.Column(db.String(16), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(24))
    references = db.Column(db.JSON, nullable=False, default=list, server_default='[]')
    vehicle_context = db.Column(db.JSON)
    source_line = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    feedback = db.relationship(
        'Feedback', backref='message', uselist=False, cascade='all, delete-orphan'
    )


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False, unique=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    helpful = db.Column(db.Boolean, nullable=False)
    comment = db.Column(db.Text, nullable=False, default='')
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, onupdate=now)


class ManuelPassage(db.Model):
    __tablename__ = 'manuel_passages'
    __table_args__ = (
        db.Index('ix_manuel_vehicle', 'brand', 'model', 'year'),
        db.UniqueConstraint('brand', 'model', 'year', 'page', 'position', name='uq_manuel_passage'),
    )
    id = db.Column(db.Integer, primary_key=True)
    review_revision = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    page = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    search_index = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(1000), nullable=False)
    added_at = db.Column(db.String(10), nullable=False)
    document_metadata = db.Column(db.JSON, nullable=False, default=dict, server_default='{}')

    def as_passage(self):
        return dict(
            brand=self.brand,
            model=self.model,
            year=self.year,
            page=self.page,
            active=self.active,
            section=self.section,
            contenu=self.contenu,
            search_index=self.search_index,
            source=self.source,
            position=self.position,
            **(self.document_metadata or {}),
        )


class ManualReview(db.Model):
    """Journal conservé même après réimport : identité et empreinte, pas une FK de passage."""

    __tablename__ = 'manual_reviews'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    passage_id = db.Column(db.Integer, nullable=False)
    identity = db.Column(db.JSON, nullable=False)
    before = db.Column(db.JSON, nullable=False)
    after = db.Column(db.JSON, nullable=False)
    action = db.Column(db.String(16), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
