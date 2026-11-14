# 14 novembre 2026 — P1-11 : versions moteur documentées

Liste « Version indiquée dans le manuel » alimentée par les marqueurs de l’édition exacte, avec « Je ne sais pas ». Une version forgée provenant d’un autre modèle est refusée. Le champ de précision libre préserve les saisies historiques ; un choix explicite enregistre le marqueur canonique utilisé par le filtre existant. Catalogue/API et cascade année mettent à jour les options. 33 tests formulaire/catalogue réussis après adaptation du DOM de recette au nouveau sélecteur.

# 14 novembre 2026 — reprise globale et P1-10 : revue administrateur

La nouvelle demande « continue tous » autorise les tâches indépendantes pendant la préparation du benchmark ; elle ne valide pas les annotations à la place d’un humain et ne justifie pas l’adoption d’un moteur sans gain mesuré. Les huit PDF restent conservés dans la livraison. Sauvegarde vérifiée du code courant (147 fichiers) avant cette reprise, en complément de la sauvegarde complète privée initiale.

Page /admin/manuels : pagination des réserves actives, rendu PNG de l’édition exacte contrôlée par SHA-256, décision garder bloqué/lever/corriger, note obligatoire et journal avant/après. Un numéro de révision refuse les décisions concurrentes périmées. Les utilisateurs ordinaires ne peuvent ni voir le rendu ni décider. Aucune réserve levée automatiquement ; un réimport reste à revoir séparément. Migration f93a1b2c3d40. Deux tests ciblés passent (1,57 s), contrôlant droits, PDF changé et écrasement concurrent ; suite complète à la recette finale.

# 14 novembre 2026 — reprise P1-8 : premier lot annoté, corpus toujours en attente

Les cinquante questions Bigster ont des attendus reformulés à partir de la notice exacte, avec pages imprimées/PDF, chapitre, section, restrictions et preuves de lecture. Contrôles visuels ciblés pour les schémas, symboles et tableaux. Les questions, identités et empreintes PDF sont inchangées. Il s’agit d’annotations assistées à faire relire, pas de signatures humaines inventées ; 350 autres attendus restent à établir.

Correction du seul évaluateur : km/h n’est plus lu comme km ; décimales, unités usuelles et bornes de plages explicites sont conservées. Les cas sans information ne gonflent plus le rappel de pages. Le rapport inclut le SHA-256 du jeu et le nombre de revues humaines. Le corpus ne peut être déclaré prêt sans une revue humaine traçable, même avec quatre cents annotations assistées.

Mesure partielle : 25/49 pages attendues retrouvées dans le top trois (51,0 %), absence de passage pour le tarif local 1/1. Les vingt-quatre échecs sont conservés ; aucun seuil ni classement du moteur n’a été modifié. Génération réelle non mesurée. L’ordre strict reste respecté : tâches P1-9 et suivantes en attente de la validation du corpus. Résultats des tests et livraison dans recette.md.

# 14 novembre 2026 — P1-8 : outil d'évaluation, annotations à compléter

Ajout de flask evaluer-manuels et de 400 questions fixées (50 par notice). Seules les annotations vérifiées, liées au modèle/millésime et au SHA-256 exact, sont mesurées. Une page Bigster a été rendue et lue visuellement ; 1 cas évalué, page retrouvée, 399 brouillons sans attendus inventés. Ce n'est pas un taux global de qualité ; aucune génération réelle n'a été mesurée. Le mode modèle est facultatif et plafonné ; les rapports n'exposent ni secrets ni longs extraits.

Le CLI refuse une validation complète sans cinquante annotations par manuel et refuse les éditions/index absents. L'équipe confirme l'ordre strict : attendre les annotations, ne pas entamer recherche hybride ni autres tâches indépendantes. Les six tâches P0 et la préparation CI restent acquises. Guide : EVALUATION_MANUELS.md. Résultats finaux dans recette.md.

# 14 novembre 2026 — P1-7 : intégration continue

Ajout d'un workflow GitHub Actions sans secret : Ruff, audit Git/dépendances, construction Docker et matrice SQLite/PostgreSQL. Actions épinglées à leurs SHA officiels ; permissions lecture et délais bornés. Configuration Ruff locale explicite pour éviter les préférences globales du poste ; formatage/imports harmonisés, fixtures réexportées explicitement. Actionlint passe, 93 fichiers Python conformes, 348 tests sur chaque moteur après nettoyage. Workflow non encore exécuté à distance, publication du dépôt laissée au groupe.

# 14 novembre 2026 — P0-6 : audit des dépendances

Correction des trois paquets signalés : Flask 3.1.3, pytest 9.0.3, pypdf 6.21.4. Ajout de requirements-dev.txt avec pip-audit 2.10.1 et ruff 0.17.5, hors dépendances de production supplémentaires. Audit résolu sans avis connu sur 48 paquets runtime et 73 paquets dev ; aucun conflit pip ; 348 tests sur chaque moteur. Les rapports temporaires restent exclus de la livraison. Voir AUDIT_DEPENDANCES.md et recette.md.

# 14 novembre 2026 — P0-5 : sessions et proxy explicite

Durée de session huit heures sans rafraîchissement systématique ; cookies de session/reconnexion HttpOnly, SameSite=Lax et Secure en production. Conservation de CSP stricte, X-Content-Type-Options, protection contre les frames, Referrer-Policy et HSTS ; object-src none ajouté. ProxyFix ne fait confiance aux adresses/protocoles transférés que si PROXY_HOPS est explicitement renseigné ; hôte non transféré. Aucune confiance par défaut. 348 tests passent ; six routes et le chat mobile vérifiés dans un navigateur sans violation CSP.

# 14 novembre 2026 — P0-4 : limites et verrouillage

Flask-Limiter protège les POST connexion/inscription/chat, avec Redis partagé en Compose et stockage mémoire local. Verrouillage temporaire après cinq échecs sur un compte, connu ou inconnu, remise à zéro après succès, réponse française 429 et Retry-After. Le chat limite par compte ; les clés de compte et d'IP sont HMACisées. Une panne du stockage refuse temporairement la requête (503), sans désactiver les contrôles. Redis est obligatoire en production. Aucun changement des droits ou du contenu documentaire. 338 tests sur SQLite et PostgreSQL ; contrôle Redis réel partagé réussi.

# 14 novembre 2026 — P0-3 : recette PostgreSQL

Ajout d'un Compose de test isolé, d'une image cible tests avec Git/Node et d'un choix explicite AUTOHELP_TEST_DATABASE_URL pour la fixture principale. Le moteur par défaut reste SQLite ; une base PostgreSQL non dédiée est refusée avant création/suppression du schéma. Tous les tests passent sur les deux moteurs (329 chacun), migrations PostgreSQL également vérifiées. Aucun écart ORM métier trouvé. Commandes et durées dans recette.md.

# 14 novembre 2026 — P0-2 : livraison reproductible et Docker

Consolidation dans le source des adaptations de la livraison : SQLite persistant, port 5000, image Python 3.12 slim, Gunicorn non-root, /health sans base et /ready avec contrôle base, import --lecture-seule. Les huit PDF restent fournis hors image/Git selon la décision explicite de l'équipe.

Le générateur contrôle les identités/empreintes et le contenu des fichiers remplacés : une copie personnalisée n'est adoptée que si sa version exacte se trouve dans la sauvegarde ZIP. Les fichiers inconnus provoquent un refus avant écriture. Ajout d'un audit de paquet et d'une recette avec vrai PDF, administrateur CLI et transport factice, sans compte conservé. Aucun changement de logique des réponses ni des règles de sécurité.

Docker désormais disponible et réellement validé ; résultats complets, durées et neuf tests facultatifs ignorés dans recette.md. Prochaine tâche : environnement PostgreSQL de test isolé, même suite sur les deux moteurs.

# Changements AutoHELP

## 14 novembre 2026 — sauvegarde et P0-1 : versionnement initial

La reprise suit les améliorations proposées dans `improv (1).md`, une tâche à la fois. Avant modification, sauvegarde complète du projet source et de la livraison voisine : 24 654 fichiers vérifiés dans une archive ZIP privée, avec instantané SQLite cohérent et `quick_check` réussi. Les copies intermédiaires du processus de sauvegarde n'ont pas été nettoyées : action refusée par le contrôle automatique. Aucun original n'a été supprimé.

Le dépôt Git existait déjà, mais sans aucun commit et avec un index ancien partiellement préparé. Il est conservé et reçoit un historique initial sur une branche `codex/fiabilisation-autohelp`, sans publication distante. Le premier commit décrit l'état courant complet, pas une reconstruction artificielle des modifications antérieures.

`.gitignore` exclut maintenant toutes les extensions PDF, y compris majuscules, les configurations privées `.env.*`, clés, journaux, bases et fichiers annexes SQLite, environnements, caches, rapports générés et vidéos. README, manifeste et provenance des manuels restent versionnables. Le nouvel audit `scripts/audit_git.py` analyse les blobs de l'index Git, signale les chemins interdits et des signatures de secrets sans afficher leur contenu, et exige un `.env.example` vide. Des tests vérifient notamment un ajout forcé et le cas où le disque est nettoyé alors que l'ancienne clé reste indexée.

**Décision explicite de l'équipe :** conserver les huit PDF dans `livraison/manuels/`, contrairement à la proposition sans PDF du document. Ils restent privés, ignorés par Git et hors image. La copie SQLite/port 5000 n'est pas écrasée par l'ancien générateur ; son adaptation précède toute régénération. Aucune règle métier, sécurité automobile, CSRF, propriété, FAQ ou référence n'est modifiée par P0-1. Recette exacte et suite des travaux : `recette.md` et `AMELIORATIONS.md`.

## Historique — 18 octobre 2026

La demande du 18/10/2026 remplace explicitement les anciennes listes limitatives, le relais FAQ, « Je ne sais pas. » seul, l’absence de sources/détails dans ce cas et les règles d’utilisation sans clé. Le cahier des charges reste applicable aux points non remplacés : droits CA-12, comptes, carnet, français, ORM, CSRF, sorties échappées, absence de VIN/plaque et notifications. Les phases initiales étaient réalisées ; cette évolution conserve leur socle et nécessite une nouvelle recette.

## Formulaire libre et liaison des manuels

Datalists facultatives alimentées par le dataset, sans refus d’une marque ou combinaison inconnue. Lexus est acceptée. Marque/modèle nettoyés, 1 à 60 caractères ; année entière 1950 à année courante + 1 ; motorisation et compteur facultatifs. Aucune règle de forme supplémentaire. Compteur entier non négatif représentable sur 64 bits. Les sorties sont échappées, même si un nom contient du HTML.

La migration `e41ac907d256` rend ces champs facultatifs et ajoute `manual_reference`, un triplet canonique JSON. Correspondance unique normalisée : casse, accents et espaces ignorés, sans modifier la saisie. L’absence de manuel n’empêche pas l’enregistrement. Réimport : actualisation des liaisons ; recherche : nouvelle validation et filtrage exact.

## Dialogue LLM uniquement

`answer_service` n’importe ni ne consulte la FAQ ; ses 120 entrées, son import et son administration restent une archive explicitement signalée. `llm_service` concentre tous les appels externes. Priorité de configuration : OpenAI si sa clé existe, sinon Groq, sinon indisponibilité neutre. Modèles et URL proviennent exclusivement de l’environnement privé ; template vide. Une configuration incomplète ou une erreur distante ne donne aucun détail technique public.

Deux outils natifs en lecture seule : `rechercher_manuel(requete)` et `rechercher_web(requete)`. Le véhicule est fixé par l’API après contrôle de propriété ; aucun identifiant, table ou action d’écriture n’est accepté. Manuel d’abord ; si aucun résultat ou synthèse insuffisante, web autorisé ; sinon mécanicien avec indications à lui transmettre. Une question vague entraîne une seule demande de précision ; hors sujet, refus poli ; politesse et explication générale qualitative sans véhicule peuvent ne pas citer de source.

Les appels de fonctions et la synthèse JSON sont séparés pour compatibilité réelle avec Groq. Les résultats d’outils sont transmis comme données à la synthèse. Les références publiques sont construites par le serveur uniquement à partir des résultats du tour courant ; les nouveaux chiffres/unités et références inconnues sont rejetés. Les sujets de sécurité recommandent de ne pas rouler avant contrôle professionnel. Cet avertissement reste présent même si le fournisseur est indisponible ; les odeurs/fuites d’essence ou de gazole sont reconnues comme du carburant. Ces contrôles ne prouvent pas intégralement la fidélité sémantique : relecture automobile humaine indispensable.

Les dix pages exactes autorisées, vérifiées le 17/10/2026, figurent dans [SOURCES_WEB.md](SOURCES_WEB.md). Sans SEARCH_API_KEY, la recherche utilise l’index local construit par la CLI. Aucun adaptateur de moteur externe n’est implémenté. Un index local absent conduit à une orientation honnête, jamais à une source inventée. La livraison ne contient ni PDF ni index web.

## Mémoire et sécurité

Conversations persistantes et privées. Dix messages récents/5 500 caractères et résumé extractif de 900 caractères, calculés sur au plus 80 messages. Changement de véhicule : suppression du contexte précédent ; reprise de l’historique : sélection du dernier véhicule encore accessible. Les anciennes réponses FAQ sont exclues du contexte. Les données utilisateur/documents ne sont jamais des instructions privilégiées. Les arguments d’outils non autorisés sont rejetés et les clés sont retirées des contextes accidentels ; aucun corps distant ni clé n’est journalisé.

Délai de 5 secondes par appel, au plus deux tentatives sur 500/502/503/504, quatre tours et 20 secondes pour un dialogue ; contexte 28 000 caractères et sortie 1 200 jetons. Aucun modèle ni URL codé en dur. Les documents officiels OpenAI function calling, Groq tool use et modèles ont été consultés le 18/10/2026 ; `openai/gpt-oss-20b` est documenté pour les outils locaux et le JSON, sans appels parallèles. Aucune dépendance supplémentaire.

## Évaluation et limites

Les 78 formulations, identifiants, catégories et contextes sont conservés ; seules les attentes changent pour ce contrat sans FAQ. Les anciennes attentes FAQ sont archivées. La recette utilise un modèle factice et quatre pages fictives : le taux de conformité ne mesure pas la qualité d’un vrai modèle. Les orientations sur ce corpus réduit sont attendues lorsque les anciens contenus de FAQ ne sont plus disponibles. Résultats, orientations et limites : [recette.md](recette.md). Le rapport détaillé se régénère avec `flask evaluer-chatbot` et n’est pas livré.

Le projet local conserve ses manuels et sa clé privée, sans les copier dans la livraison. Le groupe doit importer ses PDF et sources web, configurer son fournisseur, relire des réponses réelles et valider les pages autorisées. HTTPS public reste à effectuer lorsqu’un hébergement sera choisi.

## Source complémentaire ManualsLib — 18 octobre 2026

À la demande de l’équipe, ajout de ManualsLib dans le registre. Exception explicite aux seules sources constructeur : bibliothèque indépendante, utilisée uniquement pour des manuels locaux vérifiés et autorisés. Les conditions consultées interdisent les accès automatisés : portail non aspiré, indexation automatique désactivée et anciens passages HTML exclus/purgés. Aucun nouveau PDF téléchargé. Le téléchargement automatique conserve sa liste de domaines constructeur.

L’import exige la page exacte du document ManualsLib, pas la racine ou un catalogue de produits. La recherche reste fixée à la référence du véhicule ; ses citations indiquent aussi l’hébergeur ManualsLib.com et l’URL exacte. Pas de commentaires utilisateur ou de fiche rapide assimilés à un manuel complet. Tests ajoutés : aucune requête vers le portail, exclusion/purge de cache, import et attribution d’un PDF fictif, rejet d’une provenance trop générale.

## Restriction PDF Dacia et extraction géométrique — 24 octobre 2026

La nouvelle demande remplace la recherche manuel puis web et les réponses générales sans source : le chatbot utilise uniquement les PDF actifs de huit versions Dacia (liste dans README et `manual_policy.py`). Les véhicules restent en saisie libre, mais les autres ne sont pas interrogeables. Le registre web n’est pas élargi ; son outil est retiré des définitions fournies au modèle et du chemin `/api/chat`.

Le manifeste conserve toutes ses entrées : huit actives, autres désactivées. Seul Bigster 2026 est prêt à importer ; les autres PDF présents historiquement restent conservés mais en attente de validation explicite. Migration `f82b650ca410` et champ `active` : archives conservées sans suppression et liaisons recalculées. Une sauvegarde SQLite préalable est gardée localement dans `.work/backups`.

Extraction pdfplumber géométrique : colonnes séparées, encadrés atomiques, tableaux avec en-têtes/cellules fusionnées, pagination PDF/imprimée, chapitre, section, marqueurs de version et renvois. Déhyphénation, retrait des flèches/en-têtes/pieds/numéros et signalement des pages incertaines. Les passages nécessitant un contrôle visuel ne peuvent fournir de réponse. Aucun OCR ni téléchargement supplémentaire. La version demandée est fixée côté serveur, indépendamment de la reformulation du modèle.

La recette utilise un extrait géométrique réel de deux pages du Bigster, des PDF fictifs et une intégration sur trois pages du PDF local ; aucun PDF complet n’est ajouté au dépôt/livraison. Les formulations du jeu de 78 questions restent inchangées ; seules les attentes de sélection/absence sont adaptées. Les résultats courants priment sur les recettes précédentes : voir `recette.md`.


## 24 octobre 2026 — formulaire limité aux huit versions Dacia

Cette demande remplace la saisie libre décrite dans les évolutions antérieures. Liste unique `manual_policy.VEHICLES`, partagée par le formulaire, sa validation serveur, le catalogue exposé et le chat : sept modèles et huit combinaisons, Sandero 2021/2026 distincts et Stepway 2026 seulement. Marque Dacia fixe, modèle/année en cascade, plus de datalists du catalogue marocain ; la motorisation reste facultative et libre.

POST hors liste refusé en HTTP 422, même en contournant le HTML. La graphie est canonisée après comparaison exacte normalisée. Les véhicules historiques restent conservés et consultables ; leur formulaire s’ouvre avec avertissement, sans modifier la base. Leur réenregistrement exige la liste actuelle. Commande en lecture seule `flask lister-vehicules-hors-liste`. Le chat ne propose que les véhicules autorisés du compte ; un ancien identifiant envoyé directement annonce le manuel absent, sans passage étranger. Aucun changement des règles de sécurité.


## 24 octobre 2026 — inventaire dynamique et diagnostic de l’assistant

Le périmètre fixe est remplacé par les PDF Dacia identifiés dans `MANUALS_DIR`. Scan récursif sans OCR ni réseau, confrontation modèle/couverture, année explicite ou preuve officielle liée à une empreinte, rejet motivé des identités inconnues et autres marques. `flask import-manuels` met à jour le manifeste ; `flask lister-manuels-dacia` distingue trouvés, indexés et rejetés. Les anciens passages et véhicules restent conservés. Formulaire et validation serveur partagent l’inventaire local, sans liste de modèles figée. Aucun nouveau PDF téléchargé.

47 fichiers trouvés : 8 Dacia indexés / 11 892 passages, 39 autres marques désactivées. Pagination chapitre.page ajoutée pour Sandero 2021. Recherche sans sommaire, chapitres d’alerte moins prioritaires pour une demande d’entretien ; seulement deux blocs Bigster vérifiés visuellement réintroduits, sans lever les réserves des autres blocs. Le contrat de synthèse restitue un contenu partiel utile. L’année du libellé véhicule vérifié n’est plus confondue avec une prescription technique ; tests négatifs conservant le rejet des chiffres et unités inventés.

Configuration privée locale fonctionnelle, appels fournisseur réussis : le défaut reproduit provenait de la recherche et de faux rejets de synthèse, sans erreur de clé/quota. Diagnostics de démarrage ajoutés sans secret. Aucun changement de CSRF, des droits, du registre web ni des avertissements. Détails et limites : `docs/DIAGNOSTIC_ASSISTANT.md`.


## Questions suggérées — 24 octobre 2026

Les trois boutons du chat proposent désormais : contrôle du niveau d’huile moteur, pression des pneus et précautions avant ouverture du capot. Ces formulations exactes ont été essayées avec le modèle configuré et le manuel Bigster 2026 : trois réponses documentaires avec références vérifiées. Les boutons continuent de remplir le champ sans envoyer automatiquement la question. La réponse dépend toujours du manuel du véhicule sélectionné.


## 24 octobre 2026 — rétablissement de la FAQ générale sans véhicule

**Annulation explicite :** la règle précédente « la FAQ est remplacée/désactivée dans toutes les réponses » est remplacée par : **sans véhicule, FAQ générale en priorité ; avec véhicule, manuel exact uniquement, sans remplacement par la FAQ**. Cette nouvelle demande prime sur les passages historiques de ce document et du plan qui excluaient toute FAQ.

Création de `data/faq_generale.json` : quarante fiches originales, identifiants uniques, douze catégories, risques faible/moyen/élevé, aucune marque, valeur chiffrée ou norme technique. L’ancienne FAQ de cent vingt entrées et sa table d’administration restent archivées et ne sont pas utilisées. Le nouveau fichier est lu directement ; aucun import SQL ni clé de modèle n’est nécessaire sans véhicule.

`general_faq_service` adapte les fiches au moteur existant `chatbot_service.search_response`, sans second moteur : normalisation, synonymes, TF-IDF et score combiné, seuil conservé à 0,45. Les réponses insuffisantes proposent de reformuler ou de sélectionner un véhicule. Les demandes de pression, huile, couple, capacité ou fusible restent générales, sans valeur inventée, avec invitation à choisir le véhicule. Aucun manuel, modèle ou numéro de page n’est cité dans ce parcours.

Étiquette « Réponse générale, sans véhicule sélectionné », source FAQ et identifiant conservés dans l’historique. Le sélecteur de véhicule est déplacé près du champ de question. Hors sujet : refus poli ; question vague : précision ; dangers : avertissement et contrôle professionnel. Authentification, propriété CA-12, CSRF, ORM, échappement, avertissements et contrôles des références de manuels sont conservés. Le registre web n’a pas changé et aucun appel web n’est ajouté.

Les formulations du jeu de soixante-dix-huit questions sont conservées. Seules les attentes sans véhicule changent, avec archivage des anciennes attentes ; l’évaluation vérifie aussi la fiche attendue, et pas seulement le statut. Résultats exacts, sujets non couverts et vérifications de contenu : [FAQ_GENERALE.md](FAQ_GENERALE.md) et [recette.md](recette.md).

Recette finale : **247 tests réussis en 62,96 s**, évaluation **78/78 comportements conformes** avec les mêmes questions. Aucun échec restant sur ce jeu ; portée et relecture humaine dans les rapports liés.


## 25 octobre 2026 — contenu détaillé, sans libellés ni bandeaux

Cette demande remplace explicitement le format du 24 octobre : aucun label « réponse générale » ni source FAQ affichée. Sans véhicule, recherche FAQ uniquement, réponse détaillée et une seule phrase finale vers un mécanicien. Avec véhicule, manuel exact uniquement, dernière ligne `Source` construite par le serveur et aucune clôture informative vers un mécanicien. Le contrôle professionnel lié à un risque reste dans le contenu ; aucun bandeau ni avertissement générique répété. Les cas sans document ne citent aucune référence inventée.

Zéro nouvelle fiche, quarante réécrites de 187 à 209 mots dans `reponse`, à la place de `reponse_courte`. Identifiants, catégories, risques, recherche TF-IDF, ancrages et seuil conservés. Aucun chiffre ou norme universels ajoutés. Le chargeur valide longueur et clôture. Les réponses de manuel développent seulement les faits présents dans les passages et leurs limites.

Le sélecteur n’est pas déplacé : il conserve son bloc près de la saisie. Son déplacement antérieur est consigné dans le présent historique et correspond à la demande de le proposer à côté de la question ; aucun commentaire supplémentaire et aucun commit Git disponible pour l’expliquer (`HEAD` absent, zéro commit). Proposition de conserver cet emplacement ; tout retour dans la colonne latérale attend la validation du groupe. Rapport : [FORMAT_REPONSES.md](FORMAT_REPONSES.md).

Bandeau de bas de chat, annonces de mode et avertissement générique suffixé retirés. Les consignes d’arrêt, de non-reprise, de contrôle et les interdictions de manipulation sont dans les fiches et les gardes adaptées au risque. La phrase générale du pied de page est masquée sur le chat. Aucune règle d’action de sécurité supprimée. CSRF, propriété CA-12, ORM, échappement et contrôles des références/valeurs préservés. Les anciens messages restent en base ; seule leur présentation change. Le navigateur ne duplique pas les sources. Aucun nouvel accès web ni changement du registre autorisé.

Répartition, fiches à relire, vérification factuelle et recette : [FORMAT_REPONSES.md](FORMAT_REPONSES.md) et [recette.md](recette.md).

Recette finale du format : **311 tests réussis en 209,41 s**, puis **106 contrôles ciblés réussis en 13,22 s** après renforcement de la consigne rouge/huile. Évaluation : **78/78** avec les questions inchangées. Réponse réelle du fournisseur et deux parcours HTTP vérifiés ; comptes temporaires supprimés. Voir les rapports liés pour la portée de ces résultats.

## 25 octobre 2026 — consolidation du plan d’implémentation

`PLAN_IMPLEMENTATION.md` est réécrit comme état courant cohérent : six phases, FAQ détaillée sans véhicule, manuel exact avec véhicule, inventaire Dacia dynamique, formats sans bandeaux, API, sécurité, recette, livraison et critères restant à valider. Les anciennes règles de saisie libre, relais web, FAQ désactivée et anciens résultats ne sont plus présentés comme actifs. Les huit identités et compteurs d’import du tableau sont repris du manifeste local ; aucun nouvel import ou comptage de base n’est revendiqué. Les résultats du 25 octobre sont cités comme dernière recette, sans nouvelle exécution de pytest pour cette modification documentaire. Les commandes d’import Docker respectent le montage web des PDF en lecture seule. Aucun comportement applicatif ni emplacement du sélecteur n’est modifié.
