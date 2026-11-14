import re
from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)


class FrenchForm(FlaskForm):
    class Meta(FlaskForm.Meta):
        def get_translations(self, form):
            from wtforms.i18n import get_translations

            return get_translations(['fr'])


def clean_text(value):
    return value.strip() if isinstance(value, str) else value


def email_format(form, field):
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', field.data or ''):
        raise ValidationError('Adresse email invalide.')


class RegisterForm(FrenchForm):
    name = StringField(
        'Nom', filters=[clean_text], validators=[InputRequired(), Length(min=1, max=80)]
    )
    email = StringField(
        'Adresse email',
        filters=[lambda x: x.strip().lower() if x else x],
        validators=[InputRequired(), Length(max=254), email_format],
    )
    password = PasswordField(
        'Mot de passe (12 caractères minimum)',
        validators=[InputRequired(), Length(min=12, max=128)],
    )
    confirm = PasswordField(
        'Confirmer le mot de passe',
        validators=[
            InputRequired(),
            EqualTo('password', message='Les mots de passe doivent correspondre.'),
        ],
    )


class LoginForm(FrenchForm):
    email = StringField(
        'Adresse email',
        filters=[lambda x: x.strip().lower() if x else x],
        validators=[InputRequired(), Length(max=254), email_format],
    )
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(max=128)])


def clean_vehicle_text(value):
    return ' '.join(value.split()) if isinstance(value, str) else value


class VehicleForm(FrenchForm):
    brand = SelectField(
        'Marque',
        default='Dacia',
        validators=[InputRequired(message='La marque Dacia est obligatoire.')],
        validate_choice=False,
        render_kw={'disabled': True},
    )
    model = SelectField(
        'Modèle',
        validators=[InputRequired(message='Sélectionnez un modèle Dacia autorisé.')],
        validate_choice=False,
    )
    year = SelectField(
        'Année',
        coerce=int,
        validators=[InputRequired(message='Sélectionnez une année autorisée.')],
        validate_choice=False,
    )
    engine_type = StringField(
        'Motorisation (facultatif)',
        filters=[clean_vehicle_text],
        validators=[Optional()],
        render_kw={'list': 'engine-suggestions'},
    )
    mileage = IntegerField(
        'Kilométrage actuel (facultatif)',
        validators=[Optional(), NumberRange(min=0, max=9223372036854775807)],
        render_kw={'min': 0, 'max': 9223372036854775807, 'step': 1},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.services.manual_policy import identity
        from app.services.vehicle_catalog import allowed_vehicles

        self.catalog = allowed_vehicles()
        if self.year.process_errors:
            self.year.process_errors = [
                'Sélectionnez une année entière de la liste Dacia autorisée.'
            ]
        brands = ['Dacia']
        models = list(dict.fromkeys(row['model'] for row in self.catalog))
        # Normalisation exacte partagée avec la recherche de manuels ; stockage canonique.
        self.brand.data = next(
            (b for b in brands if identity(b) == identity(self.brand.data)), self.brand.data
        )
        self.model.data = next(
            (m for m in models if identity(m) == identity(self.model.data)), self.model.data
        )
        self.brand.choices = [(b, b) for b in brands]
        self.model.choices = [('', 'Choisir un modèle'), *((m, m) for m in models)]
        self.year.choices = [
            (row['year'], str(row['year']))
            for row in self.catalog
            if row['model'] == self.model.data
        ]
        # Ouvrir un ancien véhicule ne le corrige ni ne le supprime implicitement.
        obj = kwargs.get('obj')
        from app.services.manual_policy import reference_key

        self.legacy = bool(
            obj
            and reference_key(obj.brand, obj.model, obj.year)
            not in {reference_key(r['brand'], r['model'], r['year']) for r in self.catalog}
        )
        if not self.is_submitted() and self.legacy:
            self.brand.data = brands[0]
            if self.model.data and self.model.data not in models:
                self.model.choices.append(
                    (self.model.data, f'{self.model.data} (hors liste)', {'disabled': True})
                )
            if self.year.data not in {y for y, _ in self.year.choices}:
                self.year.choices.append(
                    (self.year.data, f'{self.year.data} (hors liste)', {'disabled': True})
                )

    def validate_brand(self, field):
        if field.data not in {row['brand'] for row in self.catalog}:
            raise ValidationError('Seule la marque Dacia est autorisée.')

    def validate_model(self, field):
        if field.data not in {row['model'] for row in self.catalog}:
            raise ValidationError('Sélectionnez un modèle Dacia présent dans la liste autorisée.')

    def validate_year(self, field):
        from app.services.manual_policy import reference_key

        if reference_key(self.brand.data, self.model.data, field.data) not in {
            reference_key(r['brand'], r['model'], r['year']) for r in self.catalog
        }:
            raise ValidationError(
                'Cette combinaison marque / modèle / année ne correspond à aucun manuel Dacia local identifié et autorisé. Importez son PDF avant de l’enregistrer.'
            )


class MaintenanceForm(FrenchForm):
    type = SelectField(
        'Opération',
        choices=[
            (x, x)
            for x in [
                'Vidange',
                'Filtres',
                'Pneus',
                'Freins',
                'Révision',
                'Batterie',
                'Refroidissement',
                'Distribution',
                'Autre',
            ]
        ],
    )
    date = DateField('Date de l’opération', validators=[InputRequired()])
    mileage = IntegerField(
        'Kilométrage lors de l’opération (km)',
        validators=[InputRequired(), NumberRange(min=0, max=10000000)],
    )
    cost = DecimalField(
        'Coût (MAD)', places=2, validators=[InputRequired(), NumberRange(min=0, max=99999999)]
    )
    notes = TextAreaField('Notes', validators=[Length(max=3000)])
    next_date = DateField('Prochaine date (facultatif)', validators=[Optional()])
    next_mileage = IntegerField(
        'Prochain kilométrage (facultatif)',
        validators=[Optional(), NumberRange(min=0, max=10000000)],
    )

    def validate_date(self, field):
        if field.data is not None and field.data > date.today():
            raise ValidationError('Une opération réalisée ne peut pas être datée dans le futur.')

    def validate_next_date(self, field):
        if self.date.data and field.data is not None and field.data <= self.date.data:
            raise ValidationError('La prochaine date doit suivre la date de l’opération.')

    def validate_next_mileage(self, field):
        if (
            self.mileage.data is not None
            and field.data is not None
            and field.data <= self.mileage.data
        ):
            raise ValidationError('La prochaine échéance doit dépasser le compteur de l’opération.')


class DeleteForm(FrenchForm):
    confirm = BooleanField(
        'Je confirme la suppression définitive.',
        validators=[InputRequired(message='Confirmez la suppression.')],
    )


class DeleteAccountForm(DeleteForm):
    password = PasswordField('Mot de passe actuel', validators=[InputRequired(), Length(max=128)])


class FAQForm(FrenchForm):
    category = SelectField(
        'Catégorie',
        choices=[
            (x, x)
            for x in [
                'vidange',
                'pneus',
                'freinage',
                'batterie',
                'filtres',
                'refroidissement',
                'voyants',
                'entretien general',
                'bruits',
                'climatisation',
                'eclairage',
                'demarches',
            ]
        ],
    )
    source = StringField(
        'Source (URL officielle ou connaissance générale du domaine)',
        default='connaissance générale du domaine',
        filters=[clean_text],
        validators=[Length(max=1000)],
    )
    question = StringField(
        'Question', filters=[clean_text], validators=[InputRequired(), Length(min=5, max=300)]
    )
    variants = TextAreaField(
        'Variantes (une par ligne)', validators=[InputRequired(), Length(max=3000)]
    )
    keywords = TextAreaField(
        'Mots-clés (un par ligne)', validators=[InputRequired(), Length(max=2000)]
    )
    answer = TextAreaField(
        'Réponse générale',
        filters=[clean_text],
        validators=[InputRequired(), Length(min=10, max=5000)],
    )
    risk_level = SelectField(
        'Niveau de risque', choices=[('faible', 'Faible'), ('modere', 'Modéré'), ('eleve', 'Élevé')]
    )
