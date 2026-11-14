"""Modèle de recette déterministe : simule le protocole, pas une qualité de génération."""
import json
CONFIG={'GROQ_API_KEY':'cle-factice-tests','GROQ_MODEL':'simulation','GROQ_BASE_URL':'https://example.invalid/v1'}

def final(text,kind='reponse',ids=None):
    return {'content':json.dumps(dict(reponse=text,type=kind,passages_utilises=ids or []),ensure_ascii=False)}

def tool(name,query,extra=None):
    return {'tool_calls':[{'id':'call_test','type':'function','function':{'name':name,'arguments':json.dumps({'requete':query,**(extra or {})})}}]}

class FakeModel:
    def __init__(self):self.requests=[]
    def __call__(self,provider,payload,timeout):
        self.requests.append(payload)
        current=next(json.loads(m['content']) for m in reversed(payload['messages']) if m['role']=='user' and m['content'].startswith('{') and 'question' in json.loads(m['content']))
        question=current['question']
        if current['situation']=='clarification':return final('Dans quelle partie du véhicule le symptôme se manifeste-t-il ?','clarification')
        if current['situation']=='politesse':return final('Bonjour, je suis là pour vous aider avec votre véhicule.','politesse')
        forced=payload.get('tool_choice')
        if isinstance(forced,dict):return tool(forced['function']['name'],question)
        outputs=current.get('documents_consultes') or [json.loads(m['content']) for m in payload['messages'] if m['role']=='tool']
        if outputs:
            last=outputs[-1]
            if last.get('passages'):
                row=last['passages'][0]
                return final(row['contenu'],'reponse',[row['id']])
            return final('Les documents ne permettent pas une réponse fiable. Décrivez les symptômes à un mécanicien.','orientation')
        return tool('rechercher_manuel' if current['vehicule'] else 'rechercher_web',question)
