"""Mémoire bornée, limitée au segment du véhicule courant ; aucun ancien passage transmis."""
import re

def vehicle_key(context):
    if not context:return None
    return (context.get('id'),context.get('marque'),context.get('modele'),context.get('annee'),context.get('motorisation'))

def build_history(messages,vehicle=None):
    current=vehicle_key(vehicle);segment=[]
    for item in reversed(messages):
        if vehicle_key(item.get('vehicle'))!=current:break
        # Les anciennes réponses factuelles restent visibles dans l'historique,
        # mais ne peuvent devenir des sources à la place du PDF actif de ce tour.
        if item.get('source') in {'faq','web','mixte','manuel'} and item['role']=='assistant':continue
        if item['role'] in ('user','assistant'):
            text=re.split(r'\nSource\s*:',item['content'],maxsplit=1)[0]
            segment.append({'role':item['role'],'content':text[:1200]})
    segment.reverse()
    recent=segment[-10:];old=segment[:-10]
    # Résumé extractif des seuls propos utilisateur, sans ancienne consigne mécanique.
    summary=' | '.join(m['content'][:140] for m in old if m['role']=='user')[-900:]
    total=0;bounded=[]
    for item in reversed(recent):
        if total+len(item['content'])>5500:break
        bounded.append(item);total+=len(item['content'])
    return list(reversed(bounded)),summary
