"""Limites partagées et verrouillage temporaire, sans email/IP en clair dans les clés."""
import hashlib
import hmac
import math
import time

from flask import current_app, jsonify, render_template, request
from flask_login import current_user
from flask_limiter import Limiter
from limits.errors import StorageError


def private_key(value):
    secret = current_app.config['SECRET_KEY']
    if isinstance(secret, str):
        secret = secret.encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


def client_key():
    return private_key('ip:' + (request.remote_addr or 'unknown'))


def chat_key():
    return private_key('user:' + str(current_user.id)) if current_user.is_authenticated else client_key()


def storage():
    return current_app.extensions['autohelp_limiter'].storage


def account_keys(email):
    identity = private_key('login:' + email.strip().lower())
    return 'autohelp:failures:' + identity, 'autohelp:locked:' + identity


def locked(email):
    if not current_app.config['RATELIMIT_ENABLED']:
        return False
    return bool(storage().get(account_keys(email)[1]))


def login_failed(email):
    if not current_app.config['RATELIMIT_ENABLED']:
        return
    failures, lock = account_keys(email)
    count = storage().incr(failures, current_app.config['LOGIN_FAILURE_WINDOW'])
    if count >= current_app.config['LOGIN_MAX_FAILURES']:
        storage().incr(lock, current_app.config['LOGIN_LOCKOUT_SECONDS'])


def login_succeeded(email):
    if current_app.config['RATELIMIT_ENABLED']:
        failures, lock = account_keys(email)
        storage().clear(failures)
        storage().clear(lock)


def too_many_requests(error=None):
    message = 'Trop de tentatives. Patientez avant de réessayer.'
    if request.path.startswith('/api/'):
        response = jsonify(error=message)
    else:
        response = current_app.make_response(render_template('error.html', message=message, code=429))
    response.status_code = 429
    response.headers['Retry-After'] = '60'
    return response


def lock_response(email):
    response = too_many_requests()
    delay = storage().get_expiry(account_keys(email)[1]) - time.time()
    response.headers['Retry-After'] = str(max(1, math.ceil(delay)))
    return response


def init_protection(app):
    if app.config['APP_ENV'] == 'production' and not app.config['RATELIMIT_STORAGE_URI'].startswith(('redis://', 'rediss://')):
        raise RuntimeError('Redis partagé est obligatoire pour les limites de requêtes en production.')
    limiter = Limiter(key_func=client_key, app=app, default_limits=[])
    app.extensions['autohelp_limiter'] = limiter
    for endpoint, setting, key in (
        ('auth.login', 'LOGIN_RATE_LIMIT', client_key),
        ('auth.register', 'REGISTER_RATE_LIMIT', client_key),
        ('chat.chat', 'CHAT_RATE_LIMIT', chat_key),
    ):
        app.view_functions[endpoint] = limiter.limit(
            lambda setting=setting: app.config[setting], methods=['POST'], key_func=key,
        )(app.view_functions[endpoint])
    app.register_error_handler(429, too_many_requests)

    @app.errorhandler(StorageError)
    def storage_unavailable(error):
        app.logger.warning('event=rate_storage_unavailable')
        message = 'Service temporairement indisponible. Réessayez plus tard.'
        if request.path.startswith('/api/'):
            return jsonify(error=message), 503
        return render_template('error.html', message=message, code=503), 503
