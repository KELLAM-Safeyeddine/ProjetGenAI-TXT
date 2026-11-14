"""Schémas historiques conservés : aucune table ni donnée supprimée."""

from app import db


class VehicleCatalog(db.Model):
    """Combinaisons documentées au Maroc ; indépendant des véhicules personnels."""

    __tablename__ = 'vehicle_catalog'
    __table_args__ = (
        db.UniqueConstraint(
            'brand', 'model', 'year', 'engine_type', name='uq_vehicle_catalog_combination'
        ),
        db.CheckConstraint('year >= 2021 AND year <= 2026', name='catalog_year_range'),
    )
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(80), nullable=False, index=True)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    engine_type = db.Column(db.String(40), nullable=False)
    source = db.Column(db.JSON, nullable=False)
    evidence = db.Column(db.JSON, nullable=False)


class FAQ(db.Model):
    __tablename__ = 'faq'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False)
    question = db.Column(db.String(300), nullable=False, unique=True)
    variants = db.Column(db.JSON, nullable=False, default=list)
    keywords = db.Column(db.JSON, nullable=False, default=list)
    answer = db.Column(db.Text, nullable=False)
    risk_level = db.Column(db.String(16), nullable=False)
    slug = db.Column(db.String(100), nullable=True, unique=True)
    source = db.Column(db.String(1000), nullable=True)
    seed_hash = db.Column(db.String(64), nullable=True)

    def as_entry(self):
        return dict(
            id=self.id,
            categorie=self.category,
            question=self.question,
            variantes=self.variants,
            mots_cles=self.keywords,
            reponse=self.answer,
            niveau_risque=self.risk_level,
            slug=self.slug,
            source=self.source or 'connaissance générale du domaine',
        )


class WebPassage(db.Model):
    __tablename__ = 'web_passages'
    __table_args__ = (db.UniqueConstraint('url', 'position', name='uq_web_passage'),)
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1500), nullable=False)
    site_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    consulted_at = db.Column(db.String(25), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(30), nullable=False)
    kind = db.Column(db.String(30), nullable=False)

    def as_passage(self):
        return {
            key: getattr(self, key)
            for key in (
                'url',
                'site_name',
                'title',
                'consulted_at',
                'position',
                'content',
                'region',
                'kind',
            )
        }
