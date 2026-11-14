"""Cache LRU borné par worker, identité exacte et contenu/édition de l'index."""

from functools import lru_cache
from threading import RLock

lock = RLock()


@lru_cache(maxsize=8)
def _fit(identity, edition, documents):
    from sklearn.feature_extraction.text import TfidfVectorizer

    from app.services.document_tools import manual_words

    vectorizer = TfidfVectorizer(
        tokenizer=manual_words, token_pattern=None, lowercase=False, sublinear_tf=True
    )
    return vectorizer, vectorizer.fit_transform(documents)


def get_index(identity, rows, documents):
    edition = tuple(sorted({str(r.get('sha256', '')) for r in rows}))
    with lock:
        return _fit(identity, edition, tuple(documents))


def cache_info():
    return _fit.cache_info()


def clear():
    with lock:
        _fit.cache_clear()
