"""Extraction des PDF locaux identifiés, sans réseau ni OCR."""

from pathlib import Path

from pypdf import PdfReader

from app.services.chatbot_service import normalize


def load_index(root):
    from app.services.manual_inventory import scan_manuals

    root = Path(root).resolve()
    inventory = scan_manuals(root)
    entries = [
        {**row['entry'], 'path': root / row['chemin']}
        for row in inventory
        if row['statut'] == 'valide'
    ]
    notices = [
        f'PDF rejeté : {row["chemin"]} — {row["raison"]}'
        for row in inventory
        if row['statut'] != 'valide'
    ]
    if not inventory:
        notices.append('Aucun PDF local trouvé ; aucun manuel disponible.')
    return entries, notices


def chunk_text(text, size=700, overlap=80):
    """Découpe aux espaces ; chevauchement local, jamais entre deux pages/sections."""
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(' ', start + size // 2, end)
            if boundary > start:
                end = boundary
        yield text[start:end].strip()
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
        while start < end and not text[start - 1].isspace():
            start += 1


def extract_manual(entry, *, page_numbers=None):
    """PDF texte uniquement ; colonnes et blocs atomiques, sans OCR ni réseau."""
    import pdfplumber

    from app.services.manual_extraction import detected_offset, page_blocks, snapshot_page

    passages, warnings = [], []
    verified = entry.get('passages_verifies', [])
    from hashlib import sha256

    from app.services.manual_inventory import file_hash

    digest = file_hash(entry['path']) if verified else None
    reader = PdfReader(entry['path'])
    if reader.is_encrypted:
        raise ValueError('PDF chiffré : fournir une copie lisible autorisée.')
    with pdfplumber.open(entry['path']) as pdf:
        bigster = 'NU 1626-3 R1310' in str(pdf.metadata.get('Title', ''))
        offset = detected_offset(pdf)
        if offset is None:
            offset = entry.get('pagination_offset')
        warnings.append(
            f'Méthode : pdfplumber, colonnes/encadrés/tableaux ; décalage de pagination détecté : {offset}.'
        )
        for index, page in enumerate(pdf.pages, 1):
            if page_numbers is not None and index not in page_numbers:
                continue
            try:
                blocks, notices = page_blocks(
                    snapshot_page(page, index), offset=offset, bigster=bigster
                )
                warnings.extend(notices)
                position = 0
                for block in blocks:
                    metadata = {
                        key: entry[key]
                        for key in ('langue', 'url_pdf', 'periode', 'marche_document', 'sha256')
                        if key in entry
                    }
                    metadata.update(block['metadata'])
                    text = block['contenu']
                    # Ne lever une réserve que sur un bloc revu visuellement, lié
                    # au PDF et au texte exacts. Les autres blocs restent bloqués.
                    checked = next(
                        (
                            v
                            for v in verified
                            if isinstance(v, dict)
                            and v.get('sha256_pdf') == digest
                            and v.get('page_pdf') == index
                            and v.get('sha256_bloc') == sha256(text.encode('utf-8')).hexdigest()
                            and v.get('date_verification')
                        ),
                        None,
                    )
                    if checked and metadata.get('controle_visuel_requis'):
                        metadata['controle_visuel_requis'] = False
                        metadata['verification_visuelle'] = checked
                    parts = [text] if metadata['type_bloc'] != 'texte' else chunk_text(text)
                    for part in parts:
                        passages.append(
                            dict(
                                brand=entry['marque'],
                                model=entry['modele'],
                                year=entry['annee'],
                                page=index,
                                position=position,
                                section=block['section'],
                                contenu=part,
                                search_index=normalize(part),
                                source=entry['source'],
                                added_at=entry['date_ajout'],
                                document_metadata=metadata,
                            )
                        )
                        position += 1
            except Exception as error:
                warnings.append(
                    f'page PDF {index} à vérifier visuellement : extraction impossible ({type(error).__name__}), non indexée.'
                )
            finally:
                page.close()
    if not passages:
        warnings.append('PDF sans texte indexable ; aucun passage importé.')
    return passages, warnings
