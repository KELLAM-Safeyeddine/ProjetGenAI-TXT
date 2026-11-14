"""Évaluation sur annotations indépendantes ; les brouillons ne donnent aucun score."""

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from app.services.answer_service import answer
from app.services.chatbot_service import normalize
from app.services.document_tools import DocumentTools
from app.services.manual_policy import canonical, reference_key


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
        else not pages
    )
    result = {
        'id': case['id'],
        'statut': 'evalue',
        'pages_trouvees': pages,
        'rappel_top3': hit,
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
            observed = re.findall(
                r'(?<!\w)\d+(?:[ \u00a0]\d{3})*(?:[.,]\d+)?\s*(?:bar|kpa|nm|litres?|l|km|mois|ans|v|°c)\b',
                body,
                re.I,
            )
            allowed = {normalize(v) for v in values}
            result['valeurs_correctes'] = (
                response['source'] == 'manuel'
                and all(normalize(v) in normalize(body) for v in values)
                and all(normalize(v) in allowed for v in observed)
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


def write_report(path, results, groups):
    counts = Counter(r['statut'] for r in results)
    lines = [
        '# Évaluation des manuels réels',
        '',
        'Date : ' + date.today().isoformat(),
        '',
        'Seules les annotations vérifiées et liées à une empreinte PDF sont mesurées. Les cas à annoter sont exclus des scores. Aucun texte extrait ni clé n’est copié dans ce rapport.',
        '',
        f'Cas : {len(results)} ; évalués : {counts["evalue"]} ; à annoter : {counts["a_annoter"]} ; index/édition indisponible : {counts["index_absent_ou_edition_differente"]}.',
        '',
        '| Véhicule | Cas | Annotations vérifiées | Rappel top 3 |',
        '| --- | ---: | ---: | ---: |',
    ]
    by_id = {r['id']: r for r in results}
    ready = bool(groups)
    for key, cases in groups.items():
        measured = [by_id[c['id']] for c in cases if by_id[c['id']]['statut'] == 'evalue']
        verified = sum(c['valide'] for c in cases)
        ready &= verified >= 50 and len(measured) == verified
        ratio = (
            f'{sum(r["rappel_top3"] for r in measured)}/{len(measured)}'
            if measured
            else 'non mesuré'
        )
        ref = cases[0]['vehicule']
        lines.append(
            f'| {ref["marque"]} {ref["modele"]} {ref["annee"]} | {len(cases)} | {verified} | {ratio} |'
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
            else 'non — au moins cinquante annotations vérifiées par manuel sont requises'
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
