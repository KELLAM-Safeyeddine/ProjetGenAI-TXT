# Prototype de recherche, non activé

14 novembre 2026. BM25 local combiné au cosinus et aux mots-clés, sans dépendance supplémentaire. La pondération est un candidat de comparaison, pas un réglage adopté. Les filtres d’identité, de version et de réserves visuelles sont conservés. Le modèle et l’API ne disposent d’aucun paramètre pour choisir ce moteur.

```bash
flask comparer-recherche --partiel --rapport .work/comparaison_recherche.md
```

Sur le premier lot Bigster (jeu inchangé, empreinte b132b4d0d7dcb412420651e02129a25ee547e5c89f9b8fb049a870e12cdf040f) : TF-IDF 25/49 pages attendues retrouvées, candidat 32/49. Huit gains et une régression sur la question de batterie de traction bigster_2026_049. La présence d’une page ne garantit pas une réponse complète ou correcte.

Aucune activation en production : les autres attendus et la revue humaine doivent être complétés ; la régression et les faux positifs doivent être examinés. Aucun seuil ou question du jeu n’est modifié pour obtenir un meilleur score. La commande sans --partiel refuse de présenter un corpus incomplet comme validé. Le rapport de comparaison reste local, hors livraison.
