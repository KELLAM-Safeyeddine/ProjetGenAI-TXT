"""Outils documentaires en lecture seule ; identité du véhicule fixée par le serveur."""
import json,re
from urllib.parse import urlsplit
from app.services.chatbot_service import _manual_words,normalize,THRESHOLD,FOCUS,_concepts
from app.services.manual_policy import canonical,absent_message,reference_key
from app.services.manual_extraction import versions

def manual_words(text):
    aliases={'charger':'recharge','recharger':'recharge','chargeur':'recharge','lubrifiant':'huile','temoin':'voyant','pneumatique':'pneu'}
    request_words={'precaution','conseil','methode','proceder','procedure','effectuer','realiser','page','section','chapitre','version'}
    return [aliases.get(w,w) for w in _manual_words(text) if w not in request_words and not w.isdecimal()]

TOOL_DEFINITIONS=[{'type':'function','function':{'name':name,'description':description,
    'parameters':{'type':'object','properties':{'requete':{'type':'string','description':'Question documentaire automobile précise.'}},'required':['requete'],'additionalProperties':False}}}
    for name,description in (
        ('rechercher_manuel','Consulter uniquement le PDF actif de la version Dacia fixée côté serveur. Aucun choix de véhicule, version ou page par le modèle.'),)]

class DocumentTools:
    def __init__(self,vehicle=None,manual_reference=None,manual_loader=None,web_loader=None):
        self.vehicle=vehicle
        expected=canonical(vehicle.get('marque'),vehicle.get('modele'),vehicle.get('annee')) if vehicle else None
        candidate=canonical(manual_reference.get('marque'),manual_reference.get('modele'),manual_reference.get('annee')) if manual_reference else None
        self.reference=candidate if expected and candidate and reference_key(*candidate.values())==reference_key(*expected.values()) else None
        self.requested_versions=versions((vehicle or {}).get('motorisation') or '')
        self.original_query=''
        self.manual_loader=manual_loader or (lambda:[])
        self.web_loader=web_loader or (lambda:([],[]))
        self.manual_consulted=False;self.web_consulted=False
        self.seen={};self.calls=[];self._manual=None;self._web=None

    def remember(self,prefix,passage):
        for identifier,old in self.seen.items():
            if old==passage:return dict(id=identifier,**passage)
        identifier=prefix+str(1+sum(k.startswith(prefix) for k in self.seen))
        self.seen[identifier]=passage
        return dict(id=identifier,**passage)

    def dispatch(self,name,arguments):
        if name!='rechercher_manuel':return {'statut':'refuse','erreur':'Action non autorisée : seuls les manuels du périmètre sont consultables.'}
        try:arguments=json.loads(arguments) if isinstance(arguments,str) else arguments
        except (ValueError,TypeError):return {'statut':'refuse','erreur':'Arguments invalides.'}
        if not isinstance(arguments,dict) or set(arguments)!={'requete'} or not isinstance(arguments['requete'],str) or not 1<=len(arguments['requete'].strip())<=1000:
            return {'statut':'refuse','erreur':'Seul le texte requete est autorisé ; aucun identifiant ni autre paramètre.'}
        self.calls.append(name)
        if name=='rechercher_web' and self.reference and not self.manual_consulted:
            return {'statut':'refuse','erreur':'Consultez le manuel du véhicule sélectionné avant le web.'}
        return self.rechercher_manuel(arguments['requete']) if name=='rechercher_manuel' else self.rechercher_web(arguments['requete'])

    def rechercher_manuel(self,requete):
        self.manual_consulted=True
        if self.vehicle is None:return {'statut':'aucun_vehicule','passages':[]}
        if not self.reference:return {'statut':'manuel_absent','message':absent_message(self.vehicle),'passages':[]}
        if self._manual is None:
            ref=self.reference
            self._manual=[p for p in self.manual_loader() if p.get('active',True) and reference_key(p['brand'],p['model'],p['year'])==reference_key(*ref.values())]
        rows=self._manual
        if not rows:return {'statut':'manuel_absent','message':absent_message(self.vehicle),'passages':[]}
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        identity_words=set(manual_words(f"{self.reference['marque']} {self.reference['modele']} {self.reference['annee']}"))
        # Les marqueurs mécaniques sont fixés à partir du message original et du
        # véhicule par le serveur, jamais par la requête reformulée du modèle.
        words=set(manual_words(requete))-identity_words-set(manual_words(' '.join(versions(requete))))
        if not words:return {'statut':'sans_passage','passages':[]}
        aliases={'huile':'oil','pneu':'tyre tire','pression':'pressure','batterie':'battery','frein':'brake','niveau':'level','filtre':'filter','moteur':'engine'}
        translated=set(w for token in words for w in aliases.get(token,'').split())
        documents=[' '.join([p.get('chapitre',''),p.get('section_parent',''),p['section'],p['contenu']]) for p in rows]
        try:
            vectorizer=TfidfVectorizer(tokenizer=manual_words,token_pattern=None,lowercase=False,sublinear_tf=True)
            matrix=vectorizer.fit_transform(documents)
            similarities=cosine_similarity(vectorizer.transform([' '.join(words|translated)]),matrix)[0]
        except ValueError:return {'statut':'sans_passage','passages':[]}
        ranked=[]
        alert_request=bool(re.search(r'alerte|avertisseur|voyant|temoin|reinitial|initialis|message|perte|crev|anomal',normalize(self.original_query or requete)))
        for row,document,cos in zip(rows,documents,similarities):
            if row.get('controle_visuel_requis'):continue
            # Un sommaire n'est pas une consigne et ne doit pas évincer son contenu.
            if 'sommaire' in normalize(row.get('chapitre','')+' '+row['section']) or len(re.findall(r'\.{4,}',row['contenu']))>=2:continue
            tags=set(row.get('versions',[]))
            requested=set(self.requested_versions)
            groups=({'4x2','4x4'},{'GPL','Hybrid','Diesel','essence'})
            if any(requested&g and tags&g and not (requested&tags&g) for g in groups):continue
            terms=set(manual_words(document))
            body_terms=set(manual_words(row['contenu']))
            if not (words|translated)&body_terms:continue
            if not (words&FOCUS)<=_concepts(row['section']+' '+row['contenu']):continue
            matched={w for w in words if w in terms or any(a in terms for a in aliases.get(w,'').split())}
            title=set(manual_words(row.get('section_parent','')+' '+row['section']))
            score=.55*float(cos)+.45*len(matched)/len(words)
            title_boost=.18*len(words&title)/len(words)
            # Une demande de pression ne demande pas nécessairement les témoins
            # ou messages de réinitialisation : ces chapitres restent accessibles
            # aux questions qui les visent, sans évincer la consigne d'entretien.
            alert_penalty=.45 if not alert_request and re.search(r'alerte|avertisseur|temoin|initialis|anomal',normalize(row.get('section_parent','')+' '+row['section'])) else 0
            if len(matched)>=min(2,len(words)) and score>=THRESHOLD:ranked.append((score+title_boost+(.25 if requested&tags else 0)-alert_penalty,row))
        found=[];size=0
        for _,row in sorted(ranked,key=lambda pair:pair[0],reverse=True)[:3]:
            if size+len(row['contenu'])>10000:continue
            size+=len(row['contenu'])
            passage=dict(source='manuel',marque=self.reference['marque'],modele=self.reference['modele'],annee=row['year'],
                page=row['page'],page_pdf=row['page'],page_imprimee=row.get('page_imprimee'),chapitre=row.get('chapitre',row['section']),
                section=row['section'],contenu=row['contenu'],langue=row.get('langue','fr'),versions=row.get('versions',[]),type_bloc=row.get('type_bloc','texte'))
            origin=row.get('source','')
            if urlsplit(origin).hostname in ('www.manualslib.com','manualslib.com'):
                passage.update(hebergeur='ManualsLib.com',url_source=origin)
            found.append(self.remember('M',passage))
        return {'statut':'trouve' if found else 'sans_passage','passages':found}

    def rechercher_web(self,requete):
        return {'statut':'refuse','passages':[],'erreur':'Manuels PDF uniquement ; aucune recherche web.'}
