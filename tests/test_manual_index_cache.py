from app.services.document_tools import DocumentTools
from app.services.manual_index import cache_info, clear


def search(row):
    ref = dict(marque=row['brand'], modele=row['model'], annee=row['year'])
    tools = DocumentTools({**ref, 'manual_reference': ref}, ref, lambda: [row])
    tools.bind_query('pression des pneus')
    return tools.dispatch('rechercher_manuel', {'requete': 'pression des pneus'})


def test_cache_reuses_index_but_never_another_identity_edition_or_corrected_text():
    clear()
    row = dict(
        brand='Dacia',
        model='Bigster',
        year=2026,
        page=12,
        section='Pression des pneus',
        contenu='Vérifier la pression des pneus à froid.',
        sha256='a' * 64,
    )
    assert search(row) == search(row)
    assert cache_info().misses == 1 and cache_info().hits == 1
    other = {**row, 'model': 'Duster'}
    assert search(other)['passages'][0]['modele'] == 'Duster'
    search({**row, 'sha256': 'b' * 64})
    updated = search({**row, 'contenu': 'La pression des pneus figure sur la porte.'})
    assert 'porte' in updated['passages'][0]['contenu']
    assert cache_info().misses == 4
