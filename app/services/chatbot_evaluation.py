"""Recette reproductible, sans réseau et sans PDF constructeur : attentes figées."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.answer_service import answer
from app.services.chatbot_service import THRESHOLD

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / 'tests/data/questions_test.json'


def fixture_passages():
    fixture = json.loads((ROOT / 'tests/data/manuel_evaluation.json').read_text(encoding='utf-8'))
    return [
        dict(
            brand='Dacia',
            model='Bigster',
            year=2026,
            page=i,
            position=0,
            section=page.splitlines()[0],
            contenu=page,
            source='equipe: manuel fictif de recette, sans valeur automobile réelle',
            langue='fr',
        )
        for i, page in enumerate(fixture['pages'], 1)
    ]


def evaluate(entries=None, threshold=THRESHOLD, cases=None, *, config=None, transport=None):
    from app.services.evaluation_model import CONFIG, FakeModel

    cases = cases if cases is not None else json.loads(QUESTIONS.read_text(encoding='utf-8'))
    results = []
    for case in cases:
        context = case['contexte']
        vehicle = (
            dict(
                marque='Dacia',
                modele='Bigster',
                annee=2026,
                motorisation='Diesel',
                manual_reference=dict(marque='Dacia', modele='Bigster', annee=2026)
                if context == 'manuel_indexe'
                else None,
            )
            if context != 'sans_vehicule'
            else None
        )
        model = transport or FakeModel()
        result = answer(
            case['message'],
            vehicle=vehicle,
            manual_loader=fixture_passages,
            config=CONFIG if config is None else config,
            transport=model,
        )
        got = 'manuel' if result['source'] == 'manuel' else result['status']
        reasons = []
        if got != case['attendu']:
            reasons.append('comportement attendu : ' + case['attendu'])
        if case.get('faq_attendue') and result.get('faq_id') not in case['faq_attendue']:
            reasons.append('fiche FAQ attendue : ' + ', '.join(case['faq_attendue']))
        if got == 'generale':
            from app.services.answer_service import has_forbidden_label
            from app.services.general_faq_service import MECHANIC_END

            if (
                result['source'] != 'faq'
                or not result['reply'].endswith(MECHANIC_END)
                or has_forbidden_label(result['reply'])
            ):
                reasons.append('format FAQ non conforme')
            if len(result['reply'].split()) < 150 or result['source_line']:
                reasons.append('réponse FAQ trop courte ou source affichée hors format')
        if got == 'generale' and any(
            set(ref) & {'page', 'page_pdf', 'page_imprimee', 'marque', 'modele', 'annee'}
            for ref in result['references']
        ):
            reasons.append('référence spécifique interdite sans véhicule')
        if (
            case.get('page_attendue')
            and got == 'manuel'
            and not any(r['page'] == case['page_attendue'] for r in result['references'])
        ):
            reasons.append('page attendue : ' + str(case['page_attendue']))
        if got == 'manuel' and (
            not result['source_line'] or not result['reply'].endswith(result['source_line'])
        ):
            reasons.append('source finale manquante')
        if got == 'orientation' and result['source_line']:
            reasons.append('référence inventée lors du repli')
        results.append(
            dict(
                case=case,
                correct=not reasons,
                reasons=reasons,
                result=result,
                got=got,
                calls=len(getattr(model, 'requests', [])),
            )
        )
    return results


def calibrate(entries=None):
    return None


def write_report(results, path, *, faq_origin=None, calibration=None):
    passed = sum(r['correct'] for r in results)
    total = len(results)
    lines = [
        '# Évaluation conversationnelle AutoHELP',
        '',
        f'Date UTC : {datetime.now(timezone.utc).isoformat()}',
        f'SHA-256 du jeu : `{hashlib.sha256(QUESTIONS.read_bytes()).hexdigest()}`.',
        '',
        f'**{passed}/{total} = {passed / total:.1%} de comportements conformes.**',
        '',
        'Sans véhicule : quarante fiches de FAQ générale locale, recherche TF-IDF/synonymes existante. Avec véhicule : modèle factice simulant les outils sur quatre pages de manuel fictif. Aucun réseau, coût API ou corpus web. Les formulations, identifiants, catégories et contextes des 78 questions sont inchangés. Les attentes antérieures sont archivées dans attendu_avant_faq_generale. Une fiche attendue est vérifiée lorsque le sujet est couvert ; les sujets précis absents doivent produire un repli honnête. Le taux mesure ces comportements et références, pas la qualité d’un vrai modèle ni la couverture des manuels réels.',
        '',
        '## Questions avec manuel sans passage exploitable',
        '',
    ]
    lines += [
        f'- {r["case"]["id"]} : {r["case"]["message"]}'
        for r in results
        if r['got'] == 'orientation'
    ] or ['Aucune.']
    lines += ['', '## Échecs restants', '']
    lines += [
        f'- {r["case"]["id"]} : {r["case"]["message"]} — {" ; ".join(r["reasons"])}. Obtenu : {r["got"]}.'
        for r in results
        if not r['correct']
    ] or ['Aucun.']
    lines += [
        '',
        '## Détail des appels et sources',
        '',
        '| ID | Attendu | Obtenu | Score FAQ | Fiche | Appels modèle simulés | Références | Résultat |',
        '| --- | --- | --- | ---: | --- | ---: | --- | --- |',
    ]
    for row in results:
        lines.append(
            f'| {row["case"]["id"]} | {row["case"]["attendu"]} | {row["got"]} | {row["result"].get("score", "—")} | {row["result"].get("faq_id", "—")} | {row["calls"]} | {row["result"]["source"]} | {"OK" if row["correct"] else "ÉCHEC"} |'
        )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return passed, total
