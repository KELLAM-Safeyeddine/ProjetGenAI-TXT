"""Suggestions issues des marqueurs de l'édition exacte, sans déduire une version."""

from collections import defaultdict

from app import db
from app.models import ManuelPassage
from app.services.manual_policy import reference_key

LABELS = {
    '4x2': '4x2',
    '4x4': '4x4',
    'GPL': 'GPL',
    'Hybrid': 'Hybride',
    'Diesel': 'Diesel',
    'essence': 'Essence',
}


def by_vehicle():
    choices = defaultdict(set)
    for brand, model, year, metadata in db.session.execute(
        db.select(
            ManuelPassage.brand,
            ManuelPassage.model,
            ManuelPassage.year,
            ManuelPassage.document_metadata,
        ).where(ManuelPassage.active.is_(True))
    ):
        choices[reference_key(brand, model, year)].update(
            v for v in (metadata or {}).get('versions', []) if v in LABELS
        )
    return {key: sorted(values) for key, values in choices.items()}
