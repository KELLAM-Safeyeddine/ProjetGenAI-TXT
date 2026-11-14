# Sauvegarde et restauration PostgreSQL

Le service backup du Compose de production s’exécute après la santé du web (migrations terminées), avec les outils PostgreSQL de la même version majeure. Il lance pg_dump au format custom, contrôle la structure, renomme atomiquement le fichier terminé, écrit son SHA-256 puis applique la rotation. Délai par défaut : 86 400 secondes ; sept fichiers terminés conservés. BACKUP_INTERVAL_SECONDS accepte 60 à 604 800 ; BACKUP_KEEP accepte 2 à 365. Aucune clé dans l’image, mot de passe lu depuis un secret monté. Le volume backups contient des données privées : contrôler ses accès et prévoir une copie chiffrée hors machine selon la politique du responsable.

```bash
docker compose -f docker-compose.production.yml logs --tail 20 backup
docker compose -f docker-compose.production.yml exec backup python3 /usr/local/bin/autohelp-backup.py
docker compose -f docker-compose.production.yml exec backup ls /backups
```

Une sauvegarde manuelle ne doit pas écraser un fichier existant : les noms sont uniques. Les erreurs ne publient ni mot de passe ni diagnostic distant privé. Vérifier régulièrement succès, espace disque et rotation ; une sauvegarde sur le même disque ne protège pas contre sa perte.

## Restaurer dans une nouvelle base de recette

N’utiliser que les sauvegardes privées de confiance. La commande vérifie l’empreinte avant tout accès de création, refuse le nom de la base active et exige un nouveau nom terminé par _restore_test. Elle ne détruit ni remplace une base existante.

```bash
docker compose -f docker-compose.production.yml exec backup python3 /usr/local/bin/autohelp-backup.py --restore /backups/<fichier>.dump --database autohelp_restore_test
docker compose -f docker-compose.production.yml exec -e DATABASE_URL=postgresql+psycopg://autohelp@db:5432/autohelp_restore_test web flask db check
```

Comparer comptes, véhicules, entretiens, conversations, messages, retours et index à l’instantané attendu. Vérifier la reconnexion et les séquences d’identifiants avant toute décision de bascule. Une restauration de production exige un créneau de maintenance, une sauvegarde de l’état courant et une modification explicite de configuration ; ce script ne fait aucune bascule automatique.

## Recette réellement exécutée le 14 novembre 2026

Sur un projet Docker isolé : import réel Bigster, données de recette uniquement, sauvegarde et restauration dans autohelp_qa_restore_test. Empreinte canonique ORM identique avant/après sur sept tables : users 2, vehicles 1, maintenance 1, conversations 1, messages 1, feedback 1, manuel_passages 1 721. Les deux comptes sont des fixtures temporaires de recette ; aucune donnée privée existante copiée. Contrôle du SHA-256 du dump réussi. Six tests vérifient également rotation bornée, conservation des fichiers étrangers, chemins et refus d’une empreinte modifiée/base interdite. La recette ne prouve pas la restauration de tous les futurs volumes ou une rétention juridique approuvée.


Complément de recette : une nouvelle sauvegarde a été restaurée dans une autre base isolée neuve. Les **onze tables ORM** ont été comparées intégralement par empreintes canoniques : toutes identiques, y compris les tables d'archives et de revue. Sur la base restaurée : vérification Alembic sans écart, connexion avec le mot de passe de la fixture (HTTPS/CSRF actifs), accès au tableau de bord et à la conversation conservée, puis insertion annulée confirmant la progression de la séquence users. La fixture ajoutée au projet de recette a été retirée ; aucune donnée réelle n'a été copiée ni restaurée dans la base active. Les bases et sauvegardes de recette restent hors livraison.
