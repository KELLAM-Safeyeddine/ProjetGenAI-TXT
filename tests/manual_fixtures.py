"""PDF de recette entièrement fictif ; aucune donnée automobile prescriptive.

Généré à la volée dans tmp_path, jamais distribué comme un manuel constructeur.
Le flux PDF simple permet de tester pypdf sans ajouter reportlab à l'application.
"""
import json
from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject, DecodedStreamObject

PAGES = [
    'Pression des pneus\nVérifiez la pression des pneus à froid.\nVersion essence : pression fictive de recette 2,1 bar.\nVersion diesel : pression fictive de recette 2,3 bar.\nCes valeurs inventées servent uniquement au test, jamais à un véhicule réel.',
    'Batterie auxiliaire\nLa recharge de la batterie nécessite un chargeur compatible.\nCoupez le contact avant toute manipulation de la batterie.\nLe branchement du chargeur doit respecter la polarité indiquée.',
    'Huile moteur\nLe contrôle du niveau d’huile moteur se fait sur terrain horizontal.\nAttendez le refroidissement avant de vérifier le niveau d’huile.\nNe dépassez pas le repère maximal de la jauge.'
]

# Corpus de formulaires fictif, sans relation avec les PDF constructeur locaux.
TEST_MANUALS=(('Dacia','Bigster',2026),('Dacia','Duster',2026),('Dacia','Jogger',2026),
              ('Dacia','Logan',2026),('Dacia','Sandero',2021),('Dacia','Sandero',2026),
              ('Dacia','Sandero Stepway',2026),('Dacia','Spring',2026))

def write_pdf(path, pages=PAGES, identification=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'), NameObject('/Subtype'):NameObject('/Type1'),
                             NameObject('/BaseFont'):NameObject('/Helvetica'), NameObject('/Encoding'):NameObject('/WinAnsiEncoding')})
    for index,text in enumerate(pages):
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        # Lignes courtes pour garder le PDF de recette lisible en rendu.
        import textwrap
        lines = [part for line in text.splitlines() for part in textwrap.wrap(line, 85)]
        commands = ['BT /F1 11 Tf 40 790 Td 16 TL']
        for line in lines:
            escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            commands.append(f'({escaped}) Tj T*')
        commands.append('ET')
        if identification and index==0:
            label=identification.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            commands.append(f'BT /F1 9 Tf 40 16 Td ({label}) Tj ET')
        stream = DecodedStreamObject()
        stream.set_data('\n'.join(commands).encode('cp1252'))
        page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(path)

def declare(root, brand='Dacia', model='Bigster', year=2026, pages=PAGES):
    relative = f'{brand.lower()}/{model.lower()}/{year}/manuel.pdf'
    write_pdf(root / relative, pages,identification=f'{brand} {model} {year}' if any(p.strip() for p in pages) else None)
    entry = dict(marque=brand, modele=model, annee=year, chemin=relative,
                 source='equipe: document fictif généré pour les tests', date_ajout='2026-10-17')
    path = root / 'index.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'manuels':[]}
    data['manuels'].append(entry)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return entry
