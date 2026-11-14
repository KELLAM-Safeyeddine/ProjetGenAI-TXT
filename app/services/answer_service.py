"""FAQ générale sans véhicule ; dialogue sur le manuel exact avec véhicule."""

import json
import logging
import re
import time

from app.services.chatbot_service import (
    MAX_MESSAGE_LENGTH,
    _guard,
    is_safety_topic,
    normalize,
    tokens,
)
from app.services.document_tools import TOOL_DEFINITIONS, DocumentTools
from app.services.llm_service import SYSTEM, choose_provider, complete
from app.services.manual_extraction import versions
from app.services.manual_policy import absent_message, canonical

logger = logging.getLogger('autohelp.answer')
UNAVAILABLE = "L'assistant est indisponible pour le moment."
NO_MANUAL_ANSWER = 'Je ne trouve pas d’indication suffisamment fiable pour répondre à ce point ; précisez l’équipement, le symptôme et les circonstances d’apparition.'
ROLE = (
    'Je peux vous aider sur l’automobile et son entretien ; posez-moi une question dans ce domaine.'
)
INJECTION = re.compile(
    r'ignore.{0,45}(instruction|consigne|regle|precedent)|system prompt|prompt system|change.{0,30}(role|format)|tu es maintenant|act as|(?:revele|donne|affiche|montre|imprime|expose).{0,35}(cle api|secret|prompt|token)|instruction system|jailbreak',
    re.I,
)
BANNED = re.compile(
    r'\b(openai|groq|llm|tfidf|api|fournisseur|rechercher_manuel|rechercher_web)\b|cle api|mode de fonctionnement|outil.{0,20}(utilise|appel)',
    re.I,
)
AUTO = set(
    'vidange huile moteur pneu frein batterie filtre refroidissement voyant bruit climatisation eclairage demarrage carburant consommation entretien revision distribution voiture vehicule tomobil circulation conduite routiere route permis assurance carte grise visite technique immatriculation covoiturage ecoconduite crit air stationnement securite accident embrayage boite vitesse roue capot recharge electrique airbag direction phare feu demarre parking courroie volant alternateur jauge ventilation courbe buee liquide gazole essence diesel essuie glace lave trafic klaxon siege ceinture plaquette liquide ralenti ecolabel pollution freinage declenche gonflage clim habitacle cycliste pieton vitesse autoroute'.split()
)
AUTO.update(
    'pedale pression flanc pneumatique amortisseur amortissement echappement radiateur vase retroviseur parebrise courroie embrayage echappement neiman butee suspension geomet rie parallelisme embrayage reservoir injecteur injection essuie turbo carrosserie coffre fusible bougie bougies'.split()
)
AUTO.update(
    'freine freiner freinage coussin gonflable clac claquement vibration aerateur optique consomme consommer'.split()
)
FORBIDDEN_LABELS = (
    'réponse générale, sans véhicule sélectionné',
    'sans véhicule, posez une question à la faq générale',
    'sélectionnez un véhicule dacia pour une réponse issue de son manuel pdf',
    'des repères documentés, jamais un diagnostic',
    'une réponse générale indique sa fiche faq',
    'applicabilité des passages',
    'le manuel source n’est pas en français ; cette explication en est une reformulation',
)


def has_forbidden_label(text):
    normalized = normalize(text)
    return any(normalize(label) in normalized for label in FORBIDDEN_LABELS) or bool(
        re.search(r'(?m)^\s*S[ée]curit[ée]\s*:', text)
    )


def in_scope(message):
    text = normalize(message)
    return bool((tokens(message) | set(text.split())) & AUTO) or any(
        t in text
        for t in (
            'burette',
            'pare brise',
            'crit air',
            'carte grise',
            'controle technique',
            'ecodriver',
            'decharge',
            'grince',
            'claquement',
        )
    )


def result(text, status='orientation', references=None, source_line=''):
    references = [{k: v for k, v in r.items() if k != 'contenu'} for r in (references or [])]
    sources = {r['source'] for r in references}
    return dict(
        reply=text,
        status=status,
        source=next(iter(sources))
        if len(sources) == 1
        else 'mixte'
        if sources
        else 'indisponible'
        if status == 'indisponible'
        else 'aucune',
        references=references,
        source_line=source_line,
    )


def safety_guidance(message):
    """Consignes dans la prose, sans bandeau et sans diagnostic de la cause."""
    words = tokens(message)
    text = normalize(message)
    if words & {'essence', 'carburant', 'diesel', 'gazole', 'gasoil'} and re.search(
        r'fuit|odeur', text
    ):
        return 'Immobilisez le véhicule, coupez le moteur et éloignez toute flamme ou source d’étincelles ; ne repartez pas avant un contrôle professionnel.'
    if words & {'frein', 'freine', 'plaquette', 'pedale'}:
        return 'Si le freinage est inhabituel, arrêtez-vous en sécurité et ne reprenez pas la route avant une vérification par un professionnel.'
    if 'pneu' in words:
        return 'Ne roulez pas avec un pneu endommagé ou dégonflé ; faites vérifier son état et le gonflage par un professionnel avant de repartir.'
    if 'direction' in words or re.search(r'volant.{0,20}(bloqu|dur)', text):
        return 'Si la direction devient anormale, arrêtez-vous en sécurité et faites-la vérifier par un professionnel avant de repartir.'
    if words & {'airbag', 'coussin'}:
        return 'N’intervenez pas sur un airbag ou son câblage ; en cas de dommage ou d’alerte, faites vérifier le système avant de reprendre la route.'
    if 'voyant' in words and 'huile' in words:
        return 'Arrêtez-vous en sécurité, coupez le moteur et ne redémarrez pas avant une vérification professionnelle de la lubrification.'
    if words & {'rouge', 'stop'}:
        return 'Arrêtez-vous en sécurité et ne reprenez pas la route avant que cette alerte ait été identifiée et vérifiée par un professionnel.'
    if words & {'rouge', 'stop', 'voyant', 'fuite'} or is_safety_topic(message):
        return 'Si une alerte inconnue ou une fuite compromet le fonctionnement, arrêtez le véhicule en sécurité et faites vérifier la situation avant de repartir.'
    return ''


def inline_safety(text, message):
    guidance = safety_guidance(message)
    # Une consigne déjà concrète ne reçoit pas une répétition du même avertissement.
    action = re.search(r'immobil|arr[eê]t|ne (?:roulez|poursuivez|reprenez|repartez)', text, re.I)
    check = re.search(r'v[eé]rifi|contr[oô]l|professionnel|assistance', text, re.I)
    return text.rstrip() + (' ' + guidance if guidance and not (action and check) else '')


def present_stored_reply(content, source, source_line):
    """Présentation des anciens messages sans modifier le texte ni les sources en base."""
    text = content
    prefix = 'Réponse générale, sans véhicule sélectionné.'
    if text.startswith(prefix):
        text = text[len(prefix) :].lstrip()
    text = text.replace(
        'Sécurité : ne reprenez pas la route avant une vérification par un professionnel.',
        'Ne reprenez pas la route avant une vérification par un professionnel.',
    )
    text = text.replace(
        'Sécurité : en cas de doute, immobilisez le véhicule en sécurité et consultez un professionnel ou un garage. Ces conseils ne remplacent pas un diagnostic.',
        'En cas de doute, immobilisez le véhicule en sécurité et faites-le vérifier par un professionnel.',
    )
    if source == 'faq':
        from app.services.general_faq_service import MECHANIC_END

        if source_line and text.rstrip().endswith(source_line):
            text = text.rstrip()[: -len(source_line)].rstrip()
        return text.removesuffix(MECHANIC_END).rstrip() + '\n\n' + MECHANIC_END, ''
    if source_line and not text.rstrip().endswith(source_line):
        text = text.rstrip() + '\n\n' + source_line
    return text, source_line


def orientation(message, vehicle=None):
    text = NO_MANUAL_ANSWER
    if vehicle and not vehicle.get('manual_reference'):
        text = absent_message(vehicle) + ' ' + text
    return result(inline_safety(text, message))


def unavailable(message):
    return result(inline_safety(UNAVAILABLE, message), 'indisponible')


def scoped_result(text, status, message):
    return result(inline_safety(text, message), status)


def answer_general(message, guard):
    """Aucun accès aux manuels, à l'historique documentaire ou au fournisseur."""
    from app.services.general_faq_service import MECHANIC_END, NO_MATCH, lookup

    normalized = normalize(message)

    def finish(text, status, refs=None, line='', **metadata):
        body = text.removesuffix(MECHANIC_END).rstrip()
        body = inline_safety(body, message)
        return {**result(body + '\n\n' + MECHANIC_END, status, refs, line), **metadata}

    if (
        INJECTION.search(normalized)
        or re.search(r'gsk_|sk-proj-', message, re.I)
        or (guard and guard['source'] == 'hors_sujet')
        or tokens(message) & {'politique', 'president', 'election'}
    ):
        return result(ROLE, 'hors_sujet')
    if normalized in {
        'bonjour',
        'salut',
        'merci',
        'merci beaucoup',
        'au revoir',
        'bonsoir',
        'a bientot',
    }:
        return result('Bonjour, comment puis-je vous aider pour votre véhicule ?', 'politesse')
    try:
        hit = lookup(message)
    except (OSError, ValueError, KeyError, TypeError):
        logger.warning('faq_generale event=unavailable')
        return finish(NO_MATCH, 'sans_reponse_generale')
    entry = hit['entry']
    if entry:
        text = entry['reponse']
        ref = dict(source='faq', faq_id=entry['identifiant'], categorie=entry['categorie'])
        return finish(
            text,
            'generale',
            [ref],
            faq_id=entry['identifiant'],
            score=hit['score'],
            keyword_score=hit['keyword_score'],
            tfidf_score=hit['tfidf_score'],
        )
    if guard and guard['source'] == 'clarification':
        return finish(guard['reply'], 'clarification', score=hit['score'])
    if not in_scope(message) and not hit['automotive_terms']:
        return result(ROLE, 'hors_sujet')
    return finish(NO_MATCH, 'sans_reponse_generale', score=hit['score'])


NUMBER = r'(?<!\w)\d+(?:[ \u202f\u00a0]\d{3})*(?:[.,]\d+)?'


def numeric_key(value):
    return re.sub(r'\s', '', value).replace(',', '.')


def _numbers(text):
    return {numeric_key(m.group()) for m in re.finditer(NUMBER, text)}


def _without_verified_vehicle_label(text, vehicle):
    """L'année de l'identité serveur n'est pas une valeur mécanique extraite.

    Seul le libellé complet exact est retiré ; nombres techniques et unités
    restent contrôlés, même s'ils sont égaux à l'année du véhicule.
    """
    if not vehicle:
        return text
    label = ' '.join(str(vehicle.get(k, '')) for k in ('marque', 'modele', 'annee'))
    return re.sub(r'\b' + re.escape(label) + r'\b', '', text, flags=re.I)


def _units(text):
    words = {
        'un': '1',
        'une': '1',
        'deux': '2',
        'trois': '3',
        'quatre': '4',
        'cinq': '5',
        'six': '6',
        'sept': '7',
        'huit': '8',
        'neuf': '9',
        'dix': '10',
    }
    pattern = (
        r'('
        + NUMBER
        + r'|\b(?:un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix))\s*(km/h|bars?|kpa|psi|litres?|ml|cl|l|km|mois|ans?|jours?|n[. ]?m|kg|g|%|°c)\b'
    )
    units = {
        'l': 'litre',
        'litres': 'litre',
        'bars': 'bar',
        'an': 'ans',
        'n.m': 'nm',
        'n m': 'nm',
        'jour': 'jours',
    }
    return {
        (words.get(value, numeric_key(value)), units.get(unit, unit))
        for value, unit in re.findall(pattern, text.casefold())
    }


def _finalize(data, message, vehicle, documents, task):
    if not isinstance(data, dict) or set(data) - {'reponse', 'type', 'passages_utilises'}:
        return orientation(message, vehicle)
    text = data.get('reponse')
    kind = data.get('type')
    used = data.get('passages_utilises', [])
    if (
        not isinstance(text, str)
        or not 1 <= len(text.strip()) <= 4000
        or kind
        not in {'reponse', 'generale', 'clarification', 'politesse', 'hors_sujet', 'orientation'}
    ):
        return orientation(message, vehicle)
    if not isinstance(used, list) or any(
        not isinstance(k, str) or k not in documents.seen for k in used
    ):
        return orientation(message, vehicle)
    if (
        BANNED.search(normalize(text))
        or INJECTION.search(normalize(text))
        or has_forbidden_label(text)
        or re.search(r'gsk_|sk-proj-|https?://|Source\s*:', text, re.I)
    ):
        return orientation(message, vehicle)
    refs = [documents.seen[k] for k in dict.fromkeys(used)]
    if task == 'automobile' and kind in {'generale', 'politesse', 'hors_sujet'}:
        return orientation(message, vehicle)
    if kind in {'reponse', 'generale'} and not refs:
        return orientation(message, vehicle)
    if any(ref['source'] != 'manuel' for ref in refs):
        return orientation(message, vehicle)
    if kind in {'orientation', 'politesse', 'hors_sujet', 'clarification'}:
        refs = []
    if task == 'clarification' and kind != 'clarification':
        return result(
            'Dans quelle partie du véhicule le symptôme se manifeste-t-il ?', 'clarification'
        )
    if text.count('?') > 1:
        return result('Quel symptôme précis observez-vous ?', 'clarification')
    precise = re.search(
        r'pression|quantite|combien|intervalle|frequence|couple|quand.{0,30}(vidange|remplacer)',
        normalize(message),
    )
    symptoms = tokens(message) & {
        'panne',
        'bruit',
        'grince',
        'fuite',
        'voyant',
        'vibration',
        'demarrage',
        'claquement',
    }
    if kind == 'generale' and (vehicle or precise or symptoms or is_safety_topic(message)):
        return orientation(message, vehicle)
    source_text = ' '.join(r['contenu'] for r in refs)
    if _numbers(_without_verified_vehicle_label(text, vehicle)) - _numbers(
        source_text
    ) or not _units(text) <= _units(source_text):
        return orientation(message, vehicle)
    lines = []
    for ref in refs:
        if ref['source'] == 'manuel':
            page_label = (
                f'page imprimée {ref["page_imprimee"]}, page PDF {ref["page_pdf"]}'
                if ref.get('page_imprimee') is not None
                else f'page imprimée non identifiée, page PDF {ref["page_pdf"]}'
            )
            line = f'manuel {ref["marque"]} {ref["modele"]} {ref["annee"]}, {page_label}, chapitre {ref["chapitre"]}, section {ref["section"]}'
            if ref.get('langue', 'fr') != 'fr':
                line += f', langue {ref["langue"]}'
            if ref.get('hebergeur') == 'ManualsLib.com':
                line += f' — hébergé sur ManualsLib.com, {ref["url_source"]}'
        else:
            line = f'Source : {ref["nom"]}, {ref["url"]}, consulté le {ref["date_consultation"]}'
        if line not in lines:
            lines.append(line)
    if kind == 'orientation':
        return orientation(message, vehicle)
    text = text.strip()
    # Seule la phrase de clôture informative est retirée ; les consignes de
    # vérification liées à un risque restent dans le contenu.
    text = re.sub(
        r'(?:\s|^)(?:Pour (?:plus|davantage) d[’\']informations,?\s*)?consultez un m[eé]canicien(?: pour (?:plus|davantage) d[’\']informations)?[.!]?\s*$',
        '',
        text,
        flags=re.I,
    ).rstrip()
    if not text:
        return orientation(message, vehicle)
    tagged = sorted({tag for ref in refs for tag in ref.get('versions', [])})
    if tagged:
        text += (
            ' Ces indications concernent '
            + ', '.join(tagged)
            + ' et ne s’appliquent pas nécessairement aux autres versions.'
        )
    if kind not in {'hors_sujet', 'politesse'}:
        text = inline_safety(text, message + ' ' + ' '.join(r.get('section', '') for r in refs))
    source_line = 'Source : ' + ' ; '.join(lines) if lines else ''
    return result(text + ('\n\n' + source_line if source_line else ''), kind, refs, source_line)


def answer(
    message,
    *,
    vehicle=None,
    history=None,
    summary='',
    manual_loader=None,
    web_loader=None,
    config=None,
    transport=None,
):
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
        return result('Écrivez une question de 1 à 1 000 caractères.', 'validation')
    normalized = normalize(message)
    guard = _guard(message)
    if vehicle is None:
        return answer_general(message, guard)
    if (
        INJECTION.search(normalized)
        or re.search(r'gsk_|sk-proj-', message, re.I)
        or (guard and guard['source'] == 'hors_sujet')
        or tokens(message) & {'politique', 'president', 'election'}
    ):
        return result(ROLE, 'hors_sujet')
    # Une indisponibilité documentaire connue ne dépend pas d'une API distante.
    if (
        vehicle
        and in_scope(message)
        and not (guard and guard['source'] == 'hors_sujet')
        and not INJECTION.search(normalized)
    ):
        ref = canonical(vehicle.get('marque'), vehicle.get('modele'), vehicle.get('annee'))
        if ref is None:
            return scoped_result(
                absent_message(vehicle)
                + ' Ce véhicule est hors du périmètre du chatbot. Sélectionnez une version Dacia disposant d’un manuel local identifié.',
                'hors_perimetre',
                message,
            )
        if not vehicle.get('manual_reference'):
            return scoped_result(absent_message(vehicle), 'manuel_absent', message)
    provider = choose_provider(config)
    if provider is None:
        logger.warning('model event=missing_configuration')
        return unavailable(message)
    if not provider.model or not provider.base_url:
        logger.warning('model provider=%s event=incomplete_configuration', provider.name)
        return unavailable(message)
    if (
        INJECTION.search(normalized)
        or re.search(r'gsk_|sk-proj-', message, re.I)
        or (guard and guard['source'] == 'hors_sujet')
        or tokens(message) & {'politique', 'president', 'election'}
    ):
        return result(ROLE, 'hors_sujet')
    history = history or []
    polite = normalized in {
        'bonjour',
        'salut',
        'merci',
        'merci beaucoup',
        'au revoir',
        'bonsoir',
        'a bientot',
    }
    contextual = bool(history) and any(
        in_scope(h['content']) for h in history if h['role'] == 'user'
    )
    if (
        not in_scope(message)
        and not polite
        and not contextual
        and not (guard and guard['source'] == 'clarification')
    ):
        return result(ROLE, 'hors_sujet')
    task = (
        'clarification'
        if guard and guard['source'] == 'clarification' and not contextual and not polite
        else 'politesse'
        if polite
        else 'automobile'
    )
    if not polite:
        if vehicle is not None and not canonical(
            vehicle.get('marque'), vehicle.get('modele'), vehicle.get('annee')
        ):
            return scoped_result(
                absent_message(vehicle)
                + ' Ce véhicule est hors du périmètre du chatbot. Sélectionnez une version Dacia disposant d’un manuel local identifié.',
                'hors_perimetre',
                message,
            )
        if vehicle is not None and not vehicle.get('manual_reference'):
            text = absent_message(vehicle)
            return scoped_result(text, 'manuel_absent', message)
    documents = DocumentTools(
        vehicle, (vehicle or {}).get('manual_reference'), manual_loader, web_loader
    )
    documents.original_query = message
    # La demande originale prime sur la motorisation enregistrée pour une question
    # explicitement comparative ; le modèle ne fournit aucun paramètre de version.
    explicit = set(versions(message))
    stored = set(documents.requested_versions)
    groups = ({'4x2', '4x4'}, {'GPL', 'Hybrid', 'Diesel', 'essence'})
    documents.requested_versions = sorted(
        set().union(*(explicit & g or stored & g for g in groups))
    )
    public_vehicle = (
        {k: vehicle.get(k) for k in ('marque', 'modele', 'annee', 'motorisation', 'kilometrage')}
        if vehicle
        else None
    )
    current = {
        'question': message,
        'vehicule': public_vehicle,
        'manuel_disponible': bool(documents.reference),
        'resume_ancien': summary[:900],
        'situation': task,
    }
    messages = [
        {'role': 'system', 'content': SYSTEM},
        *history[-10:],
        {'role': 'user', 'content': json.dumps(current, ensure_ascii=False)},
    ]
    definitions = TOOL_DEFINITIONS if task == 'automobile' else []
    deadline = time.monotonic() + 20
    next_tool = 'rechercher_manuel' if definitions else None
    for _ in range(4):
        choice = {'type': 'function', 'function': {'name': next_tool}} if next_tool else None
        response = complete(
            provider,
            messages,
            definitions if next_tool else [],
            transport=transport,
            deadline=deadline,
            tool_choice=choice,
        )
        if response is None:
            return unavailable(message)
        calls = response.get('tool_calls')
        if calls:
            if not next_tool or not isinstance(calls, list) or len(calls) > 2:
                return orientation(message, vehicle)
            safe_calls = []
            for call in calls:
                if not isinstance(call, dict) or not re.fullmatch(
                    r'[A-Za-z0-9_-]{1,128}', str(call.get('id', ''))
                ):
                    return orientation(message, vehicle)
                function = call.get('function', {})
                if not isinstance(function, dict):
                    return orientation(message, vehicle)
                safe_calls.append(
                    {
                        'id': call['id'],
                        'type': 'function',
                        'function': {
                            'name': str(function.get('name', ''))[:80],
                            'arguments': str(function.get('arguments', ''))[:2200],
                        },
                    }
                )
            messages.append({'role': 'assistant', 'content': None, 'tool_calls': safe_calls})
            for call in safe_calls:
                function = call['function']
                out = documents.dispatch(function['name'], function['arguments'])
                messages.append(
                    {
                        'role': 'tool',
                        'tool_call_id': call['id'],
                        'content': json.dumps(out, ensure_ascii=False),
                    }
                )
            if out.get('statut') == 'manuel_absent':
                return scoped_result(absent_message(vehicle), 'manuel_absent', message)
            next_tool = None
            continue
        try:
            content = response.get('content', '')
            if content.startswith('```'):
                content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content.strip())
            data = json.loads(content)
        except (ValueError, TypeError, AttributeError):
            return orientation(message, vehicle)
        final = _finalize(data, message, vehicle, documents, task)
        return final
    return orientation(message, vehicle)
