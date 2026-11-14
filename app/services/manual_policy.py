"""Identité documentaire exacte ; la disponibilité vient des PDF locaux validés."""
import unicodedata

def identity(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold())
                   if not unicodedata.combining(c) and not c.isspace())

def canonical(brand,model,year):
    if identity(brand)!='dacia' or not isinstance(model,str) or not model.strip() or len(model)>80 or type(year) is not int or not 1900<=year<=2100:return None
    return dict(marque='Dacia',modele=' '.join(model.split()),annee=year)


def reference_key(brand,model,year):
    return identity(brand),identity(model),year

def absent_message(vehicle):
    return f"Je n'ai pas le manuel du {vehicle['marque']} {vehicle['modele']} {vehicle['annee']}."
