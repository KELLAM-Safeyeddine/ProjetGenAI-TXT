# API actuelle

Sessions Flask-Login, CSRF pour chaque écriture (en-tête X-CSRFToken ou champ csrf_token), ORM et filtre propriétaire. Les identifiants étrangers répondent 404. JSON invalide/champs inconnus : 400 ; ressource publique absente : 404 ; session API expirée : 401 ; limite : 429 avec Retry-After ; panne de stockage des quotas : 503. Les messages restent du texte.

| Route | Usage |
| --- | --- |
| POST /api/chat | message obligatoire, conversation_id et vehicle_id facultatifs ; identité du véhicule fixée côté serveur |
| GET /api/conversations | 50 titres/aperçus, curseur before_id facultatif, next_before_id dans la réponse |
| GET /api/conversations/id/messages | 100 derniers messages dans l’ordre chronologique ; before_id pour les précédents ; next_before_id |
| PATCH /api/conversations/id | objet title, texte nettoyé de 1 à 80 caractères |
| DELETE /api/conversations/id | supprime la conversation, ses messages et retours |
| POST /api/messages/id/feedback | helpful booléen strict, comment facultatif de 1 000 caractères maximum ; seulement ses réponses assistant |
| GET /account/export | pièce jointe JSON des données du compte, sans secrets d’authentification |
| POST /vehicles/id/mileage | formulaire de compteur entier non négatif ; aucun recul par le raccourci |
| GET /admin/retours.csv | export privé, administrateur uniquement ; cellules neutralisées contre les formules |
| GET /admin/manuels | passages actifs, réserves par défaut, pagination |
| GET/POST /admin/manuels/id | relecture/correction, note et révision obligatoires ; administrateur uniquement |
| GET /admin/manuels/id/page.png | rendu du PDF exact vérifié par empreinte ; administrateur uniquement |
| GET /health | vivacité sans base, 200 |
| GET /ready | état base/index/configuration du fournisseur, 200 ou 503 ; pas d’appel payant |

POST /api/chat conserve reply, source, references, source_line, vehicle et status, et ajoute message_id pour le retour utilisateur. Les messages historiques exposent feedback (helpful/comment) lorsqu’il existe. Sans véhicule : FAQ générale locale uniquement ; avec véhicule : manuel exact uniquement. La dernière ligne Source du parcours documentaire est construite après vérification côté serveur. Aucun paramètre ne permet de changer de moteur, de véhicule par l’outil, de table ou de page.

X-Request-ID est généré par le serveur et sert à retrouver un événement technique sans exposer le contenu du message dans les logs. Les réponses privées sont no-store. Les formats textuels de réponse restent définis dans FORMAT_REPONSES.md.
