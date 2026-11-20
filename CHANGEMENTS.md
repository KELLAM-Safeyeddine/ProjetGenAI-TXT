# Changements AutoHELP

Journal des décisions et des recettes : [docs/CHANGEMENTS.md](docs/CHANGEMENTS.md).

20 novembre 2026 : préparation de Render gratuit avec PostgreSQL Neon et Redis TLS Upstash. Blueprint Python 3.12, démarrage Gunicorn limité à un worker, et outil d'administration depuis le PC via `.env.render` privé ; aucun import PDF au réveil, aucune suppression des protections. Déploiement public en attente des services du compte.

20 novembre 2026 : les huit notices PDF Dacia validées sont autorisées dans Git par exception explicite, avec contrôle de leur empreinte SHA-256 ; les autres PDF et les secrets restent exclus. Guide PythonAnywhere ajouté. Le lien de consultation du manuel page par page est retiré de l'assistant, sans modifier les réponses documentaires ni la route de consultation protégée.

18 novembre 2026 : préparation de la publication GitHub du source, avec sauvegarde préalable, contrôle des fichiers suivis et de l'historique à publier, et démarrage documenté depuis un clonage. Les fichiers privés, PDF, caches, bases, environnements et copies générées restent hors du dépôt ; aucune logique métier modifiée.

14 novembre 2026 : reprise des améliorations indépendantes jusqu'au paquet de production et à la sauvegarde/restauration, avec tests SQLite/PostgreSQL. Premier lot de cinquante annotations Bigster préparé ; corpus et revue humaine encore incomplets, prototype de recherche non activé. Voir le journal détaillé et docs/AMELIORATIONS.md pour les validations et les éléments externes restants.
