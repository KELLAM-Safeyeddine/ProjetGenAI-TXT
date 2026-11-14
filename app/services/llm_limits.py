import os

BOUNDS = {
    'LLM_CALL_TIMEOUT': (5, 1, 30),
    'LLM_TOTAL_TIMEOUT': (20, 5, 90),
    'LLM_MAX_TURNS': (4, 2, 8),
    'LLM_MAX_ATTEMPTS': (2, 1, 3),
    'LLM_CONTEXT_CHARS': (28000, 8000, 48000),
}


def limits(config=None):
    values = os.environ if config is None else config
    result = {}
    for name, (default, low, high) in BOUNDS.items():
        try:
            raw = values.get(name)
            value = int(default if raw is None or raw == '' else raw)
        except (ValueError, TypeError):
            raise ValueError(name + ' doit être un entier.') from None
        if not low <= value <= high:
            raise ValueError(name + f' doit être compris entre {low} et {high}.')
        result[name] = value
    return result
