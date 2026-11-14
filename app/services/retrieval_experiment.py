"""Candidat de benchmark uniquement : jamais sélectionnable par l'API ou le modèle."""

import math
from collections import Counter
from functools import lru_cache


@lru_cache(maxsize=8)
def _corpus(identity, documents):
    from app.services.document_tools import manual_words

    counts = [Counter(manual_words(doc)) for doc in documents]
    frequency = Counter(word for row in counts for word in row)
    lengths = [sum(row.values()) for row in counts]
    return counts, frequency, lengths, sum(lengths) / max(1, len(lengths))


def bm25(identity, documents, words):
    counts, frequency, lengths, average = _corpus(identity, tuple(documents))
    scores = []
    for row, length in zip(counts, lengths):
        score = 0.0
        for word in words:
            tf = row[word]
            if tf:
                idf = math.log1p((len(counts) - frequency[word] + 0.5) / (frequency[word] + 0.5))
                score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * length / max(1, average)))
        scores.append(score)
    maximum = max(scores, default=0)
    return [s / maximum if maximum else 0 for s in scores]
