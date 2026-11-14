import json

import pytest

from app.services.manual_evaluation import evaluate_case, load_cases, numeric_accuracy, write_report

SHA = 'a' * 64
REF = {'marque': 'Dacia', 'modele': 'Bigster', 'annee': 2026}
CASE = {
    'id': 'M001',
    'vehicule': REF,
    'question': 'Comment vérifier la pression des pneus ?',
    'valide': True,
    'sha256_pdf': SHA,
    'verification': {'date': '2026-11-14', 'par': 'recette fictive', 'methode': 'fixture'},
    'attendu': {
        'type': 'reponse',
        'pages_pdf': [12],
        'reponse': 'Lire l’étiquette du véhicule.',
        'valeurs': None,
    },
}
ROW = {
    'brand': 'Dacia',
    'model': 'Bigster',
    'year': 2026,
    'page': 12,
    'page_imprimee': 10,
    'section': 'Pression des pneus',
    'contenu': 'Vérifiez la pression des pneus sur l’étiquette du véhicule. Contrôlez les pneumatiques à froid.',
    'sha256': SHA,
}


def test_draft_annotations_cannot_be_scored(tmp_path):
    case = {**CASE, 'valide': False}
    result = evaluate_case(case, [ROW])
    assert result == {'id': 'M001', 'statut': 'a_annoter'}
    assert not write_report(tmp_path / 'rapport.md', [result], {'bigster': [case]})
    assert 'non mesuré' in (tmp_path / 'rapport.md').read_text(encoding='utf8')


def test_real_page_recall_uses_bound_vehicle_only():
    result = evaluate_case(CASE, [ROW, {**ROW, 'model': 'Duster', 'page': 99}])
    assert result['rappel_top3'] is True and result['pages_trouvees'] == [12]


def test_other_vehicle_and_other_edition_cannot_produce_a_score():
    assert (
        evaluate_case(CASE, [{**ROW, 'model': 'Duster'}])['statut']
        == 'index_absent_ou_edition_differente'
    )
    assert (
        evaluate_case(CASE, [{**ROW, 'sha256': 'b' * 64}])['statut']
        == 'index_absent_ou_edition_differente'
    )


def test_expected_page_miss_is_reported_not_adjusted():
    result = evaluate_case({**CASE, 'attendu': {**CASE['attendu'], 'pages_pdf': [99]}}, [ROW])
    assert result['rappel_top3'] is False


def test_verified_annotation_requires_manual_evidence(tmp_path):
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps([{**CASE, 'verification': {}}]))
    with pytest.raises((ValueError, KeyError)):
        load_cases(path)


def test_generation_metrics_use_actual_verified_references():
    from app.services.evaluation_model import CONFIG, FakeModel

    result = evaluate_case(CASE, [ROW], generate=True, config=CONFIG, transport=FakeModel())
    assert result['citation_correcte'] is True and result['valeurs_correctes'] is None


def test_refusal_is_measured_without_inventing_a_citation():
    from app.services.evaluation_model import CONFIG, FakeModel

    case = {
        **CASE,
        'question': 'Comment remplacer le filtre d’habitacle ?',
        'attendu': {'type': 'sans_information', 'pages_pdf': [], 'valeurs': None},
    }
    result = evaluate_case(case, [ROW], generate=True, config=CONFIG, transport=FakeModel())
    assert result['rappel_top3'] is None and result['absence_recherche'] is True
    assert result['refus_correct'] is True
    assert result['citation_correcte'] is None


def test_generation_budget_limits_model_calls():
    from app.services.evaluation_model import CONFIG, FakeModel
    from app.services.manual_evaluation import evaluate

    model = FakeModel()
    results, _ = evaluate(
        [CASE, {**CASE, 'id': 'M002'}],
        lambda ref: [ROW],
        generate=True,
        config=CONFIG,
        transport=model,
        limit=1,
    )
    assert len(model.requests) == 2
    assert results[1]['citation_correcte'] is None


def test_numeric_mismatch_is_reported_without_changing_expected_values():
    from app.services.evaluation_model import CONFIG, FakeModel

    case = {**CASE, 'attendu': {**CASE['attendu'], 'valeurs': ['2,2 bar']}}
    row = {**ROW, 'contenu': 'La pression des pneus de cette fixture fictive est de 1,4 bar.'}
    result = evaluate_case(case, [row], generate=True, config=CONFIG, transport=FakeModel())
    assert result['valeurs_correctes'] is False


def test_numeric_metric_keeps_compound_units_and_accepts_equivalent_notation():
    assert numeric_accuracy(
        'Moins de 4 mm ; au plus 15 min, 200 kilomètres et 80 km/h.',
        ['4 millimètres', '15 minutes', '200 km', '80 km/h'],
    )
    assert not numeric_accuracy('Ne pas dépasser 80 km.', ['80 km/h'])
    assert not numeric_accuracy('Ne pas dépasser 80 km/h.', ['80 km'])


def test_numeric_metric_preserves_decimals_grouped_digits_and_range_endpoints():
    assert numeric_accuracy('2,2 bars et 1\u202f000 km.', ['2.2 bar', '1000 kilomètres'])
    assert not numeric_accuracy('22 bar', ['2,2 bar'])
    assert numeric_accuracy('De 3 000 à 3 500 tr/mn.', ['3000 tr/min', '3500 tr/min'])
    assert not numeric_accuracy('De 3000 à 3500 tr/min.', ['3500 tr/min'])


def test_numeric_metric_rejects_missing_extra_and_unsupported_measurements():
    assert not numeric_accuracy('15 min et 80 km/h', ['15 minutes'])
    assert not numeric_accuracy('Aucune valeur disponible.', ['2 bar'])
    assert not numeric_accuracy('Une valeur non prise en charge.', ['2 unités_inconnues'])
    assert numeric_accuracy('Aucune valeur technique dans cette phrase.', [])
    assert not numeric_accuracy('2 bar', [])


def test_assisted_annotations_cannot_complete_the_benchmark_without_human_review(tmp_path):
    cases = [{**CASE, 'id': f'M{i:03d}'} for i in range(50)]
    results = [evaluate_case(case, [ROW]) for case in cases]
    assert not write_report(tmp_path / 'rapport.md', results, {'bigster': cases})
    reviewed = [
        {
            **case,
            'verification': {
                **case['verification'],
                'revue_humaine': {
                    'par': 'relecteur de recette fictif',
                    'date': '2026-11-14',
                    'methode': 'lecture indépendante de la fixture',
                },
            },
        }
        for case in cases
    ]
    assert write_report(tmp_path / 'rapport.md', results, {'bigster': reviewed})


def test_report_does_not_inflate_page_recall_with_absence_cases(tmp_path):
    absent = {
        **CASE,
        'id': 'M002',
        'question': 'Quel est le prix du garage local ?',
        'attendu': {'type': 'sans_information', 'pages_pdf': [], 'valeurs': None},
    }
    path = tmp_path / 'rapport.md'
    results = [evaluate_case(CASE, [ROW]), evaluate_case(absent, [ROW])]
    write_report(path, results, {'bigster': [CASE, absent]}, SHA)
    report = path.read_text(encoding='utf8')
    assert '| Dacia Bigster 2026 | 2 | 2 | 0 | 1/1 | 1/1 |' in report
    assert 'Empreinte SHA-256 du jeu : ' + SHA in report


def test_absence_annotation_cannot_supply_an_invented_page(tmp_path):
    path = tmp_path / 'cases.json'
    path.write_text(
        json.dumps([{**CASE, 'attendu': {**CASE['attendu'], 'type': 'sans_information'}}])
    )
    with pytest.raises(ValueError, match='page source'):
        load_cases(path)


@pytest.mark.parametrize(
    'review',
    [
        True,
        {},
        {'par': 'relecteur'},
        {'par': 'relecteur', 'date': 'invalide', 'methode': 'lecture'},
    ],
)
def test_human_review_needs_explicit_traceable_evidence(tmp_path, review):
    path = tmp_path / 'cases.json'
    path.write_text(
        json.dumps([{**CASE, 'verification': {**CASE['verification'], 'revue_humaine': review}}])
    )
    with pytest.raises(ValueError):
        load_cases(path)


def test_cli_refuses_to_validate_incomplete_real_corpus(app, tmp_path):
    result = app.test_cli_runner().invoke(
        args=['evaluer-manuels', '--rapport', str(tmp_path / 'rapport.md')]
    )
    assert result.exit_code == 1
    assert 'cinquante annotations' in result.output
    assert (tmp_path / 'rapport.md').is_file()


def test_cli_normalizes_case_accents_and_spaces_without_changing_vehicle(app, tmp_path):
    from app import db
    from app.models import ManuelPassage

    with app.app_context():
        db.session.add(
            ManuelPassage(
                brand='Dacia',
                model='Bigster',
                year=2026,
                page=12,
                position=0,
                section=ROW['section'],
                contenu=ROW['contenu'],
                search_index='',
                source='equipe: fixture',
                added_at='2026-11-14',
                document_metadata={'sha256': SHA, 'page_imprimee': 10},
            )
        )
        db.session.commit()
    case = {**CASE, 'vehicule': {'marque': 'DÁ CIA', 'modele': 'Big ster', 'annee': 2026}}
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps([case]), encoding='utf8')
    result = app.test_cli_runner().invoke(
        args=[
            'evaluer-manuels',
            '--jeu',
            str(path),
            '--rapport',
            str(tmp_path / 'rapport.md'),
            '--partiel',
        ]
    )
    assert result.exit_code == 0, result.output
    assert '1 évalués' in result.output


def test_benchmark_uses_api_version_rules_from_original_question():
    case = {
        **CASE,
        'question': 'Quelle pression des pneus pour la version 4x2 ?',
        'vehicule': {**REF, 'motorisation': '4x4'},
        'attendu': {**CASE['attendu'], 'pages_pdf': [13]},
    }
    result = evaluate_case(
        case, [{**ROW, 'versions': ['4x4']}, {**ROW, 'page': 13, 'versions': ['4x2']}]
    )
    assert result['pages_trouvees'] == [13]
