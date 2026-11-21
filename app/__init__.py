from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(test_config=None):
    from config import instance_directory, settings

    values = settings()
    app = Flask(__name__, instance_path=str(instance_directory()))
    app.config.update(values)
    if test_config:
        app.config.update(test_config)
        if test_config.get('TESTING') and 'RATELIMIT_ENABLED' not in test_config:
            app.config['RATELIMIT_ENABLED'] = False
    hops = app.config['PROXY_HOPS']
    if type(hops) is not int or not 0 <= hops <= 2:
        raise RuntimeError(
            'PROXY_HOPS doit être un entier entre zéro et deux, selon les proxys de confiance.'
        )
    if hops:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=hops, x_proto=hops, x_host=0, x_port=0, x_prefix=0
        )
    from app.services.observability import init_observability
    from app.services.startup_checks import report_startup

    init_observability(app)
    report_startup(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Connectez-vous pour accéder à cette page.'

    @app.before_request
    def api_session():
        from flask_login import current_user

        if request.path.startswith('/api/') and not current_user.is_authenticated:
            return jsonify(error='Session expirée. Reconnectez-vous.'), 401

    csrf.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        parts = user_id.split(':')
        if len(parts) > 2 or not all(p.isascii() and p.isdigit() and len(p) < 19 for p in parts):
            return None
        user = db.session.get(User, int(parts[0]))
        version = int(parts[1]) if len(parts) == 2 else 1
        return user if user and user.auth_version == version else None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith('/api/'):
            return jsonify(error='Session expirée. Reconnectez-vous.'), 401
        from flask import redirect, url_for

        return redirect(url_for('auth.login'))

    from app.routes import (
        admin,
        auth,
        chat,
        feedback,
        maintenance,
        manual_review,
        privacy,
        vehicles,
    )

    for module in (auth, vehicles, maintenance, admin, chat, manual_review, feedback, privacy):
        app.register_blueprint(module.bp)
    from app.services.abuse_protection import init_protection

    init_protection(app)

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/health')
    def health():
        # Vivacité du serveur : aucune requête vers la base de données.
        return jsonify(status='ok'), 200

    @app.get('/ready')
    def ready():
        from urllib.parse import urlsplit

        from app.models import ManuelPassage
        from app.services.llm_service import choose_provider

        try:
            # Une requête ORM vérifie la connexion et l'existence du schéma.
            db.session.execute(db.select(User.id).limit(1)).first()
            indexed = (
                db.session.execute(
                    db.select(ManuelPassage.id)
                    .where(
                        ManuelPassage.active.is_(True),
                        ManuelPassage.document_metadata['controle_visuel_requis']
                        .as_boolean()
                        .is_not(True),
                    )
                    .limit(1)
                ).first()
                is not None
            )
            provider = choose_provider(app.config)
            configured = bool(
                provider
                and provider.model
                and urlsplit(provider.base_url).scheme == 'https'
                and urlsplit(provider.base_url).hostname
            )
            available = indexed and configured
            return jsonify(
                status='ok' if available else 'unavailable',
                components=dict(database=True, index=indexed, provider=configured),
            ), 200 if available else 503
        except Exception:
            db.session.rollback()
            return jsonify(status='unavailable'), 503

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error='Jeton de sécurité absent ou expiré. Rechargez la page.'), 400
        return render_template(
            'error.html', message='Formulaire expiré. Rechargez la page et réessayez.', code=400
        ), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {
            400: 'Requête invalide.',
            403: 'Accès réservé.',
            404: 'Ressource introuvable ou inaccessible.',
            405: 'Méthode non autorisée.',
            413: 'Contenu trop volumineux.',
            415: 'Envoyez un objet JSON.',
        }
        message = messages.get(error.code, 'La requête ne peut pas être traitée.')
        if request.path.startswith('/api/'):
            return jsonify(error=message), error.code
        return render_template('error.html', message=message, code=error.code), error.code

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify(
                error='Service temporairement indisponible. Rechargez l’historique avant de réessayer.'
            ), 500
        return render_template(
            'error.html', message='Service temporairement indisponible.', code=500
        ), 500

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
        )
        if request.path != '/health':
            response.headers['Cache-Control'] = 'no-store'
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    from app.cli import register_cli

    register_cli(app)
    return app
