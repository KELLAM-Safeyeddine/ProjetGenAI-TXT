# Reprise des améliorations AutoHELP

Date de reprise : 14 novembre 2026. Source : propositions de l'équipe dans `improv (1).md`. Les tâches sont traitées et validées dans l'ordre ; une préparation documentaire ne vaut pas validation d'une fonctionnalité.

## Étape préalable : sauvegarde

Sauvegarde privée complète des deux dossiers, avant modification : `../sauvegardes/AutoHELP_avant_ameliorations_2026-11-14_13-11-53/AutoHELP_sauvegarde_complete.zip`. 24 654 fichiers vérifiés par SHA-256 ; 3 351 024 963 octets non compressés, 1 645 347 689 octets d'archive ; instantané SQLite supplémentaire, `quick_check : ok`. Le ZIP contient aussi environnements, Git, manuels et configuration privée : ne jamais le partager. Les copies intermédiaires restent dans ce dossier, leur nettoyage ayant été refusé automatiquement.

## P0-1 : historique et hygiène Git

Le dépôt préexistant était sans commit ; conserver son identité, travailler sur `codex/fiabilisation-autohelp`, créer un premier commit fidèle au socle présent et des commits distincts par tâche suivante. Ne pas publier de dépôt distant automatiquement.

Les exclusions couvrent configurations privées, bases et annexes SQLite, manuels PDF partout et sans distinction de casse, environnements/caches, clés, journaux, rapports et vidéos. Les métadonnées documentaires nécessaires sont conservées. `python scripts/audit_git.py` contrôle les objets indexés avant commit, même après nettoyage de la copie de travail. Résultats de tests et limites dans `recette.md`.

## P0-2 validé le 14 novembre : Docker

326 tests source ; 317 réussis/9 facultatifs ignorés dans deux campagnes Docker. Import Bigster, référence, santé et persistance vérifiés ; détails dans recette.md. Le plan exécuté était :

1. Vérifier la disponibilité réelle du moteur avec un délai borné ; ne pas assimiler présence du client et moteur opérationnel.
2. Réconcilier source et livraison : récupérer dans le source les adaptations d'infrastructure déjà validées de la copie (SQLite persistant, port 5000, santé et import lecture seule) sans modifier les réponses ou le formulaire.
3. Adapter le générateur pour conserver uniquement les huit notices autorisées dans `livraison/manuels/`, conformément à la décision explicite de l'équipe. Ne jamais versionner les PDF ni les copier dans l'image. Refuser l'écrasement de fichiers non gérés ou modifiés sans sauvegarde.
4. Régénérer et auditer : pas de `.env`, clé, base, cache ou donnée de compte ; huit PDF attendus et montés en lecture seule. Le `.env.example` reste vide.
5. Construire et démarrer depuis cette copie, vérifier accueil, `/health`, `/ready`, migrations, import d'un PDF autorisé, création CLI d'un administrateur éphémère et réponses sourcées. Employer un volume isolé pour la recette, pas les données privées existantes.
6. Lancer pytest dans le conteneur, sans fournisseur puis avec une configuration factice qui n'appelle aucun service réel ; vérifier persistance et absence de PDF/secrets dans l'image.
7. Consigner commandes, résultats réels, durées et éventuels blocages. Un moteur indisponible laisse P0-2 non validé ; ne pas revendiquer un démarrage Docker.

## Suivi des travaux suivants

| Priorité | Travail prévu | Dépendance ou limite |
| --- | --- | --- |
| P0-3 | Validé : 329 tests sur chaque moteur | Migrations PostgreSQL vérifiées ; instance isolée |
| P0-4 | Validé : quotas, verrouillage, 338 tests par moteur | Redis réel partagé et panne fermée vérifiés |
| P0-5 | Validé : sessions, cookies, CSP et ProxyFix explicite | 348 tests et navigateur mobile sans violation CSP |
| P0-6 | Validé : trois correctifs et audits runtime/dev sans avis connu | 348 tests sur chaque moteur |
| P1-7 | CI lint, tests, audit et image | Aucun secret ni PDF constructeur dans CI |
| P1-8 | Évaluation par manuel réel | Attentes et pages relues humainement, pas 100 % artificiel |
| P1-9 | Recherche hybride | Mesure préalable, adoption seulement si gain démontré |
| P1-10 | Revue admin des passages bloqués | Journal de validation et droits administrateur |
| P1-11 | Motorisation normalisée | Valeurs des manuels, compatibilité des anciens textes |
| P1-12 | Réinitialisation par administrateur | Sans email et sans divulgation publique de compte |
| P1-13 | Observabilité et disponibilité | Aucun contenu utilisateur ni secret dans les logs |
| P1-14 | Robustesse LLM | Budgets configurables, mesures réelles et tests d'injection |
| P1-15 | Retour utile/pas utile | Migration et export admin |
| P2-16 | Confidentialité, export et conservation | Relecture juridique ; aucune conformité proclamée sans validation |
| P2-17 | Rappels internes et compteur rapide | Pas de notification email/SMS |
| P2-18 | Conversations et accessibilité | Progression, gestion des conversations, mobile et clavier |
| P2-19 | Isolation de l'archive historique | Aucune suppression sans validation du groupe |
| P2-20 | Mesure de performance | Cache par worker, charge avec modèle factice |
| P2-21 | Sauvegarde et restauration PostgreSQL | Vérification réelle de restauration |
| P2-22 | Déploiement HTTPS | Hébergement et domaine à choisir par l'équipe |

Les règles FAQ sans véhicule, manuel exact avec véhicule, sécurité intégrée, CSRF, ORM, propriété et contrôle des références restent impératives. Les valeurs techniques et les sources ne sont jamais inventées.
