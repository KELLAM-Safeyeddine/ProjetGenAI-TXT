"""Met à jour les réponses livrées intactes et préserve les modifications administrateur."""
import hashlib,json
from pathlib import Path
FIELDS=('categorie','question','variantes','mots_cles','reponse','niveau_risque')

def fingerprint(entry,with_source=False):
    fields=FIELDS+('source',) if with_source else FIELDS
    return hashlib.sha256(json.dumps({k:entry[k] for k in fields},sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def synchronize(entries,preserve_legacy_deletions=False):
    from app import db
    from app.models import FAQ
    legacy=json.loads((Path(__file__).resolve().parents[2]/'data/faq_legacy_hashes.json').read_text(encoding='utf-8'))
    added=updated=preserved=0
    for entry in entries:
        row=db.session.scalar(db.select(FAQ).where(FAQ.slug==entry['slug'])) or db.session.scalar(db.select(FAQ).where(FAQ.question==entry['question']))
        if row is None:
            if preserve_legacy_deletions and entry['slug'] in legacy:
                preserved+=1
                continue
            row=FAQ();db.session.add(row);added+=1
        else:
            current=fingerprint(row.as_entry())
            intact=row.seed_hash==fingerprint(row.as_entry(),True) or (row.seed_hash is None and legacy.get(entry['slug'])==current)
            if not intact:
                preserved+=1
                continue
            updated+=1
        row.slug=entry['slug'];row.category=entry['categorie'];row.question=entry['question']
        row.variants=entry['variantes'];row.keywords=entry['mots_cles'];row.answer=entry['reponse']
        row.risk_level=entry['niveau_risque'];row.source=entry['source'];row.seed_hash=fingerprint(entry,True)
    db.session.commit()
    return added,updated,preserved
