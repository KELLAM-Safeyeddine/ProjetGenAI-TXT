"""Liaison canonique sans modifier la graphie saisie."""
from app import db
from app.models import ManuelPassage
from app.services.manual_policy import identity,canonical,reference_key

def references():
    from app.services.vehicle_catalog import allowed_vehicles
    allowed={reference_key(r['brand'],r['model'],r['year']) for r in allowed_vehicles()}
    return [row for row in db.session.execute(db.select(ManuelPassage.brand,ManuelPassage.model,ManuelPassage.year).where(ManuelPassage.active.is_(True)).distinct()).all() if reference_key(*row) in allowed]

def reference_for(brand,model,year,known=None):
    if not canonical(brand,model,year):return None
    matches=[dict(marque=b,modele=m,annee=y) for b,m,y in (references() if known is None else known) if (identity(b),identity(m),y)==(identity(brand),identity(model),year)]
    return matches[0] if len(matches)==1 else None

def link_manual(vehicle,known=None):
    vehicle.manual_reference=reference_for(vehicle.brand,vehicle.model,vehicle.year,known)
    return vehicle.manual_reference

def query_for(vehicle):
    ref=reference_for(vehicle.brand,vehicle.model,vehicle.year)
    if not ref:return db.select(ManuelPassage).where(db.false())
    return db.select(ManuelPassage).where(ManuelPassage.active.is_(True),ManuelPassage.brand==ref['marque'],ManuelPassage.model==ref['modele'],ManuelPassage.year==ref['annee']).order_by(ManuelPassage.page,ManuelPassage.position)
