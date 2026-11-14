"""Extraction géométrique : colonnes, encadrés et tableaux restent distincts.

Les snapshots servent aussi de petits extraits de recette sans distribuer le PDF.
"""

import re
import unicodedata
from collections import Counter

ARROWS = r'[🡺➥➜➔→⇒\uF0E0\uF0E8]'


def clean_text(text):
    text = unicodedata.normalize('NFC', text or '').replace('\x00', '').replace('\u2011', '-')
    text = re.sub(r'(?<=\w)[\-\u00ad]\s*\n\s*(?=\w)', '', text)
    text = text.replace('\u00ad', '')
    text = re.sub(ARROWS + r'\s*\d*', '', text)
    return '\n'.join(
        re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines() if line.strip()
    )


def versions(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    found = []
    for label, pattern in [
        ('4x2', r'4\s*[x×]\s*2'),
        ('4x4', r'4\s*[x×]\s*4'),
        ('GPL', r'\bgpl\b'),
        ('Hybrid', r'\bhybrid\w*'),
        ('Diesel', r'\bdiesel\b'),
        ('essence', r'\bessence\b'),
    ]:
        if re.search(pattern, text):
            found.append(label)
    return found


def lines_of(words):
    rows = []
    for word in sorted(words, key=lambda w: (round(w['top'], 1), w['x0'])):
        row = next((r for r in reversed(rows[-4:]) if abs(r[0]['top'] - word['top']) < 2.4), None)
        if row is None:
            rows.append([word])
        else:
            row.append(word)
    return [sorted(row, key=lambda w: w['x0']) for row in rows]


def line_text(row):
    return ' '.join(w['text'] for w in row)


def within(word, bbox):
    x = (word['x0'] + word['x1']) / 2
    y = (word['top'] + word['bottom']) / 2
    return bbox[0] - 0.5 <= x <= bbox[2] + 0.5 and bbox[1] - 0.5 <= y <= bbox[3] + 0.5


def footnote(words, height):
    text = ' '.join(
        line_text(row) for row in lines_of([w for w in words if w['top'] > height - 26])
    )
    match = re.search(r'^(\d+)\s*[-–]\s*(.+)$', text)
    if match:
        return int(match[1]), match[2].strip()
    match = re.search(r'^(.+?)\s*[-–]\s*(\d+)\s*$', text)
    if match:
        return int(match[2]), match[1].strip()
    # Anciennes notices : pagination chapitre.page (ex. 2.56), pas PDF-2.
    if re.fullmatch(r'\d{1,2}\.\d{1,3}', text):
        return text, text.split('.')[0]
    return None, ''


def snapshot_page(page, pdf_number):
    words = page.extract_words(extra_attrs=['size', 'fontname'], x_tolerance=2, y_tolerance=2)
    words = [
        {k: w[k] for k in ('text', 'x0', 'x1', 'top', 'bottom', 'size', 'fontname')}
        for w in words
        if w.get('upright', True)
    ]
    tables = []
    for table in page.find_tables():
        if len(table.rows) >= 2 and len(table.columns) >= 2:
            tables.append(
                dict(
                    bbox=list(table.bbox),
                    rows=table.extract(x_tolerance=2, y_tolerance=2),
                    cellules=[
                        [list(cell) if cell else None for cell in row.cells] for row in table.rows
                    ],
                    colonnes=[[column.bbox[0], column.bbox[2]] for column in table.columns],
                )
            )
    boxes = []
    for shape in [*page.rects, *page.curves]:
        color = shape.get('non_stroking_color')
        if isinstance(color, (float, int)):
            color = [color]
        if not isinstance(color, (list, tuple)) or not color:
            continue
        grey = max(color) - min(color) < 0.02 and 0.7 < float(color[0]) < 0.98
        if grey and 60 < shape['width'] < page.width * 0.65 and shape['height'] > 25:
            boxes.append([shape[k] for k in ('x0', 'top', 'x1', 'bottom')])
    return dict(
        page_pdf=pdf_number,
        width=page.width,
        height=page.height,
        words=words,
        tables=tables,
        boxes=boxes,
    )


def remove_arrows(words):
    """Les chiffres d'un renvoi sortent du texte mais restent dans les métadonnées."""
    removed = set()
    references = []
    for i, word in enumerate(words):
        if not re.search(ARROWS, word['text']):
            continue
        number = re.search(r'\d+', word['text'])
        if number:
            references.append(int(number[0]))
        else:
            near = [
                (abs(w['x0'] - word['x0']) + abs(w['top'] - word['top']), j, w)
                for j, w in enumerate(words)
                if re.fullmatch(r'\d+', w['text'])
                and abs(w['top'] - word['top']) < 12
                and abs(w['x0'] - word['x0']) < 42
            ]
            if near:
                _, j, w = min(near)
                references.append(int(w['text']))
                removed.add(j)
        removed.add(i)
    return [w for i, w in enumerate(words) if i not in removed], sorted(set(references))


def column_bounds(words, width):
    """Ne coupe pas une ligne qui traverse un séparateur : repli pleine largeur."""
    if not words:
        return [(20, width - 20)]

    # Un espace ordinaire entre deux mots n'est pas une gouttière de colonne.
    # Exiger une bande blanche d'au moins huit points sur toute sa hauteur.
    def crosses(cut):
        return sum(w['x0'] < cut + 4 and cut - 4 < w['x1'] for w in words)

    cuts = []
    for target in (width / 3, 2 * width / 3):
        cut = min(
            range(round(target) - 9, round(target) + 10),
            key=lambda x: (crosses(x), abs(x - target)),
        )
        if crosses(cut) == 0:
            cuts.append(cut)
    if len(cuts) == 2:
        return list(zip([20, *cuts], [*cuts, width - 20]))
    middle = min(
        range(round(width / 2) - 9, round(width / 2) + 10),
        key=lambda x: (crosses(x), abs(x - width / 2)),
    )
    if crosses(middle) == 0:
        return [(20, middle), (middle, width - 20)]
    return [(20, width - 20)]


def heading(row):
    text = line_text(row)
    letters = ''.join(c for c in text if c.isalpha())
    bold = sum(len(w['text']) for w in row if 'Bold' in w.get('fontname', ''))
    return (
        len(text) < 110
        and len(letters) > 3
        and not re.match(r'^[-–•]', text)
        and not re.search(r'[.!?;]$', text)
        and (letters.isupper() or bold > len(text) * 0.65)
    )


def table_text(rows, cellules=None, colonnes=None):
    def cell_text(cell):
        cell = re.sub(r'\b\d+\.?\s*' + ARROWS, '', cell or '')
        return re.sub(r'\s+', ' ', clean_text(cell)).strip()

    normalized = [[cell_text(cell) for cell in row] for row in rows]
    if not normalized:
        return '', []
    # Répéter une cellule commune uniquement si sa boîte couvre géométriquement
    # les colonnes voisines ; un simple None n'autorise pas une valeur devinée.
    if cellules and colonnes:
        for i, row in enumerate(cellules):
            for j, bbox in enumerate(row):
                if bbox is None or not normalized[i][j]:
                    continue
                for k in range(j + 1, len(row)):
                    if row[k] is None and bbox[2] >= colonnes[k][1] - 0.5:
                        normalized[i][k] = normalized[i][j] + ' (cellule commune)'
                    else:
                        break
    # Remplir les cellules fusionnées seulement dans les en-têtes ; conserver la
    # matrice d'origine, afin qu'un vide ne soit pas interprété comme une valeur.
    headers = (
        [] if len(normalized[0]) == 2 and re.fullmatch('[A-Z]', normalized[0][0]) else normalized[0]
    )
    text = '\n'.join(
        ' | '.join(cell or '(cellule fusionnée ou vide)' for cell in row) for row in normalized
    )
    return text, headers


def page_blocks(snapshot, *, offset=None, bigster=False):
    words = snapshot['words']
    width = snapshot['width']
    height = snapshot['height']
    warnings = []
    printed, chapter = footnote(words, height)
    origin = 'pied_de_page' if printed is not None else 'non_identifiee'
    if printed is None and offset is not None and snapshot['page_pdf'] > offset:
        printed = snapshot['page_pdf'] - offset
        origin = 'decalage_verifie'
    headers = [
        line_text(row)
        for row in lines_of([w for w in words if w['top'] < 31 and w['x0'] > 20])
        if sum(w.get('size', 0) for w in row) / len(row) >= 10
    ]
    parent = clean_text(' '.join(headers)) or chapter or 'Section non identifiée'
    body = [
        w
        for w in words
        if w['top'] >= 31 and w['bottom'] < height - 25 and 22 < w['x0'] < width - 20
    ]
    if sum(c.isalnum() for w in body for c in w['text']) < 40:
        return [], [
            f'page PDF {snapshot["page_pdf"]} quasi vide ou sans texte (<40 caractères utiles), non indexée.'
        ]
    if sum(w['text'].count('\ufffd') for w in body) > max(
        2, sum(len(w['text']) for w in body) * 0.02
    ):
        return [], [
            f'page PDF {snapshot["page_pdf"]} à vérifier visuellement : texte illisible, non indexé.'
        ]
    blocks = []
    occupied = []

    def add(content, bbox, kind, section=None, refs=None, extra=None):
        text = clean_text(content)
        if sum(c.isalnum() for c in text) < 15:
            return
        metadata = dict(
            page_pdf=snapshot['page_pdf'],
            page_imprimee=printed,
            pagination_origine=origin,
            chapitre=chapter or parent,
            section_parent=parent,
            type_bloc=kind,
            bbox=[round(v, 2) for v in bbox],
            renvois=refs or [],
            versions=versions(text),
            methode_extraction='pdfplumber_colonnes',
        )
        metadata.update(extra or {})
        blocks.append(dict(section=clean_text(section or parent), contenu=text, metadata=metadata))

    for table in snapshot.get('tables', []):
        bbox = table['bbox']
        # Les modèles vierges de justificatifs ne sont pas des consignes d'entretien.
        if 'JUSTIFICATIFS' in parent or 'ANTICORROSION' in parent:
            occupied.append(bbox)
            continue
        table_words = [w for w in body if within(w, bbox)]
        _, refs = remove_arrows(table_words)
        text, headers_row = table_text(table['rows'], table.get('cellules'), table.get('colonnes'))
        nonempty = sum(bool(c and c.strip()) for row in table['rows'] for c in row)
        if nonempty < 4 or '\ufffd' in text:
            warnings.append(
                f'page PDF {snapshot["page_pdf"]} à vérifier visuellement : tableau incomplet, non indexé.'
            )
        else:
            above = [
                row
                for row in lines_of(body)
                if bbox[1] - 55 < row[0]['top'] < bbox[1] and heading(row)
            ]
            caption = line_text(above[-1]) if above else parent
            add(text, bbox, 'tableau', caption, refs, extra=dict(entetes_tableau=headers_row))
        occupied.append(bbox)
    for bbox in snapshot.get('boxes', []):
        if any(
            within({'x0': bbox[0], 'x1': bbox[2], 'top': bbox[1], 'bottom': bbox[3]}, other)
            for other in occupied
        ):
            continue
        selected = [w for w in body if within(w, bbox)]
        selected, refs = remove_arrows(selected)
        if not selected:
            continue
        rows = lines_of(selected)
        title = next((line_text(row) for row in rows if heading(row)), parent)
        add('\n'.join(line_text(row) for row in rows), bbox, 'avertissement', title, refs)
        occupied.append(bbox)
    remainder = [w for w in body if not any(within(w, bbox) for bbox in occupied)]
    bounds = column_bounds(remainder, width)
    for left, right in bounds:
        selected = [w for w in remainder if left <= (w['x0'] + w['x1']) / 2 < right]
        selected, refs = remove_arrows(selected)
        rows = lines_of(selected)
        section = parent
        current = []

        def flush():
            if not current:
                return
            text = '\n'.join(line_text(row) for row in current)
            bbox = [
                min(w['x0'] for row in current for w in row),
                current[0][0]['top'],
                max(w['x1'] for row in current for w in row),
                max(w['bottom'] for row in current for w in row),
            ]
            kind = (
                'liste'
                if any(re.match(r'^[-–•]', line_text(row)) for row in current)
                else 'avertissement'
                if re.search(
                    r'\b(attention|danger|avertissement|risque de|ne jamais)\b', text.casefold()
                )
                else 'texte'
            )
            add(text, bbox, kind, section, refs)

        for row in rows:
            text = line_text(row)
            if re.fullmatch(r'[\d\W]+', text):
                continue
            candidate = heading(row) or (
                not current
                and parent == 'Section non identifiée'
                and len(text) < 80
                and not re.search(r'[.!?;:]$', text)
            )
            boundary = (
                not current
                or re.search(r'[.!?;:]$', line_text(current[-1]))
                or row[0]['top'] - max(w['bottom'] for w in current[-1]) > 4
            )
            if candidate and boundary:
                flush()
                current = []
                section = text
            current.append(row)
        flush()
    blocks.sort(
        key=lambda b: (int(b['metadata']['bbox'][0] / (width / 3)), b['metadata']['bbox'][1])
    )
    # Un tableau sous forme d'image ou sans grille ne doit pas être transformé en
    # prescriptions : signaler les pages sensibles dont le tableau n'est pas reconnu.
    sensitive = unicodedata.normalize('NFKD', parent).encode('ascii', 'ignore').decode().lower()
    body_text = ' '.join(w['text'] for w in body).casefold()
    if not snapshot.get('tables') and (
        re.search(r'fusibles|caracteristiques|pressions? de gonflage', sensitive)
        or ('pneumatique' in sensitive and re.search(r'etiquette|étiquette|pression', body_text))
    ):
        warnings.append(
            f'page PDF {snapshot["page_pdf"]} à vérifier visuellement : tableau/étiquette possible sans grille textuelle reconnue.'
        )
    if any('à vérifier visuellement' in warning for warning in warnings):
        for block in blocks:
            block['metadata']['controle_visuel_requis'] = True
    return blocks, warnings


def detected_offset(pdf):
    offsets = []
    for i in [*range(min(8, len(pdf.pages))), *range(max(8, len(pdf.pages) - 4), len(pdf.pages))]:
        p = pdf.pages[i]
        try:
            printed, _ = footnote(p.extract_words(), p.height)
            if type(printed) is int:
                offsets.append(i + 1 - printed)
        finally:
            p.close()
    if offsets:
        value, count = Counter(offsets).most_common(1)[0]
        if count >= 3 and count / len(offsets) >= 0.7:
            return value
    return None
