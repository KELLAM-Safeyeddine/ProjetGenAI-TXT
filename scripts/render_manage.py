"""Administration depuis le PC vers Neon, via .env.render privé, sans appel LLM."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    'initialiser': (('db', 'upgrade'), ('import-manuels', '--lecture-seule')),
    'creer-admin': (('create-admin',),),
    'verifier': (('lister-manuels-dacia',), ('list-manuels',)),
}


def environment_from_file(path, inherited=None):
    names = {
        line.split('=', 1)[0]
        for line in (ROOT / '.env.example').read_text(encoding='utf-8').splitlines()
        if line and not line.startswith('#')
    }
    try:
        path = Path(path)
        if path.stat().st_size > 32768:
            raise ValueError('Fichier de configuration trop volumineux.')
        content = path.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError):
        raise ValueError(
            'Fichier privé illisible ; créer .env.render depuis .env.example.'
        ) from None
    values = {}
    for number, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or not re.fullmatch('[A-Z][A-Z0-9_]*', key) or key not in names:
            raise ValueError(f'Variable non reconnue à la ligne {number} ; contenu masqué.')
        if key in values:
            raise ValueError(f'Variable répétée à la ligne {number} ; contenu masqué.')
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        values[key] = value
    if values.get('APP_ENV') != 'production' or len(values.get('SECRET_KEY', '')) < 32:
        raise ValueError('Renseigner APP_ENV=production et SECRET_KEY (au moins 32 caractères).')
    try:
        database = urlsplit(values.get('DATABASE_URL', ''))
        if (
            database.scheme not in ('postgres', 'postgresql', 'postgresql+psycopg')
            or not database.hostname
            or not database.path.strip('/')
            or database.netloc.endswith(':')
            or database.fragment
        ):
            raise ValueError
        if database.port is not None and not 1 <= database.port <= 65535:
            raise ValueError
    except ValueError:
        raise ValueError('DATABASE_URL doit contenir une connexion PostgreSQL valide.') from None
    try:
        redis = urlsplit(values.get('RATELIMIT_STORAGE_URI', ''))
        if redis.scheme != 'rediss' or not redis.hostname or not redis.password or redis.query:
            raise ValueError
        if redis.port is not None and not 1 <= redis.port <= 65535:
            raise ValueError
    except ValueError:
        raise ValueError(
            'RATELIMIT_STORAGE_URI doit être une URL Redis TLS rediss:// valide.'
        ) from None
    if values.get('DATABASE_PASSWORD_FILE'):
        raise ValueError('Utiliser la connexion Neon complète, sans DATABASE_PASSWORD_FILE.')
    environ = dict(os.environ if inherited is None else inherited)
    # Les valeurs absentes restent vides : config.load_dotenv ne peut ainsi pas
    # reprendre les secrets ou la base du .env personnel du développeur.
    for name in names:
        environ[name] = values.get(name, '')
    environ.update(LLM_PROVIDER='none', FLASK_SKIP_DOTENV='1')
    for prefix in ('GROQ', 'OPENAI', 'SEARCH'):
        environ[prefix + '_API_KEY'] = ''
    environ['AI_API_KEY'] = ''
    return environ


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=COMMANDS)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env.render')
    args = parser.parse_args(argv)
    try:
        environ = environment_from_file(args.env_file)
    except ValueError as error:
        print(f'Configuration Render invalide : {error}', file=sys.stderr)
        return 2
    try:
        for command in COMMANDS[args.operation]:
            subprocess.run(
                [sys.executable, '-m', 'flask', '--app', 'run', *command],
                cwd=ROOT,
                env=environ,
                check=True,
            )
    except subprocess.CalledProcessError:
        print(
            'Opération interrompue après échec ; consulter le diagnostic précédent.',
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
