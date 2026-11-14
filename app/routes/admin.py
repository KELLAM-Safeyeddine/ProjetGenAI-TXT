from functools import wraps

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms import DeleteForm, FAQForm
from app.models import FAQ

bp = Blueprint('admin', __name__, url_prefix='/admin/faq')


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.get('')
@admin_required
def index():
    entries = db.session.scalars(db.select(FAQ).order_by(FAQ.category, FAQ.id)).all()
    return render_template('admin.html', entries=entries)


def save(entry, form):
    entry.category = form.category.data
    entry.question = form.question.data
    entry.answer = form.answer.data
    entry.risk_level = form.risk_level.data
    entry.source = form.source.data or 'connaissance générale du domaine'
    entry.variants = [x.strip() for x in form.variants.data.splitlines() if x.strip()]
    entry.keywords = [x.strip() for x in form.keywords.data.splitlines() if x.strip()]
    if not entry.variants or not entry.keywords:
        form.keywords.errors.append('Ajoutez au moins une variante et un mot-clé.')
        return False
    db.session.add(entry)
    try:
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        form.question.errors.append('Cette question existe déjà.')
        return False


@bp.route('/new', methods=['GET', 'POST'])
@admin_required
def create():
    form = FAQForm()
    if form.validate_on_submit() and save(FAQ(), form):
        return redirect(url_for('admin.index'))
    return render_template(
        'form.html', form=form, title='Ajouter une réponse FAQ'
    ), 422 if form.errors else 200


@bp.route('/<int:faq_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(faq_id):
    entry = db.get_or_404(FAQ, faq_id)
    form = FAQForm(obj=entry)
    from flask import request

    if request.method == 'GET':
        form.variants.data = '\n'.join(entry.variants)
        form.keywords.data = '\n'.join(entry.keywords)
    if form.validate_on_submit() and save(entry, form):
        return redirect(url_for('admin.index'))
    return render_template(
        'form.html', form=form, title='Modifier la réponse FAQ'
    ), 422 if form.errors else 200


@bp.route('/<int:faq_id>/delete', methods=['GET', 'POST'])
@admin_required
def delete(faq_id):
    entry = db.get_or_404(FAQ, faq_id)
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for('admin.index'))
    return render_template(
        'form.html', form=form, title='Supprimer cette réponse FAQ', danger=True
    ), 422 if form.errors else 200
