"""FAQ générale sans véhicule : données locales, moteur FAQ existant, aucun LLM."""

import json
import re
from functools import lru_cache
from pathlib import Path

from app.services.chatbot_service import THRESHOLD, search_response, tokens

FAQ_PATH = Path(__file__).resolve().parents[2] / 'data/faq_generale.json'
RISK_LEVELS = {'faible', 'moyen', 'élevé'}
MECHANIC_END = 'Pour plus d’informations, consultez un mécanicien.'
NO_MATCH = 'Je ne trouve pas de réponse assez précise à cette question. Reformulez en indiquant l’élément concerné et ce que vous observez, ou sélectionnez votre véhicule pour rechercher une indication adaptée.'


def validate_entries(entries):
    if not isinstance(entries, list) or not entries:
        raise ValueError('La FAQ générale doit contenir une liste non vide.')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Entrée de FAQ générale invalide.')
        identifier = entry.get('identifiant')
        if (
            not isinstance(identifier, str)
            or not re.fullmatch('[a-z_]+', identifier)
            or identifier in seen
        ):
            raise ValueError('Identifiant de FAQ générale invalide ou dupliqué.')
        seen.add(identifier)
        for name in ('categorie', 'question', 'reponse'):
            if (
                not isinstance(entry.get(name), str)
                or not entry[name].strip()
                or len(entry[name]) > 4000
            ):
                raise ValueError('Texte de FAQ générale invalide.')
        if not 150 <= len(entry['reponse'].split()) <= 300:
            raise ValueError('Une réponse de FAQ doit contenir entre 150 et 300 mots.')
        if not entry['reponse'].endswith(MECHANIC_END) or entry['reponse'].count(MECHANIC_END) != 1:
            raise ValueError(
                'La réponse doit se terminer par une seule phrase de conseil au mécanicien.'
            )
        if entry.get('niveau_risque') not in RISK_LEVELS:
            raise ValueError('Niveau de risque de FAQ générale invalide.')
        for name in ('mots_cles', 'variantes', 'ancrages', 'exclusions'):
            values = entry.get(name, [])
            if (
                not isinstance(values, list)
                or (name == 'mots_cles' and not values)
                or not all(isinstance(v, str) and v.strip() and len(v) < 250 for v in values)
            ):
                raise ValueError('Mots-clés ou variantes invalides.')
        text = ' '.join(
            [
                entry['question'],
                entry['reponse'],
                *entry['mots_cles'],
                *entry.get('variantes', []),
                *entry.get('ancrages', []),
                *entry.get('exclusions', []),
            ]
        )
        if re.search(r'\d|\b(?:ISO|SAE|ACEA|API|DOT|ECE|UNECE)\b', text):
            raise ValueError('Aucune valeur chiffrée ni norme technique dans la FAQ générale.')
        if entry['niveau_risque'] == 'élevé' and not re.search(
            'vérifi|contrôl|professionnel', entry['reponse']
        ):
            raise ValueError(
                'Une réponse à risque élevé doit prévoir une vérification professionnelle.'
            )
    return entries


@lru_cache(maxsize=4)
def _load(path, modified, size):
    return validate_entries(json.loads(Path(path).read_text(encoding='utf-8')))


def load_general_faq(path=None):
    path = Path(path or FAQ_PATH)
    stat = path.stat()
    return _load(str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def lookup(message):
    entries = load_general_faq()
    # Adaptateur de données seulement : TF-IDF, synonymes, score combiné et seuil
    # sont ceux de search_response ; aucun moteur de recherche supplémentaire.
    adapted = [
        dict(
            id=e['identifiant'],
            categorie=e['categorie'],
            question=e['question'],
            reponse=e['reponse'],
            mots_cles=e['mots_cles'],
            variantes=e.get('variantes', []),
            ancrages=e.get('ancrages', []),
            exclusions=e.get('exclusions', []),
            niveau_risque={'faible': 'faible', 'moyen': 'modere', 'élevé': 'eleve'}[
                e['niveau_risque']
            ],
        )
        for e in entries
    ]
    hit = search_response(message, entries=adapted, threshold=THRESHOLD)
    entry = next(
        (
            e
            for e in entries
            if hit.get('source') == 'faq' and e['identifiant'] == hit.get('faq_id')
        ),
        None,
    )
    vocabulary = set().union(*(tokens(' '.join([e['question'], *e['mots_cles']])) for e in entries))
    return dict(
        entry=entry,
        score=hit.get('score', 0.0),
        keyword_score=hit.get('keyword_score', 0.0),
        tfidf_score=hit.get('tfidf_score', 0.0),
        automotive_terms=bool(tokens(message) & vocabulary),
    )
