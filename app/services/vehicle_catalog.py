"""Chargement strict du catalogue factuel et projection pour les formulaires."""

import json
from pathlib import Path
from urllib.parse import urlparse

CATALOG_PATH = Path(__file__).resolve().parents[2] / 'data' / 'vehicules_maroc.json'
UNKNOWN_ENGINE = 'Non documentée'
ENGINES = {'Essence', 'Diesel', 'Hybride', 'Électrique'}


def allowed_vehicles():
    """Uniquement les identités de PDF Dacia locaux validés ; aucun millésime inventé."""
    import logging

    from app.services.manual_inventory import available_entries

    try:
        entries = available_entries()
    except (ValueError, TypeError, OSError):
        logging.getLogger('autohelp.manuals').warning(
            'Inventaire indisponible : vérifier MANUALS_DIR et index.json, puis lancer flask import-manuels.'
        )
        return []
    return [dict(brand=e['marque'], model=e['modele'], year=e['annee']) for e in entries]


def allowed_public_catalog():
    from app.services.manual_access import reference_for, references

    known = references()
    return [
        dict(
            **row,
            manual_indexed=bool(reference_for(row['brand'], row['model'], row['year'], known)),
        )
        for row in allowed_vehicles()
    ]


def load_catalog(path=None):
    data = json.loads(Path(path or CATALOG_PATH).read_text(encoding='utf-8'))
    rows = data['vehicules']
    if not rows:
        raise ValueError('Le catalogue est vide.')
    seen = set()
    for row in rows:
        if (
            not isinstance(row.get('marque'), str)
            or not row['marque'].strip()
            or len(row['marque']) > 80
        ):
            raise ValueError('Marque invalide.')
        if (
            not isinstance(row.get('modele'), str)
            or not row['modele'].strip()
            or len(row['modele']) > 80
        ):
            raise ValueError('Modèle invalide.')
        if type(row.get('annee')) is not int or not 2021 <= row['annee'] <= 2026:
            raise ValueError('Année hors de la période documentée.')
        if row.get('motorisation') is not None and row['motorisation'] not in ENGINES:
            raise ValueError('Motorisation inconnue.')
        if 'manuel_indisponible' in row and type(row['manuel_indisponible']) is not bool:
            raise ValueError('manuel_indisponible doit être un booléen.')
        if (
            not isinstance(row.get('source'), list)
            or not row['source']
            or not all(
                isinstance(url, str) and urlparse(url).scheme == 'https' and urlparse(url).netloc
                for url in row['source']
            )
        ):
            raise ValueError('Chaque entrée exige une source HTTPS.')
        if not row.get('preuve_annee') or not row.get('consulte_le'):
            raise ValueError('Chaque année exige une preuve et une date de consultation.')
        key = (row['marque'], row['modele'], row['annee'], row['motorisation'])
        if key in seen:
            raise ValueError('Combinaison dupliquée dans le catalogue.')
        seen.add(key)
    return data


def catalog_rows():
    from app import db
    from app.models import VehicleCatalog

    return db.session.scalars(
        db.select(VehicleCatalog).order_by(
            VehicleCatalog.brand,
            VehicleCatalog.model,
            VehicleCatalog.year.desc(),
            VehicleCatalog.engine_type,
        )
    ).all()


def public_catalog(rows):
    from app.services.manual_access import references

    available = set(references())
    return [
        dict(
            brand=r.brand,
            model=r.model,
            year=r.year,
            engine_type=r.engine_type,
            source=r.source,
            manuel_indisponible=(r.evidence or {}).get('manuel_indisponible', True),
            manual_indexed=(r.brand, r.model, r.year) in available,
        )
        for r in rows
    ]
