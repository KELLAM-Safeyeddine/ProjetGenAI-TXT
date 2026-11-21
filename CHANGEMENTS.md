# Changements AutoHELP

Journal des décisions et des recettes : [docs/CHANGEMENTS.md](docs/CHANGEMENTS.md).

21 novembre 2026 : après confirmation du fichier opérateur privé, connexions Neon/Upstash vérifiées, migrations appliquées sur une base initialement vide et huit manuels importés (11 892 passages ; 671 réservés à la revue). Health/ready 200 et parcours HTTPS complet réussi, avec FAQ et réponse Bigster sourcée. Compte temporaire supprimé ; aucun secret ni donnée personnelle publié. Livraison inchangée.

21 novembre 2026 : correctifs Vercel réellement publiés (e7d5674/b733208). Accueil, pages publiques, health, CSS et JavaScript répondent 200 ; 431 tests réussis en 100,37 s. L'initialisation Neon et la recette authentifiée restent à terminer (`/ready` 503).

21 novembre 2026 : diagnostic réel du site Vercel : erreur 500, Flask absent au démarrage. Le manifeste TOML de configuration était prioritaire sur requirements.txt sans déclarer ses dépendances. Ajout des 48 dépendances identiques, mode uv sans empaquetage du source et contrôle d'imports au build. Aucune logique métier modifiée ; redéploiement et recette publique à vérifier.

21 novembre 2026 : le premier build Vercel échoue à 463,32 Mo contre 225 Mo et identifie une installation personnalisée désactivant l'optimisation. `installCommand: null` rétablit l'installation native ; le guide précise de désactiver l'override du tableau de bord. Huit notices et TF-IDF conservés. Résultat du nouveau build à constater.

21 novembre 2026 : préparation Vercel Hobby, avec Neon et Upstash existants. Entrée Flask, build des ressources CDN et vérification des huit PDF ; chemins temporaires et connexions SQL adaptés au serverless. Les données restent dans les services externes et les protections sont conservées. Déploiement public et taille finale du paquet à vérifier sur le compte.

20 novembre 2026 : préparation de Render gratuit avec PostgreSQL Neon et Redis TLS Upstash. Blueprint Python 3.12, démarrage Gunicorn limité à un worker, et outil d'administration depuis le PC via `.env.render` privé ; aucun import PDF au réveil, aucune suppression des protections. Déploiement public en attente des services du compte.

20 novembre 2026 : les huit notices PDF Dacia validées sont autorisées dans Git par exception explicite, avec contrôle de leur empreinte SHA-256 ; les autres PDF et les secrets restent exclus. Guide PythonAnywhere ajouté. Le lien de consultation du manuel page par page est retiré de l'assistant, sans modifier les réponses documentaires ni la route de consultation protégée.

18 novembre 2026 : préparation de la publication GitHub du source, avec sauvegarde préalable, contrôle des fichiers suivis et de l'historique à publier, et démarrage documenté depuis un clonage. Les fichiers privés, PDF, caches, bases, environnements et copies générées restent hors du dépôt ; aucune logique métier modifiée.

14 novembre 2026 : reprise des améliorations indépendantes jusqu'au paquet de production et à la sauvegarde/restauration, avec tests SQLite/PostgreSQL. Premier lot de cinquante annotations Bigster préparé ; corpus et revue humaine encore incomplets, prototype de recherche non activé. Voir le journal détaillé et docs/AMELIORATIONS.md pour les validations et les éléments externes restants.
