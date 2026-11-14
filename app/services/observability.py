"""Événements sur liste blanche : ni texte libre, URL, compte, exception ou secret."""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from flask import g, has_request_context


class SafeJSONFormatter(logging.Formatter):
    def format(self, record):
        event = getattr(record, 'event', '')
        data = {
            'date': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'event': event
            if event in {'request', 'llm_call', 'startup', 'retention', 'error'}
            else 'application_event',
        }
        if has_request_context():
            data['request_id'] = getattr(g, 'request_id', None)
        provider = getattr(record, 'provider', None)
        if provider in ('openai', 'groq'):
            data['provider'] = provider
        reasons = {
            'no_provider': 'Configurer le fournisseur dans les variables privées ; FAQ locale disponible.',
            'incomplete_provider': 'Compléter le modèle et son URL dans la configuration privée.',
            'no_manuals': 'Placer les PDF autorisés puis lancer flask import-manuels.',
        }
        reason = getattr(record, 'reason', None)
        if reason in reasons:
            data['reason'] = reason
            data['message'] = reasons[reason]
        for key in ('duration_ms', 'turns', 'tokens'):
            value = getattr(record, key, None)
            if type(value) in (int, float) and 0 <= value <= 10_000_000:
                data[key] = round(value, 2)
        status = getattr(record, 'status', None)
        if (
            type(status) is int
            and 100 <= status <= 599
            or status in ('ok', 'unavailable', 'timeout', 'configuration', 'error')
        ):
            data['status'] = status
        return json.dumps(data, ensure_ascii=False)


def init_observability(app):
    handler = logging.StreamHandler()
    handler.setFormatter(SafeJSONFormatter())
    handler._autohelp = True
    logger = logging.getLogger('autohelp')
    for old in list(logger.handlers):
        if getattr(old, '_autohelp', False):
            logger.removeHandler(old)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    app.logger.handlers = [handler]

    @app.before_request
    def start_request():
        g.request_id = uuid.uuid4().hex
        g.started = time.monotonic()
        g.llm_turns = 0
        g.llm_tokens = None

    @app.after_request
    def record_request(response):
        response.headers['X-Request-ID'] = g.get('request_id', '')
        logging.getLogger('autohelp.http').info(
            'request',
            extra=dict(
                event='request',
                duration_ms=(time.monotonic() - g.get('started', time.monotonic())) * 1000,
                status=response.status_code,
                turns=g.get('llm_turns', 0),
                tokens=g.get('llm_tokens'),
            ),
        )
        return response


def record_model(provider, started, status, result=None):
    count = (result or {}).get('_usage', {}).get('total_tokens')
    count = count if type(count) is int and 0 <= count <= 1_000_000 else None
    if has_request_context():
        g.llm_turns = g.get('llm_turns', 0) + 1
        if count is not None:
            g.llm_tokens = (g.get('llm_tokens') or 0) + count
    logging.getLogger('autohelp.llm').info(
        'llm_call',
        extra=dict(
            event='llm_call',
            provider=provider.name,
            duration_ms=(time.monotonic() - started) * 1000,
            turns=1,
            tokens=count,
            status=status,
        ),
    )
