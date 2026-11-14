# Audit des dépendances — 14 novembre 2026

| Paquet | Ancienne version | Version corrigée épinglée |
| --- | --- | --- |
| Flask | 3.1.2 | 3.1.3 |
| pytest | 8.4.2 | 9.0.3 |
| pypdf | 6.21.1 | 6.21.4 |

Audit initial : 14 signalements pour 12 identifiants uniques ; aucune exclusion d'avis. Après correction et résolution des dépendances : 48 paquets runtime et 73 paquets dev sans vulnérabilité connue. `pip check` réussit. Tests : 348 SQLite, 348 PostgreSQL, aucun ignoré avec les PDF locaux.

```bash
python -m pip install -r requirements-dev.txt
python -m pip_audit -r requirements.txt
python -m pip_audit -r requirements-dev.txt
python -m pip check
```

Rapports JSON de recette conservés uniquement dans .work/ ; pas de rapport temporaire, clé ou base dans la livraison. Les résultats portent sur les bases d'avis consultées à cette date et les dépendances Python résolues, pas sur tous les paquets système ni les vulnérabilités encore inconnues.

Fiches officielles vérifiées : [Flask](https://pypi.org/project/Flask/3.1.3/), [pytest](https://pypi.org/project/pytest/9.0.3/), [pypdf](https://pypi.org/project/pypdf/6.21.4/).


Contrôle intégré final du 14 novembre : audits résolus relancés, **48 runtime et 73 dev, zéro avis connu**, pip check sans conflit. Un premier essai dev a échoué sur une réponse PyPI au type de contenu invalide ; la relance complète a réussi, aucun paquet ni avis n'a été exclu. Suite actuelle : 402 tests sur chaque moteur, résultats dans recette.md.
