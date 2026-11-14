from app.services.document_tools import DocumentTools


def test_experimental_ranker_preserves_identity_version_and_visual_reserves():
    ref = dict(marque='Dacia', modele='Bigster', annee=2026)
    row = dict(
        brand='Dacia',
        model='Bigster',
        year=2026,
        page=12,
        section='Pression des pneus',
        contenu='Contrôler la pression des pneus à froid.',
        versions=['4x2'],
    )
    rows = [
        row,
        {**row, 'model': 'Duster', 'page': 99},
        {**row, 'page': 98, 'controle_visuel_requis': True},
        {**row, 'page': 97, 'versions': ['4x4']},
    ]
    tools = DocumentTools(
        {**ref, 'motorisation': '4x2'}, ref, lambda: rows, search_variant='hybride_experimental'
    )
    tools.bind_query('Quelle pression des pneus ?')
    found = tools.dispatch('rechercher_manuel', {'requete': 'pression des pneus'})
    assert [r['page_pdf'] for r in found['passages']] == [12]
    assert (
        tools.dispatch(
            'rechercher_manuel', {'requete': 'pression', 'search_variant': 'hybride_experimental'}
        )['statut']
        == 'refuse'
    )
