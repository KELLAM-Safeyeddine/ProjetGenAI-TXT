"""Recette HTTP réelle avec CSRF et cookies, sans dépendance supplémentaire.

Depuis le dossier autonome : python tests/smoke_http.py http://localhost:8000
Ajouter --restart pour recréer web et db puis vérifier la persistance.
Crée puis supprime un compte de test unique ; aucune donnée préexistante modifiée.
"""

import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import time
from datetime import date, timedelta
from http.cookiejar import CookieJar
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, HTTPSHandler, ProxyHandler, Request, build_opener


def main():
    base = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:8000'
    handlers = [
        HTTPCookieProcessor(CookieJar()),
        HTTPSHandler(context=ssl.create_default_context(cafile=os.environ.get('AUTOHELP_TEST_CA'))),
    ]
    if urlsplit(base).hostname in ('localhost', '127.0.0.1'):
        handlers.append(ProxyHandler({}))
    opener = build_opener(*handlers)

    def call(path, data=None, json_data=None, csrf=None):
        headers = {'Referer': base + '/'} if base.startswith('https:') else {}
        payload = None
        if data is not None:
            payload = urlencode(data).encode()
        if json_data is not None:
            payload = json.dumps(json_data).encode()
            headers['Content-Type'] = 'application/json'
        if csrf:
            headers['X-CSRFToken'] = csrf
        with opener.open(
            Request(base + path, data=payload, headers=headers), timeout=30
        ) as response:
            return response.read().decode()

    def token(path):
        return re.search(r'name="csrf-token" content="([^"]+)"', call(path)).group(1)

    email = f'recette-{secrets.token_hex(6)}@example.test'
    password = secrets.token_urlsafe(24)
    assert json.loads(call('/health'))['status'] == 'ok'
    call(
        '/register',
        data=dict(
            name='Recette HTTP',
            email=email,
            password=password,
            confirm=password,
            csrf_token=token('/register'),
        ),
    )
    page = call(
        '/vehicles/new',
        data=dict(
            brand='Dacia',
            model='Bigster',
            year=2026,
            engine_type='Essence',
            mileage=50000,
            csrf_token=token('/vehicles/new'),
        ),
    )
    vid = int(re.search(r'/vehicles/(\d+)/maintenance', page).group(1))
    path = f'/vehicles/{vid}/maintenance/new'
    page = call(
        path,
        data=dict(
            type='Vidange',
            date=str(date.today() - timedelta(days=1)),
            mileage=49000,
            cost='325.50',
            notes='Recette avec CSRF',
            next_date=str(date.today() + timedelta(days=365)),
            next_mileage=60000,
            csrf_token=token(path),
        ),
    )
    assert '325.50' in page
    result = json.loads(
        call(
            '/api/chat',
            json_data=dict(message='Quelle pression pour mes pneus ?', vehicle_id=vid),
            csrf=token('/chat'),
        )
    )
    assert result['source'] in {'manuel', 'aucune', 'indisponible'}
    if result['status'] == 'indisponible':
        assert result['reply'].startswith("L'assistant est indisponible pour le moment.")
    elif result['status'] == 'orientation':
        assert (
            not result['source_line'] and not result['references'] and 'précisez' in result['reply']
        )
    elif result['status'] == 'manuel_absent':
        assert 'manuel du Dacia Bigster 2026' in result['reply'] and not result['references']
    elif result['source'] == 'manuel':
        assert result['references'] and result['source_line'].startswith('Source : ')
    assert result['source'] != 'faq'
    cid = result['conversation_id']
    call('/logout', data=dict(csrf_token=token('/dashboard')))
    call('/login', data=dict(email=email, password=password, csrf_token=token('/login')))
    assert 'Recette HTTP' in call('/dashboard')
    assert len(json.loads(call(f'/api/conversations/{cid}/messages'))['messages']) == 2
    print('Parcours HTTP complet : OK (CSRF actif, historique après reconnexion).', flush=True)
    if '--restart' in sys.argv:
        restart_env = os.environ.copy()
        restart_env['PORT'] = str(urlsplit(base).port or 80)
        subprocess.run(
            ['docker', 'compose', 'up', '-d', '--force-recreate'], check=True, env=restart_env
        )
        for _ in range(45):
            try:
                if json.loads(call('/health'))['status'] == 'ok':
                    break
            except (URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(1)
        else:
            raise RuntimeError('Le service ne revient pas en état sain.')
        assert 'Recette HTTP' in call('/dashboard')
        assert '325.50' in call(f'/vehicles/{vid}/maintenance')
        assert len(json.loads(call(f'/api/conversations/{cid}/messages'))['messages']) == 2
        print('Recréation web + db : données et session conservées.', flush=True)
    call(
        '/account/delete',
        data=dict(password=password, confirm='y', csrf_token=token('/account/delete')),
    )
    print('Compte de recette et données supprimés ; aucun identifiant conservé.', flush=True)


if __name__ == '__main__':
    main()
