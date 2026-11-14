import io

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user
from wtforms import HiddenField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Length

from app import db
from app.forms import FrenchForm
from app.models import ManualReview, ManuelPassage
from app.routes.admin import admin_required
from app.services.chatbot_service import normalize
from app.services.manual_inventory import file_hash, manuals_root, read_manifest
from app.services.manual_policy import reference_key

bp = Blueprint('manual_review', __name__, url_prefix='/admin/manuels')


class ReviewForm(FrenchForm):
    revision = HiddenField(validators=[InputRequired()])
    action = SelectField(
        'Décision',
        choices=[
            ('bloquer', 'Garder bloqué'),
            ('valider', 'Lever la réserve'),
            ('corriger', 'Corriger puis valider'),
        ],
    )
    contenu = TextAreaField('Texte corrigé', validators=[Length(max=10000)])
    note = TextAreaField(
        'Motif et éléments vérifiés sur le PDF',
        validators=[InputRequired(), Length(min=15, max=1000)],
    )


def pdf_for(row):
    root = manuals_root()
    matches = [
        e
        for e in read_manifest(root)['manuels']
        if reference_key(e['marque'], e['modele'], e['annee'])
        == reference_key(row.brand, row.model, row.year)
    ]
    if len(matches) != 1:
        abort(404)
    entry = matches[0]
    path = (root / entry['chemin']).resolve()
    expected = (row.document_metadata or {}).get('sha256')
    if (
        root not in path.parents
        or not path.is_file()
        or not expected
        or file_hash(path) != expected
    ):
        abort(409, description='Le PDF exact du passage est absent ou a changé.')
    return path


@bp.get('')
@admin_required
def index():
    query = db.select(ManuelPassage).where(ManuelPassage.active.is_(True))
    if request.args.get('tous') != '1':
        query = query.where(
            ManuelPassage.document_metadata['controle_visuel_requis'].as_boolean().is_(True)
        )
    rows = db.paginate(query.order_by(ManuelPassage.id), per_page=30, max_per_page=30)
    return render_template('manual_reviews.html', rows=rows)


@bp.get('/<int:passage_id>/page.png')
@admin_required
def image(passage_id):
    import pdfplumber

    row = db.get_or_404(ManuelPassage, passage_id)
    with pdfplumber.open(pdf_for(row)) as pdf:
        if not 1 <= row.page <= len(pdf.pages):
            abort(404)
        buffer = io.BytesIO()
        pdf.pages[row.page - 1].to_image(resolution=110).save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', max_age=0)


@bp.route('/<int:passage_id>', methods=['GET', 'POST'])
@admin_required
def review(passage_id):
    row = db.get_or_404(ManuelPassage, passage_id)
    if not row.active:
        abort(404)
    form = ReviewForm()
    if request.method == 'GET':
        form.revision.data = str(row.review_revision)
        form.contenu.data = row.contenu
    if form.validate_on_submit():
        if form.revision.data != str(row.review_revision):
            abort(409)
        # Une validation exige la présence de l'édition exacte ; pas de levée aveugle.
        pdf_for(row)
        text = form.contenu.data.strip() if form.action.data == 'corriger' else row.contenu
        if len(text) < 40:
            form.contenu.errors.append('Conservez au moins 40 caractères utiles du PDF.')
        else:
            metadata = dict(row.document_metadata or {})
            metadata['controle_visuel_requis'] = form.action.data == 'bloquer'
            metadata['revue_admin'] = True
            changed = db.session.execute(
                db.update(ManuelPassage)
                .where(
                    ManuelPassage.id == row.id, ManuelPassage.review_revision == row.review_revision
                )
                .values(
                    contenu=text,
                    search_index=normalize(text),
                    document_metadata=metadata,
                    review_revision=row.review_revision + 1,
                )
                .execution_options(synchronize_session=False)
            )
            if changed.rowcount != 1:
                db.session.rollback()
                abort(409)
            db.session.add(
                ManualReview(
                    admin_id=current_user.id,
                    passage_id=row.id,
                    identity=dict(
                        marque=row.brand,
                        modele=row.model,
                        annee=row.year,
                        page_pdf=row.page,
                        position=row.position,
                        sha256=(row.document_metadata or {}).get('sha256'),
                    ),
                    before=dict(contenu=row.contenu, metadata=row.document_metadata),
                    after=dict(contenu=text, metadata=metadata),
                    action=form.action.data,
                    note=form.note.data.strip(),
                )
            )
            db.session.commit()
            flash(
                'Décision enregistrée et journalisée. Un réimport doit être revu séparément.',
                'success',
            )
            return redirect(url_for('manual_review.index'))
    logs = db.session.scalars(
        db.select(ManualReview)
        .where(ManualReview.passage_id == row.id)
        .order_by(ManualReview.id.desc())
    ).all()
    return render_template(
        'manual_review.html', row=row, form=form, logs=logs
    ), 422 if form.errors else 200
