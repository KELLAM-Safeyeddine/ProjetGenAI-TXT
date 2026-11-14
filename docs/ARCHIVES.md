# Archives et plan de nettoyage

14 novembre 2026. Aucune suppression de données ni de l’ancien .venv n’est effectuée.

Les modèles faq, vehicle_catalog et web_passages sont définis dans app/legacy/models.py et réexportés pour compatibilité. Leurs imports CLI sont isolés dans app/legacy/commands.py ; Docker ne les exécute plus au démarrage. Les fonctions de normalisation/TF-IDF partagées avec la FAQ générale restent dans les services actifs. L’administration historique porte le libellé FAQ archivée. Aucun contenu de ces tables ne remplace un manuel ou la FAQ générale actuelle.

Avant toute suppression future :

1. Arrêter les écritures et disposer d’une sauvegarde complète privée testée.
2. Exporter avec `flask exporter-archives instance/archives/archives.jsonl.gz` : FAQ historique, catalogue, pages web et passages inactifs, via ORM et par lots. Le fichier doit rester privé ; les notices conservent leurs droits. La commande refuse tout écrasement et ne supprime rien.
3. Vérifier l’empreinte et relire/restaurer l’export dans une instance de recette ; relever les comptages de l’installation réelle, sans réutiliser un chiffre historique comme mesure actuelle.
4. Faire approuver par le groupe le périmètre exact et une migration de retrait. Conserver les migrations historiques nécessaires aux mises à niveau.
5. Pour .venv cassé, vérifier d’abord que .work/venv ou un nouvel environnement exécute les tests, relever son chemin absolu et obtenir la validation du groupe avant retrait. La sauvegarde complète initiale le contient.

Un réimport de manuels incrémente désormais la révision des passages existants, empêchant un formulaire admin ouvert avant l’import d’écraser ce nouvel état. Les anciennes décisions ne débloquent pas automatiquement une nouvelle extraction.
