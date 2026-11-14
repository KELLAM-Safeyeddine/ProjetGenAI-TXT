import ast
import importlib.util
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'standalone_chatbot', ROOT / 'app/services/chatbot_service.py'
)
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)


def evaluate():
    from app.services.chatbot_evaluation import evaluate as run_evaluation

    start = perf_counter()
    results = run_evaluation()
    for row in results:
        print(
            row['case']['id'],
            row['case']['message'],
            'score=',
            row['result'].get('score', 0),
            row['got'],
            row['correct'],
        )
    return results, perf_counter() - start


def test_dataset_accuracy():
    results, elapsed = evaluate()
    assert len(results) >= 60
    assert sum(row['correct'] for row in results) / len(results) >= 0.8, [
        r for r in results if not r['correct']
    ]
    assert elapsed / len(results) < 2


def test_normalization_and_validation():
    assert bot.normalize(' ÉTÉ,  huile! ') == 'ete huile'
    for value in (None, '', '   ', 12, 'a' * 1001):
        assert bot.search_response(value)['source'] == 'validation'


def test_safety_even_when_unknown():
    for message in ('freins', 'pneus', 'voyant rouge inconnu', 'STOP'):
        assert 'Sécurité' in bot.get_response(message)


def test_all_sensitive_entries_warn():
    for entry in bot.load_faq():
        if entry['categorie'] in ('pneus', 'freinage') or entry['niveau_risque'] == 'eleve':
            assert 'Sécurité' in bot.get_response(entry['question'])


def test_unknown_and_no_flask_dependency():
    assert (
        bot.search_response('Quelle recette pour un gâteau au chocolat ?')['source'] == 'hors_sujet'
    )
    tree = ast.parse((ROOT / 'app/services/chatbot_service.py').read_text(encoding='utf-8'))
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(name and name.startswith('flask') for name in imports)
