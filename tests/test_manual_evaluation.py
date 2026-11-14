import json

import pytest

from app.services.manual_evaluation import evaluate_case, load_cases, write_report

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
    assert result['rappel_top3'] is True and result['refus_correct'] is True
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
