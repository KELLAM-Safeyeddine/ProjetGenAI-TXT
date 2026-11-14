"""Index local de pages exactes autorisées. Aucune navigation depuis le chat."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import json,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from app.services.chatbot_service import tokens,normalize,_faq_index,THRESHOLD

AGENT='AutoHELP-Indexer'
MAX_BYTES=3_000_000

def load_sources(path):
    rows=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(rows,list):raise ValueError('liste attendue')
    seen=set()
    for row in rows:
        url=row['url'];p=urlsplit(url)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment or p.port not in (None,443) or not p.path or url in seen:
            raise ValueError('URL précise HTTPS unique requise')
        if not all(row.get(k) for k in ('nom','date_verification','region','type')):raise ValueError('métadonnées manquantes')
        if 'acces_automatise' in row and type(row['acces_automatise']) is not bool:raise ValueError('acces_automatise doit être un booléen')
        datetime.strptime(row['date_verification'],'%Y-%m-%d');seen.add(url)
    return rows

def web_indexable(source):
    """Un portail de manuels autorisé n'autorise pas l'aspiration de ses pages."""
    return source.get('acces_automatise',True) and source.get('type')!='bibliotheque_manuels'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('redirection non autorisée')

def fetch(url):
    request=Request(url,headers={'User-Agent':AGENT,'Accept':'text/html,text/plain'})
    with build_opener(NoRedirect()).open(request,timeout=12) as response:
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('document trop volumineux')
        if response.geturl()!=url:raise ValueError('redirection non autorisée')
        mime=response.headers.get_content_type()
        encoding=response.headers.get_content_charset() or 'utf-8'
        return raw.decode(encoding,errors='replace'),mime

class VisibleText(HTMLParser):
    SKIP={'script','style','head','nav','header','footer','aside','form','noscript','svg','template','button'}
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self):
        super().__init__(convert_charrefs=True);self.stack=[];self.parts=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        if tag=='title':self.in_title=True
        hidden=any(k in ('hidden','aria-hidden') and v not in ('false',) for k,v in attrs)
        if tag not in self.VOID:self.stack.append((tag,tag in self.SKIP or hidden))
        if tag in ('p','div','li','br','h1','h2','h3','section'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
        if tag in ('p','div','li','h1','h2','h3'):self.parts.append('\n')
    def handle_data(self,data):
        if self.in_title:self.title.append(data)
        if not any(hidden for _,hidden in self.stack):self.parts.append(data)
    def extract(self):
        text='\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())
        return ' '.join(''.join(self.title).split())[:300],text

def chunks(text,size=750,overlap=90):
    start=0
    while start<len(text):
        end=min(start+size,len(text))
        if end<len(text):
            stop=max(text.rfind('. ',start+size//2,end),text.rfind('\n',start+size//2,end))
            if stop>start:end=stop+1
        part=text[start:end].strip()
        if len(part)>=80:yield part
        if end==len(text):break
        new_start=max(start+1,end-overlap)
        # Reprendre à une frontière de phrase évite une consigne tronquée.
        boundary=text.find('\n',new_start,end)
        start=boundary+1 if boundary!=-1 else end

def index_pages(sources,*,getter=fetch,sleep=time.sleep,clock=time.monotonic):
    """Robots lu avant chaque domaine ; redirections et erreurs ne sont pas contournées."""
    robots={};last=None;rows=[];journal=[]
    def get_spaced(url,delay=2):
        nonlocal last
        if last is not None:sleep(max(0,delay-(clock()-last)))
        try:return getter(url)
        finally:last=clock()
    for source in sources:
        if not web_indexable(source):
            journal.append(f"{source['url']} : non indexée (consultation manuelle ; import local de PDF autorisés uniquement).")
            continue
        url=source['url'];p=urlsplit(url);origin=f'{p.scheme}://{p.netloc}'
        if origin not in robots:
            parser=RobotFileParser(origin+'/robots.txt')
            try:
                text,_=get_spaced(origin+'/robots.txt');parser.parse(text.splitlines());robots[origin]=parser
            except HTTPError as error:
                if error.code==404:parser.parse([]);robots[origin]=parser
                else:robots[origin]=None
            except Exception:robots[origin]=None
        parser=robots[origin]
        if parser is None or not parser.can_fetch(AGENT,url):
            journal.append(f'{url} : non indexée (robots.txt inaccessible ou accès interdit).');continue
        try:
            text,mime=get_spaced(url,max(2,parser.crawl_delay(AGENT) or parser.crawl_delay('*') or 0))
            if mime!='text/html':raise ValueError('HTML attendu')
            html=VisibleText();html.feed(text);title,body=html.extract()
            if len(body)<100 or re.search(r'access denied|verify you are human|captcha|just a moment',body,re.I):raise ValueError('texte inaccessible ou insuffisant')
            passages=list(chunks(body))
            if not passages:raise ValueError('aucun texte exploitable')
            now=datetime.now(timezone.utc).isoformat(timespec='seconds')
            rows.extend(dict(url=url,site_name=source['nom'],title=title or source['nom'],consulted_at=now,
                position=i,content=content,region=source['region'],kind=source['type']) for i,content in enumerate(passages,1))
            journal.append(f'{url} : {len(passages)} passages, consultation {now}.')
        except Exception as error:
            # Le journal ne contient ni corps de réponse ni en-têtes privés.
            journal.append(f'{url} : non indexée ({"HTTP "+str(error.code) if isinstance(error,HTTPError) else type(error).__name__}).')
    return rows,journal

def search_web(message,passages,allowed,*,threshold=THRESHOLD):
    from sklearn.metrics.pairwise import cosine_similarity
    registry={r['url']:r for r in allowed if web_indexable(r)};original_query=tokens(message)
    query=original_query-{'quoi','sert','objectif','france','maroc'}
    definition=any(phrase in normalize(message) for phrase in ('quoi sert','qu est ce','quel est l objectif'))
    candidates=[]
    for row in passages:
        source=registry.get(row.get('url'))
        if source is None:continue
        if source['region']=='France' and source['type']=='reglementation' and not original_query&{'france','francai','crit','zfe'}:continue
        content=row['content']
        if len(query & tokens(content))<min(2,len(query)) or not query:continue
        candidates.append((row,source))
    if not candidates:return None
    # Comme pour la FAQ, comparer aussi les formulations courtes : un long bloc
    # de page ne doit pas diluer une définition exacte dans ses paragraphes voisins.
    documents=[];owners=[]
    for i,(row,_) in enumerate(candidates):
        for text in [row['content'],*re.split(r'(?<=[.!?])\s+|\n',row['content'])]:
            if len(tokens(text))>=3:documents.append(text);owners.append(i)
    if not documents:return None
    documents=tuple(documents)
    vectorizer,matrix=_faq_index(documents)
    similarity=cosine_similarity(vectorizer.transform([' '.join(sorted(query))]),matrix)[0]
    cosines=[0.0]*len(candidates)
    for owner,sim in zip(owners,similarity):cosines[owner]=max(cosines[owner],float(sim))
    scored=[]
    for (row,source),cos in zip(candidates,cosines):
        coverage=len(query&tokens(row['content']))/len(query)
        score=.55*float(cos)+.45*coverage
        if score>=threshold:scored.append((score,row,source))
    if not scored:return None
    for score,row,source in sorted(scored,key=lambda item:item[0],reverse=True):
        sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+|\n',row['content']) if len(s.split())>=6 and s.rstrip().endswith(('.','!','?')) and not s.rstrip().endswith('?')]
        if definition:sentences=[s for s in sentences if tokens(s)&{'permet','designe','objectif','consiste','sert'}]
        sentences=sorted(enumerate(sentences),key=lambda s:len(query&tokens(s[1])),reverse=True)[:3]
        # Extrait limité à 95 mots : pas de redistribution de pages entières.
        selected=[];count=0
        for _,sentence in sorted(sentences):
            n=len(sentence.split())
            if count+n<=95:selected.append(sentence);count+=n
        if not selected:continue
        text=' '.join(selected)
        if source['region']=='France' and source['type']=='reglementation':text='En France : '+text
        return dict(reply=text,source='web',references=[],score=score,site_name=source['nom'],url=row['url'])
    return None
