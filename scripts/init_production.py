"""Génère uniquement sur le serveur choisi ; aucun secret affiché ou livré."""

import argparse
import re
import secrets
from pathlib import Path


def initialize(root, domain):
    if (
        not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,250}[a-z0-9])?', domain)
        or '.' not in domain
        or '..' in domain
    ):
        raise ValueError('Utilisez un nom de domaine DNS simple, sans URL ni port.')
    root = Path(root).resolve()
    private = root / 'secrets'
    if (root / '.env').exists() or private.exists():
        raise ValueError('Configuration privée déjà présente ; aucun écrasement.')
    root.mkdir(parents=True, exist_ok=True)
    private.mkdir(mode=0o700)
    password = private / 'postgres_password'
    password.write_text(secrets.token_urlsafe(48), encoding='utf8')
    # Le répertoire hôte est privé ; le fichier reste lisible par les UID des
    # conteneurs sur le bind-mount Compose, qui ne remappe pas son uid/mode.
    password.chmod(0o644)
    with (root / '.env').open('x', encoding='utf8') as output:
        output.write(
            'APP_ENV=production\nDOMAIN='
            + domain
            + '\nSECRET_KEY='
            + secrets.token_hex(48)
            + '\nDATABASE_PASSWORD_FILE=secrets/postgres_password\nLLM_PROVIDER=auto\nOPENAI_API_KEY=\nOPENAI_MODEL=\nOPENAI_BASE_URL=\nGROQ_API_KEY=\nGROQ_MODEL=\nGROQ_BASE_URL=\nDATA_CONTROLLER_NAME=\nDATA_CONTROLLER_CONTACT=\nCONVERSATION_RETENTION_DAYS=0\nBACKUP_INTERVAL_SECONDS=86400\nBACKUP_KEEP=7\n'
        )
    (root / '.env').chmod(0o600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', required=True)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    initialize(args.directory, args.domain.lower())
    print(
        'Configuration privée créée ; aucune clé affichée. Compléter responsable et fournisseur avant ouverture.'
    )
