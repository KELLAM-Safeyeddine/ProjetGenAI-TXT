# Évaluation des manuels réels

État au 14 novembre 2026 : outil disponible, **corpus non validé**. L'équipe demande de garder l'ordre strict et d'attendre les annotations avant les tâches suivantes. Aucun changement de moteur hybride n'est adopté.

## Ce qui existe

`tests/data/evaluation_manuels_reels.json` contient cinquante questions originales contextualisées par notice, soit quatre cents cas pour les huit identités Dacia. Les formulations sont fixées avant la mesure. Une annotation Bigster a été contrôlée par lecture visuelle assistée de la page PDF 336, imprimée 334 ; ce contrôle par Codex ne constitue pas une validation automobile professionnelle. Les trois cent quatre-vingt-dix-neuf autres cas sont explicitement `valide: false`, sans réponse ni page attendues inventées.

La première mesure retrouve la page attendue sur ce seul cas (1/1). Ce n'est ni un taux global de couverture, ni un score de qualité du modèle. Les métriques de génération n'ont pas été mesurées avec un vrai fournisseur.

## Annoter sans fabriquer la vérité terrain

1. Ouvrir la notice exacte et comparer son empreinte SHA-256 à `sha256_pdf`. Dans le source, les PDF sont sous data/manuels/ ; dans la livraison, sous manuels/. Ne pas prendre un autre modèle ou millésime.
2. Conserver la question. Trouver les pages indépendamment du classement du chatbot (sommaire, recherche du lecteur PDF), puis lire les pages complètes, schémas, notes et restrictions de version.
3. Remplir `attendu.type` avec `reponse` si la notice contient l'information ; écrire une réponse attendue reformulée, les pages PDF, pages imprimées et le chapitre. Une correction de pression n'est pas une pression recommandée.
4. Si plusieurs motorisations/versions sont distinguées, renseigner `vehicule.motorisation` et conserver les conditions applicables dans l'attendu. Ne pas généraliser les valeurs.
5. `attendu.valeurs` vaut null si l'exactitude numérique n'est pas évaluée ; sinon c'est la liste des valeurs et unités réellement relevées. Une liste vide signifie qu'aucune valeur technique n'est attendue. Ne jamais renseigner un chiffre supposé.
6. Pour une absence d'information, choisir `sans_information` seulement après examen des sections pertinentes, pas après un simple échec de recherche. Garder les pages attendues vides et expliquer la limite dans la réponse attendue.
7. Renseigner `verification.date`, `verification.par` (initiales/rôle suffisent) et `verification.methode`, puis marquer `valide: true` uniquement après relecture. Ne pas valider en masse les brouillons. Les sujets à risque demandent une relecture automobile professionnelle.

Exemple déjà contrôlé : Bigster 2026, question sur les conditions de lecture du niveau d'huile, page PDF 336/imprimée 334, chapitre Entretien. L'attendu reformule les conditions et la lecture à la jauge sans introduire d'intervalle ou de quantité. Utiliser ce format, sans recopier de long extrait protégé.

## Exécution locale, sans appel au modèle

```bash
flask --app run evaluer-manuels --partiel --rapport .work/rapport_manuels.md
```

Dans Docker :

```bash
docker compose exec web flask evaluer-manuels --partiel --rapport /app/instance/rapport_manuels.md
```

L'index doit être importé au préalable. La commande ne lit que les passages actifs de l'identité exacte et exige l'empreinte de l'édition annotée. Une édition absente ou modifiée est signalée, jamais remplacée. Les brouillons sont exclus des scores.

Sans `--partiel`, la commande retourne un échec explicite tant qu'au moins cinquante annotations par manuel ne sont pas vérifiées et évaluables. Ce refus évite de déclarer le benchmark complet sur un seul exemple. Le rapport reste produit pour identifier le travail restant.

## Génération réelle, facultative et limitée

```bash
flask --app run evaluer-manuels --avec-modele --limite 10 --partiel --rapport .work/rapport_generation.md
```

Cette option utilise la configuration privée et peut consommer le quota du fournisseur. Elle est désactivée par défaut. Seuls les cas validés et compatibles avec l'édition sont envoyés ; la limite borne les générations. Aucune clé, aucun compte et aucun long extrait ne figurent dans le rapport distribué. Les rapports temporaires sont exclus de la livraison.

## Mesures et limites

- Rappel top trois : une page attendue se trouve parmi les passages renvoyés ; pour une absence annotée, aucune page n'est attendue.
- Citation : références issues du contrôle serveur, page attendue et identité du véhicule. Pas de source inventée.
- Valeurs/unités : comparaison lexicale des valeurs annotées ; ne remplace pas une validation sémantique des conditions, variantes ou négations.
- Refus : absence de référence et comportement d'orientation pour les cas annotés sans information.

Les résultats sont séparés par véhicule. Un rapport de recherche seul n'évalue pas la reformulation d'un vrai modèle. Avant toute recherche hybride, compléter/revoir les annotations, figer le jeu, produire la référence initiale et comparer les mêmes questions sans les adapter aux réponses.
