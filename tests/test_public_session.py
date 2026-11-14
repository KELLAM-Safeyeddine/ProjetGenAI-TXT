import pytest


@pytest.mark.parametrize('path', ['/', '/login', '/register'])
def test_public_pages_respect_authenticated_session(alice, path):
    response = alice.get(path, follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Tableau de bord' in html
    assert 'Déconnexion' in html
    assert 'Me connecter' not in html
    assert 'Créer mon compte' not in html
    assert 'M’inscrire' not in html


def test_public_home_keeps_anonymous_access(client):
    html = client.get('/').data.decode('utf-8')
    assert 'Me connecter' in html
    assert 'Déconnexion' not in html
