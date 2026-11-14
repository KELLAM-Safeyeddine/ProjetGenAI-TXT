"""Évaluation sur annotations indépendantes ; les brouillons ne donnent aucun score."""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.services.answer_service import answer
from app.services.document_tools import DocumentTools
from app.services.manual_policy import canonical, reference_key

NUMBER = r'\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?'
UNIT = (
    r'km\s*/\s*h|kmh|tr\s*/\s*(?:min|mn)|'
    r'millimetres?|mm|minutes?|min|bars?|kpa|n\s*[.·]?\s*m|'
    r'litres?|l|kilometres?|km|mois|ans?|volts?|v|°\s*c'
)
MEASUREMENT = re.compile(rf'(?<![\w.,])({NUMBER})\s*({UNIT})(?!\w)', re.I)
RANGE = re.compile(rf'(?<![\w.,])({NUMBER})\s*(?:a|et|–|—|-)\s*({NUMBER})\s*({UNIT})(?!\w)', re.I)


def measurements(text):
    """Unités explicites uniquement ; aucune déduction de valeur ou conversion."""
    text = ''.join(
        c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c)
    )

    def item(number, unit):
        value = Decimal(re.sub(r'\s', '', number).replace(',', '.'))
        unit = re.sub(r'\s', '', unit)
        if unit in ('km/h', 'kmh'):
            unit = 'km/h'
        elif unit.startswith('tr/'):
            unit = 'tr/min'
        elif unit in ('mm', 'millimetre', 'millimetres'):
            unit = 'mm'
        elif unit in ('min', 'minute', 'minutes'):
            unit = 'min'
        elif unit in ('l', 'litre', 'litres'):
            unit = 'l'
        elif unit in ('km', 'kilometre', 'kilometres'):
            unit = 'km'
        elif unit in ('v', 'volt', 'volts'):
            unit = 'v'
        elif unit in ('n.m', 'n·m', 'nm'):
            unit = 'nm'
        elif unit in ('an', 'ans'):
            unit = 'an'
        elif unit in ('bar', 'bars'):
            unit = 'bar'
        return value, unit

    found = {item(*match.groups()) for match in MEASUREMENT.finditer(text)}
    for match in RANGE.finditer(text):
        low, high, unit = match.groups()
        found.update((item(low, unit), item(high, unit)))
    return found


def numeric_accuracy(body, expected):
    """Proxy strict : valeurs annotées présentes, sans autre valeur technique."""
    annotated = [measurements(value) for value in expected]
    if any(not values for values in annotated):
        return False
    allowed = set().union(*annotated)
    return measurements(body) == allowed


def human_reviewed(case):
    review = (case.get('verification') or {}).get('revue_humaine') or {}
    return bool(review.get('par') and review.get('date') and review.get('methode'))


def load_cases(path):
    cases = json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(cases, list):
        raise ValueError('Le jeu doit contenir une liste de cas.')
    seen = set()
    for case in cases:
        identity = canonical(
            case['vehicule']['marque'], case['vehicule']['modele'], case['vehicule']['annee']
        )
        if (
            not identity
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', case.get('id', ''))
            or case['id'] in seen
        ):
            raise ValueError('Identité ou identifiant de cas invalide/dupliqué.')
        if not isinstance(case.get('question'), str) or not 1 <= len(case['question']) <= 1000:
            raise ValueError('Question invalide.')
        if type(case.get('valide')) is not bool:
            raise ValueError('Le statut valide doit être explicite.')
        if case['valide']:
            proof = case.get('verification') or {}
            date.fromisoformat(proof['date'])
            if (
                not proof.get('par')
                or not proof.get('methode')
                or not re.fullmatch('[0-9a-f]{64}', case.get('sha256_pdf', ''))
            ):
                raise ValueError('Annotation vérifiée sans provenance/empreinte.')
            review = proof.get('revue_humaine')
            if review is not None:
                if not isinstance(review, dict) or not human_reviewed(case):
                    raise ValueError(
                        'La revue humaine doit identifier sa date, son auteur et sa méthode.'
                    )
                date.fromisoformat(review['date'])
            expected = case['attendu']
            if expected['type'] not in ('reponse', 'sans_information'):
                raise ValueError('Comportement attendu invalide.')
            pages = expected.get('pages_pdf')
            if not isinstance(pages, list) or any(type(p) is not int or p < 1 for p in pages):
                raise ValueError('Les pages attendues doivent être des numéros PDF positifs.')
            if expected['type'] == 'reponse' and (not pages or not expected.get('reponse')):
                raise ValueError(
                    'Une réponse attendue doit fournir une réponse et une page vérifiées.'
                )
            if expected['type'] == 'sans_information' and pages:
                raise ValueError('Une absence d’information ne doit pas inventer de page source.')
            values = expected.get('valeurs')
            if values is not None and (
                not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values)
            ):
                raise ValueError('Valeurs attendues invalides.')
        seen.add(case['id'])
    return cases


def evaluate_case(case, rows, *, generate=False, config=None, transport=None):
    if not case['valide']:
        return {'id': case['id'], 'statut': 'a_annoter'}
    ref = canonical(
        case['vehicule']['marque'], case['vehicule']['modele'], case['vehicule']['annee']
    )
    own = [
        r
        for r in rows
        if r.get('active', True)
        and reference_key(r['brand'], r['model'], r['year']) == reference_key(*ref.values())
    ]
    if not own or any(r.get('sha256') != case['sha256_pdf'] for r in own):
        return {'id': case['id'], 'statut': 'index_absent_ou_edition_differente'}
    vehicle = {**ref, 'motorisation': case['vehicule'].get('motorisation'), 'manual_reference': ref}
    tools = DocumentTools(vehicle, ref, lambda: own)
    tools.bind_query(case['question'])
    passages = tools.dispatch('rechercher_manuel', {'requete': case['question']})['passages']
    expected = case['attendu']
    pages = [p['page_pdf'] for p in passages]
    hit = (
        bool(set(pages) & set(expected.get('pages_pdf', [])))
        if expected['type'] == 'reponse'
        else None
    )
    result = {
        'id': case['id'],
        'statut': 'evalue',
        'pages_trouvees': pages,
        'rappel_top3': hit,
        'absence_recherche': not pages if expected['type'] == 'sans_information' else None,
        'citation_correcte': None,
        'valeurs_correctes': None,
        'refus_correct': None,
    }
    if generate:
        response = answer(
            case['question'],
            vehicle=vehicle,
            manual_loader=lambda: own,
            config=config,
            transport=transport,
        )
        refs = response['references']
        if expected['type'] == 'reponse':
            result['citation_correcte'] = (
                bool(refs)
                and any(r.get('page_pdf') in expected.get('pages_pdf', []) for r in refs)
                and all(
                    reference_key(r.get('marque'), r.get('modele'), r.get('annee'))
                    == reference_key(*ref.values())
                    for r in refs
                )
            )
        body = response['reply'].split('\nSource :')[0]
        values = expected.get('valeurs')
        if values is not None:
            result['valeurs_correctes'] = response['source'] == 'manuel' and numeric_accuracy(
                body, values
            )
        if expected['type'] == 'sans_information':
            result['refus_correct'] = not refs and response['status'] in (
                'orientation',
                'manuel_absent',
            )
        result['comportement'] = response['status']
    return result


def evaluate(cases, loader, *, generate=False, config=None, transport=None, limit=10):
    groups = defaultdict(list)
    results = []
    generation_count = 0
    for case in cases:
        key = reference_key(
            case['vehicule']['marque'], case['vehicule']['modele'], case['vehicule']['annee']
        )
        groups[key].append(case)
        run_model = generate and case['valide'] and generation_count < limit
        rows = loader(case['vehicule']) if case['valide'] else []
        results.append(
            evaluate_case(case, rows, generate=run_model, config=config, transport=transport)
        )
        generation_count += int(run_model)
    return results, groups


def write_report(path, results, groups, corpus_sha256=None):
    counts = Counter(r['statut'] for r in results)
    lines = [
        '# Évaluation des manuels réels',
        '',
        'Date : ' + date.today().isoformat(),
        '',
        'Empreinte SHA-256 du jeu : ' + (corpus_sha256 or 'non fournie'),
        '',
        'Seules les annotations relues et liées à une empreinte PDF sont mesurées. Une annotation assistée ne vaut pas validation humaine. Les cas à annoter sont exclus des scores. Aucun texte extrait ni clé n’est copié dans ce rapport.',
        '',
        f'Cas : {len(results)} ; évalués : {counts["evalue"]} ; à annoter : {counts["a_annoter"]} ; index/édition indisponible : {counts["index_absent_ou_edition_differente"]}.',
        '',
        '| Véhicule | Cas | Annotations relues | Revues humaines | Rappel top 3 (réponses présentes) | Absence de passage (cas sans information) |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    by_id = {r['id']: r for r in results}
    ready = bool(groups)
    for key, cases in groups.items():
        measured = [by_id[c['id']] for c in cases if by_id[c['id']]['statut'] == 'evalue']
        verified = sum(c['valide'] for c in cases)
        reviewed = sum(c['valide'] and human_reviewed(c) for c in cases)
        ready &= verified >= 50 and reviewed == verified and len(measured) == verified
        hits = [r['rappel_top3'] for r in measured if r['rappel_top3'] is not None]
        absent = [
            r['absence_recherche'] for r in measured if r.get('absence_recherche') is not None
        ]
        ratio = f'{sum(hits)}/{len(hits)}' if hits else 'non mesuré'
        absence_ratio = f'{sum(absent)}/{len(absent)}' if absent else 'non mesuré'
        ref = cases[0]['vehicule']
        lines.append(
            f'| {ref["marque"]} {ref["modele"]} {ref["annee"]} | {len(cases)} | {verified} | {reviewed} | {ratio} | {absence_ratio} |'
        )
    lines += ['', '## Génération (uniquement si demandée)', '']
    for metric in ('citation_correcte', 'valeurs_correctes', 'refus_correct'):
        applicable = [r[metric] for r in results if r.get(metric) is not None]
        lines.append(
            f'- {metric} : '
            + (f'{sum(applicable)}/{len(applicable)}' if applicable else 'non mesuré')
        )
    lines += [
        '',
        '**Corpus prêt pour comparaison : '
        + (
            'oui'
            if ready
            else 'non — au moins cinquante annotations par manuel, vérifiées par une revue humaine, sont requises'
        )
        + '.**',
        '',
        'Les recouvrements lexicaux de valeurs et les citations sont des indicateurs, pas un jugement sémantique professionnel. Aucun score global de qualité LLM n’est déduit de la recherche.',
        '',
        '| Cas | Statut | Pages retrouvées | Rappel top 3 |',
        '| --- | --- | --- | --- |',
    ]
    lines.extend(
        f'| {r["id"]} | {r["statut"]} | {r.get("pages_trouvees", [])} | {r.get("rappel_top3", "—")} |'
        for r in results
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(lines) + '\n', encoding='utf8')
    return ready
