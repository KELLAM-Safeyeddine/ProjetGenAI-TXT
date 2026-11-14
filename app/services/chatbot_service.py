"""Recherche locale FAQ/manuels : aucun import Flask, réseau ou modèle génératif."""
import json
import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path
from functools import lru_cache

FAQ_PATH = Path(__file__).resolve().parents[2] / 'data' / 'faq.json'
MAX_MESSAGE_LENGTH = 1000
THRESHOLD = 0.45  # Retenu sur le lot de calibration (19 cas), rapport reproductible.
SAFETY = "Sécurité : en cas de doute, immobilisez le véhicule en sécurité et consultez un professionnel ou un garage. Ces conseils ne remplacent pas un diagnostic."
FALLBACK = ("Je n'ai pas de réponse assez précise. Peux-tu préciser le symptôme et l'élément concerné ? "
            "Par exemple : pression des pneus, fréquence de vidange ou batterie déchargée. "
            "Pour un diagnostic, consulte un professionnel.")
STOP = set('a au aux avec ce ces comment dans de des du en est et faire faut il je la le les ma me mes mon ne on ou par pas peut peux pour pourquoi qu quand que quel quelle quelles quels qui se son sur un une voiture vehicule savoir dois combien ca ai as avez vous votre vos mes moi nous suis etre plus tres depuis apres avant encore bien cette cet cela meme bghit بغيت dyal dial ndir wach 3afak chno kifach imta rah kayn fiha li had wahed svp merci bonjour voudrais souhaite maintenant'.split())
ALIASES = {'tomobil':'voiture','tonobil':'voiture','frin':'frein','frins':'frein','freins':'frein',
 'vidanj':'vidange','vidanger':'vidange','vidanges':'vidange','lubrifiant':'huile',
 'temoin':'voyant','temoins':'voyant','pneumatique':'pneu','pneumatiques':'pneu','pneus':'pneu',
 'accu':'batterie','accumulateur':'batterie','accumulateurs':'batterie','baterie':'batterie',
 'clim':'climatisation','garniture':'plaquette','garnitures':'plaquette',
 'controle':'verifier','controler':'verifier','verification':'verifier','mesurer':'niveau',
 'gonflage':'pression','gonfler':'pression','froide':'froid','froids':'froid',
 'souci':'probleme','mochkil':'probleme','phare':'feu','phares':'feu',
 'chauffe':'chaud','refroidit':'froid','remplacement':'remplacer','renouveler':'remplacer',
 'grincement':'grince','grincent':'grince','sifflent':'siffle','sifflement':'siffle'}
STOP.update('fait font y ai peu presque toujours deja dernier derniere regarder prendre partir viens devient tourne souhaiterais connaitre possible normal cas'.split())
STOP.update('beaucoup reste restent uniquement chaque tous toute tout aussi souvent apparait apparaitre peut etre sont etes avoir etait quelle serait utile'.split())
ALIASES.update({'roue':'pneu','roues':'pneu','use':'usure','uses':'usure','usee':'usure','peniblement':'lent',
 'lentement':'lent','lancement':'demarrage','demarrer':'demarrage','demarre':'demarrage','spongieuse':'molle',
 'enfonce':'molle','feux':'feu','vends':'vente','vendre':'vente','changer':'remplacer','brulant':'chaud',
 'devisser':'ouvrir','perdent':'perte','decharger':'decharge','sale':'encrasse','sales':'encrasse'})
ALIASES.update({'ouverture':'ouvrir','fermeture':'fermer'})

def normalize(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', text))

def tokens(text):
    return set(_manual_words(text))

def load_faq():
    return json.loads(FAQ_PATH.read_text(encoding='utf-8'))

@lru_cache(maxsize=8)
def _faq_index(documents):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer=TfidfVectorizer(tokenizer=_manual_words,token_pattern=None,lowercase=False,sublinear_tf=True)
    return vectorizer,vectorizer.fit_transform(documents)

def _guard(message):
    if not isinstance(message,str) or not message.strip() or len(message)>MAX_MESSAGE_LENGTH:
        return dict(reply='Écris une question de 1 à 1 000 caractères.',source='validation',faq_id=None,score=0.0)
    words=tokens(message)
    if words & {'meteo','recette','tajine','pizza','cuisine','chocolat','gateau','cinema','film','football','foot','bitcoin','medicament','rhume','video'} or (words & {'temps','temp'} and words & {'demain','rabat','marrakech'}):
        return dict(reply="Je peux aider sur l’entretien automobile et les démarches courantes liées au véhicule au Maroc. Cette question est hors sujet ; posez-moi plutôt une question sur votre voiture.",source='hors_sujet',faq_id=None,score=0.0)
    vague=words <= {'huile','moteur','bruit','probleme','entretien','bizarre','truc','climatisation','voyant','allume','panne','marche','question'}
    if not words or vague:
        if 'bruit' in words:
            text="Pouvez-vous préciser où se situe le bruit (moteur, roue, habitacle), quand il apparaît (démarrage, freinage, virage) et à quelle vitesse ? Indiquez aussi s’il s’agit d’un grincement, d’un claquement ou d’une vibration."
        elif 'voyant' in words:
            text="Pouvez-vous préciser le pictogramme du voyant, sa couleur, s’il reste fixe ou clignote et le message affiché ? Un voyant rouge ou un changement de freinage demande un arrêt en sécurité et l’avis d’un garage."
        elif 'huile' in words:
            text="Pouvez-vous préciser si vous voulez vérifier le niveau, choisir l’huile, connaître l’échéance de vidange ou comprendre un voyant ?"
        else:
            text="Pouvez-vous préciser l’équipement concerné, le symptôme et le moment où il apparaît ? Par exemple : démarrage lent, climatisation sans froid ou bruit au freinage."
        return dict(reply=text,source='clarification',faq_id=None,score=0.0)
    return None

def search_response(message, entries=None, *, threshold=THRESHOLD):
    """Retourne métadonnées pour l'API ; entries permet d'injecter la FAQ de l'ORM."""
    guarded=_guard(message)
    if guarded:
        if isinstance(message,str) and is_safety_topic(message):guarded['reply']+='\n\n'+SAFETY
        return guarded
    entries = load_faq() if entries is None else entries
    query = tokens(message)
    vocabulary = set().union(*(tokens(' '.join([e['question'], *e['variantes'], *e['mots_cles']])) for e in entries)) if entries else set()
    query = {next(iter(get_close_matches(w, sorted(vocabulary), n=1, cutoff=0.86)), w) if w not in vocabulary else w for w in query}
    documents=[];owners=[]
    for index,e in enumerate(entries):
        for phrase in [e['question'],*e['variantes'],*e['mots_cles']]:
            if tokens(phrase):documents.append(phrase);owners.append(index)
    tfidf=[0.0]*len(entries)
    if documents:
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer,matrix=_faq_index(tuple(documents))
        for index,score in zip(owners,cosine_similarity(vectorizer.transform([' '.join(sorted(query))]),matrix)[0]):
            tfidf[index]=max(tfidf[index],float(score))
    ranked = []
    for index,entry in enumerate(entries):
        phrases = [entry['question'], *entry['variantes'], *entry['mots_cles']]
        score = 0.0
        for phrase in phrases:
            ref = tokens(phrase)
            if not ref or not query:
                continue
            overlap = len(query & ref)
            candidate = overlap / (len(query) * len(ref)) ** 0.5
            # Un mot isolé commun à plusieurs sujets ne constitue pas un diagnostic.
            if overlap == 1 and len(query) > 2:
                candidate *= 0.7
            score = max(score, candidate)
        anchors={'huile','pneu','batterie','frein','airbag','abs','esp','adblue','direction','carburant','climatisation','habitacle','capot'}
        focus=query & anchors
        reference=tokens(' '.join(phrases)+' '+entry['categorie'])
        penalty=.35 if focus and not focus<=reference else 1.0
        # Facultatif pour les fiches générales : un mot commun comme « moteur »
        # ne suffit pas à répondre sur l'huile ou un voyant précis.
        required=tokens(' '.join(entry.get('ancrages',[])))
        if required and not query&required:penalty=0.0
        excluded=tokens(' '.join(entry.get('exclusions',[])))
        if query&excluded:penalty=0.0
        ranked.append((penalty*(.55*score+.45*tfidf[index]),entry,score,tfidf[index]))
    ranked.sort(key=lambda row: row[0], reverse=True)
    # Des entrées proches de même catégorie peuvent donner des conseils compatibles.
    ambiguous = len(ranked)>1 and ranked[0][0]-ranked[1][0]<.025 and ranked[0][1]['categorie']!=ranked[1][1]['categorie']
    if not ranked or ranked[0][0] < threshold or ambiguous:
        result = {'reply': FALLBACK, 'source': 'clarification', 'faq_id': None}
    else:
        entry = ranked[0][1]
        result = {'reply': entry['reponse'], 'source': 'faq', 'faq_id': entry.get('slug') or entry.get('id'),
                  'knowledge_sources':[entry.get('source') or 'connaissance générale du domaine']}
        result['reply']+='\n\nSource FAQ : '+str(result['knowledge_sources'][0])+'.'
    result.update(score=round(ranked[0][0],4) if ranked else 0.0,
                  keyword_score=round(ranked[0][2],4) if ranked else 0.0,
                  tfidf_score=round(ranked[0][3],4) if ranked else 0.0)
    normalized = normalize(message)
    risky = is_safety_topic(normalized)
    if result['source'] == 'faq':
        risky = risky or ranked[0][1]['categorie'] in ('freinage', 'pneus') or ranked[0][1]['niveau_risque'] == 'eleve'
    if risky:
        result['reply'] += '\n\n' + SAFETY
    return result

def get_response(message):
    """Contrat public autonome demandé dans le plan : retourne un texte français."""
    return search_response(message)['reply']


NO_MANUAL = "Je n'ai pas encore le manuel de cette version de votre véhicule."
MANUAL_FALLBACK = ("Le manuel ne traite pas clairement cette question dans les passages retrouvés. "
                   "Peux-tu préciser l'équipement ou l'opération concernée ? Tu peux aussi consulter le manuel page par page.")


def is_safety_topic(text):
    words = normalize(text).split()
    return any(w.startswith(('frein', 'frin', 'pneu', 'plaquett', 'direction', 'airbag')) for w in words) or any(w in ('rouge', 'rouges', 'stop') for w in words) or (bool(set(words)&{'carburant','essence','diesel','gazole','gasoil'}) and any(w in words for w in ('fuite','fuit','odeur')))


def _manual_words(text):
    """Même normalisation et stop words que la FAQ, avec pluriels courants."""
    normalized=normalize(text)
    words=[ALIASES.get(w,w) for w in normalized.split()]
    if re.search(r'roule.*(?:presque pas|tres peu|rarement)|faible kilometrage',normalized):words+=['frequence','vidange']
    if 'voyant' in words and 'charge' in words:words+=['batterie']
    if 'gaz' in words and any(w.startswith('recharg') for w in words):words+=['climatisation']
    if 'filtre' in words and ('ventilation' in words or 'pollen' in words):words+=['habitacle']
    return [w[:-1] if len(w)>4 and w.endswith('s') and w not in ('gazoil','gazole','abs') else w for w in words if w not in STOP and len(w)>1]


def _section_key(section):
    # Les pages « Capot moteur (1/2) » et « (2/2) » constituent la même section.
    return ' '.join(word for word in _manual_words(section) if not word.isdecimal())


def _sentences(row):
    """Rattache un titre qui est en réalité le début d'une phrase coupée par le PDF."""
    def repair(text):return re.sub(r'([A-Za-zÀ-ÿ])[-\u00ad]\s+(?=[A-Za-zÀ-ÿ])',r'\1',text)
    text=repair(row['contenu'])
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if len(lines)>1 and normalize(lines[0])==normalize(repair(row['section'])):
        heading=lines.pop(0)
        fragment=re.search(r'\b(a|à|de|du|des|en|sur|avec|pour|par|le|la|les|un|une|doit|doivent|être|etre|est|sont)\s*$',heading,re.I)
        clause=re.match(r'^(avant|après|lors|en cas|au cas|pour |si |ne |il |une fois|attention|le contrôle|la pression|la lecture)',heading,re.I)
        clause=clause or (re.match(r'^(le|la|les|un|une)\b',heading,re.I) and re.search(r'\b(doit|doivent|fait|font|est|sont|peut|peuvent)\b',heading,re.I))
        if fragment or clause:lines[0]=heading+' '+lines[0]
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', '\n'.join(lines)) if len(s.strip())>=10]


FOCUS={'huile','pneu','batterie','frein','airbag','direction','capot','refroidissement','climatisation','filtre'}

def _concepts(text):
    equivalents={'oil':'huile','tyre':'pneu','tire':'pneu','brake':'frein','battery':'batterie',
                  'coolant':'refroidissement','hood':'capot','bonnet':'capot','filter':'filtre'}
    return {equivalents.get(w,w) for w in _manual_words(text)}


def _reformulate(text):
    """Reformulation déterministe prudente : conserver négations, unités et conditions.

    Pas de génération libre : seules de courtes phrases complètes sont retenues.
    Les tableaux/lignes trop longs restent consultables sur la page de référence.
    """
    text=re.sub(r'^\d{1,2}\s+(?=Capot moteur|Huile moteur|Niveaux|Pour |Liquide de |Pression des)','',text)
    text=re.sub(r'\bdu huile\b','d’huile',text)
    if re.match(r'^Vérifiez\b',text,re.I) and re.search(r'\bet\s+\w+ez\b',text,re.I):return text
    substitutions = ((r'^Vérifiez\b', 'Il faut vérifier'), (r'^Contrôlez\b', 'Le contrôle porte sur'),
                     (r'^Consultez\b', 'La référence à consulter est'), (r'^Utilisez\b', 'Le produit indiqué est'),
                     (r'^Ne dépassez pas\b', 'La limite à ne pas dépasser est'))
    for pattern, replacement in substitutions:
        if re.search(pattern, text, re.I):
            return re.sub(pattern, replacement, text, count=1, flags=re.I)
    return 'Indication du constructeur : ' + text[0].lower() + text[1:]


def repondre_depuis_manuel(message, marque, modele, annee, *, passages=None, motorisation=None, threshold=THRESHOLD):
    """Service indépendant ; l'adaptateur ORM injecte des dicts via « passages ».

    Filtrage défensif de la version même si le dépôt a déjà filtré. La fonction
    n'accède ni à Flask ni au disque/réseau ; utilisable avec tout dépôt de passages.
    """
    result = dict(reply='', source='manuel', references=[], status='clarification',score=0.0)
    rows = [p for p in (passages or []) if (p['brand'], p['model'], p['year']) == (marque, modele, annee)]
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
        result.update(reply='Écris une question de 1 à 1 000 caractères.', status='validation')
        return result
    if not rows:
        result.update(reply=NO_MANUAL, status='manuel_absent')
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        # Fenêtres de phrases pour éviter qu'une longue page dilue le score du sujet.
        units = []
        for row in rows:
            if _section_key(row['section']) in {'sommaire','index','table matiere','contents','table contents'}:
                continue
            for sentence in _sentences(row):units.append((row,sentence))
        page_words={}
        for row in rows:page_words.setdefault(row['page'],set()).update(_concepts(row['section']+' '+row['contenu']))
        focus=_concepts(message)&FOCUS
        vocabulary = set(w for _, sentence in units for w in _manual_words(sentence))
        query_words = [w for w in _manual_words(message) if w not in {'proceder','methode','procedure','effectuer','realiser'}]
        specific=[w for w in query_words if w not in {'verifier','moteur','procedure','effectuer','realiser','methode'}]
        if len(set(specific))>=2:query_words=specific
        if rows[0].get('langue', 'fr') != 'fr':
            # Lexique de recherche, sans prétendre traduire une consigne mécanique.
            aliases = {'pression':['pressure'], 'pneu':['tyre','tire'], 'batterie':['battery'],
                'huile':['oil'], 'niveau':['level'], 'moteur':['engine'], 'frein':['brake'],
                'vidange':['oil','change'], 'filtre':['filter'], 'liquide':['fluid'],
                'refroidissement':['coolant'], 'voyant':['warning'], 'recharge':['charging'],
                'charger':['charge'], 'froid':['cold'], 'controle':['check']}
            query_words = [alias for word in query_words for alias in
                ([a for a in aliases.get(word, []) if a in vocabulary] or [word])]
        query_words = [next(iter(get_close_matches(w, sorted(vocabulary), n=1, cutoff=.84)), w) if w not in vocabulary else w for w in query_words]
        query = ' '.join(query_words)
        # Un seul mot (« huile », « problème ») ne donne pas une intention suffisante.
        if len(set(query_words)) < 2 or not units or not vocabulary:
            result['reply'] = MANUAL_FALLBACK
        else:
            documents=tuple(sentence+' '+row['section'] for row,sentence in units)
            vectorizer,matrix=_faq_index(documents)
            cosine = cosine_similarity(vectorizer.transform([query]), matrix)[0]
            coverages=[len(set(query_words)&set(_manual_words(sentence+' '+row['section'])))/len(set(query_words)) for row,sentence in units]
            scores=[min(1.0,.65*float(score)+.35*coverage+.20*len(set(query_words)&set(_manual_words(row['section'])))/len(set(query_words))) if focus<=page_words[row['page']] else 0.0
                    for (row,sentence),score,coverage in zip(units,cosine,coverages)]
            ranked = sorted(range(len(units)), key=lambda i: float(scores[i]), reverse=True)
            best = ranked[0]
            # Couverture minimale : pas de réponse à « pression de ma pizza ».
            coverage = coverages[best]
            result.update(score=round(float(scores[best]),4),tfidf_score=round(float(cosine[best]),4),coverage=round(coverage,4))
            overlap=len(set(query_words)&set(_manual_words(units[best][1]+' '+units[best][0]['section'])))
            if float(scores[best]) < threshold or coverage < .6 or overlap < 2:
                result['reply'] = MANUAL_FALLBACK
            else:
                top = units[best][0]
                # Garder toute la section pertinente : valeurs alternatives et conditions
                # ne sont jamais supprimées en faveur d'une seule motorisation.
                selected = [p for p in rows if _section_key(p['section']) == _section_key(top['section'])
                    and focus<=page_words[p['page']]
                    and (top['section'] != 'Section non identifiée' or p['page'] == top['page'])]
                section_pages={p['page'] for p in rows if _section_key(p['section'])==_section_key(top['section'])}
                if len(section_pages)>6:selected=[p for p in selected if p['page']==top['page']]
                sentences = []
                sentence_pages = {}
                answer_status = 'reponse'
                for p in selected:
                    for sentence in _sentences(p):
                        sentence = sentence.strip()
                        if sentence and sentence != p['section'] and sentence not in sentences:
                            sentences.append(sentence)
                            sentence_pages[sentence] = p
                # Pour une section longue, restituer des repères qualitatifs complets.
                # Ne jamais sélectionner une seule valeur d'un tableau de variantes.
                if not sentences or sum(len(s) for s in sentences) > 700 or any(len(s) > 280 for s in sentences):
                    concise = [s for s in sentences if 25 <= len(s) <= 240 and not re.search(r'\d', s)
                        and re.match(r'^[A-ZÀ-Ÿ]', s) and re.search(r'[.!?]$', s)
                        and set(_manual_words(s)) & set(query_words)
                        and not re.match(r'^(consultez|reportez|voir|se reporter|refer to|see )',s,re.I)]
                    concise.sort(key=lambda s: len(set(_manual_words(s)) & set(query_words)), reverse=True)
                    if concise:
                        selected_pages={sentence_pages[s]['page'] for s in concise[:2]}
                        selected=[p for p in selected if p['page'] in selected_pages]
                        result['reply'] = 'Repères retrouvés dans la section :\n' + '\n'.join(
                            f"• {_reformulate(s)} (page {sentence_pages[s]['page']}, section {sentence_pages[s]['section']})" for s in concise[:2])
                        result['reply'] += '\nCes indications sont partielles ; les tableaux et conditions propres à la version restent à vérifier sur les pages citées.'
                    else:
                        answer_status = 'clarification'
                        result['reply'] = ('La section a été retrouvée, mais son tableau ou ses conditions ne permettent pas une reformulation fiable. '
                                           'Peux-tu préciser l’opération ou la variante concernée ? Le lecteur donne accès aux pages citées.')
                else:
                    concrete=[s for s in sentences if len(s)>=25 and not re.search(
                        r'^(consultez|reportez|voir|se reporter|refer to|see )|(?:consulter|reporter).*(?:manuel|document d.entretien|carnet)',s,re.I)]
                    if concrete:
                        result['reply'] = 'Voici les repères du manuel :\n' + '\n'.join(
                            f"• {_reformulate(s)} (page {sentence_pages[s]['page']}, section {sentence_pages[s]['section']})" for s in sentences)
                    else:
                        answer_status='clarification'
                        result['reply']='Le passage retrouvé renvoie à une autre documentation et ne donne pas directement la procédure ou la valeur demandée.'
                if motorisation:
                    result['reply'] += f'\nMotorisation enregistrée : {motorisation}.'
                    engine_mentions = {engine for engine in ('essence', 'diesel', 'hybride', 'electrique') if engine in normalize(' '.join(sentences))}
                    if engine_mentions:
                        if normalize(motorisation) in engine_mentions:
                            result['reply'] += ' La ligne portant ce nom de motorisation dans les pages citées est celle à comparer ; vérifie aussi la variante moteur et les conditions indiquées.'
                        else:
                            result['reply'] += ' La correspondance exacte avec les variantes moteur de cette page n’est pas établie ; aucune valeur ne doit être choisie par défaut.'
                    else:
                        result['reply'] += ' Le libellé enregistré ne permet pas à lui seul de confirmer un code moteur ou une variante ; conserve les conditions du manuel.'
                references = []
                seen = set()
                for p in selected:
                    if (p['page'], p['section']) in seen:
                        continue
                    seen.add((p['page'], p['section']))
                    references.append(dict(page=p['page'], section=p['section'], source=p['source'], marque=marque, modele=modele, annee=annee,
                        langue=p.get('langue','fr'), url_pdf=p.get('url_pdf'), periode=p.get('periode'), marche_document=p.get('marche_document')))
                    result['reply'] += f"\nSource : manuel {marque} {modele} {annee}, page {p['page']}, section {p['section']}."
                result.update(references=references, status=answer_status)
    if is_safety_topic(message) or any(is_safety_topic(r['section']) for r in result['references']):
        result['reply'] += '\n\n' + SAFETY
    if rows:
        metadata = rows[0]
        if metadata.get('langue','fr') != 'fr':
            language = {'en':'anglais','es':'espagnol','pt':'portugais'}.get(metadata['langue'],metadata['langue'])
            result['reply'] = (f'Le manuel disponible est en {language}. Les passages cités conservent leur langue d’origine ; '
                'aucune traduction automatique des consignes n’est effectuée.\n\n' + result['reply'])
        if metadata.get('periode') or metadata.get('marche_document'):
            result['reply'] += '\n\nNotice : ' + metadata.get('periode','période non précisée') + '. Marché du document : ' + metadata.get('marche_document','non précisé') + '. Vérifie la date de version, la motorisation et les équipements de ton véhicule ; l’année seule ne garantit pas leur correspondance.'
    return result


def respond(message, *, vehicle=None, passages=None, entries=None, threshold=THRESHOLD):
    """Politique publique : manuel exact, puis FAQ annoncée ; jamais de source inventée."""
    guarded=_guard(message)
    if guarded:
        if isinstance(message,str) and is_safety_topic(message):guarded['reply']+='\n\n'+SAFETY
        guarded.update(status=guarded['source'],references=[],manual_status='non_interroge')
        return guarded
    manual=None
    if vehicle:
        manual=repondre_depuis_manuel(message,vehicle['marque'],vehicle['modele'],vehicle['annee'],
            passages=passages,motorisation=vehicle.get('motorisation'),threshold=threshold)
        if manual['status']=='reponse':
            manual['manual_status']='pertinent'
            return manual
    general=search_response(message,entries,threshold=threshold)
    general.update(status=general['source'],references=[])
    if vehicle:
        absent=manual['status']=='manuel_absent'
        general['manual_status']='absent' if absent else 'sans_passage'
        if general['source']=='faq':
            prefix=(NO_MANUAL+' Voici une réponse générale : ' if absent else
                    'Le manuel de votre véhicule ne traite pas directement ce point dans les passages retrouvés. Voici une réponse générale : ')
            general['reply']=prefix+general['reply']
        elif absent:general['reply']=NO_MANUAL+'\n\n'+general['reply']
        matching=[p for p in (passages or []) if (p['brand'],p['model'],p['year'])==(vehicle['marque'],vehicle['modele'],vehicle['annee'])]
        if matching and matching[0].get('langue','fr')!='fr':
            general['reply']+='\n\nLe manuel disponible pour cette version est en '+{'en':'anglais'}.get(matching[0]['langue'],matching[0]['langue'])+' ; les informations générales ci-dessus proviennent de la FAQ.'
        # Une section partielle n'est jamais présentée comme la source de la FAQ.
        general['manual_score']=manual.get('score',0.0)
    else:
        general['manual_status']='non_selectionne'
        if general['source']=='faq':general['reply']='Réponse générale de la FAQ, non spécifique à votre véhicule.\n\n'+general['reply']
    return general
