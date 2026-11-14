# Sources web autorisées — vérification du 17 octobre 2026

Ces dix URL précises ont été consultées sur leurs sites officiels le 17/10/2026. Le registre exécutable est `config/sources_fiables.json`. Service Public utilise désormais son adresse canonique `service-public.gouv.fr` (ancien domaine `service-public.fr`). La Sécurité routière est représentée par son observatoire officiel ONISR. Les cinq constructeurs correspondent exactement aux marques du catalogue. Aucun lien rencontré pendant l’import n’est suivi.

## Import local vérifié

9 pages / 78 passages importés dans la base locale le 17/10/2026 entre 18:51 et 18:53 UTC. La livraison ne contient ni cette base ni les textes extraits. Il faut relancer `flask indexer-sources-web` après installation. Ces résultats dépendent de l’accès des serveurs au moment de la commande.

| Source | URL vérifiée | Résultat local |
| --- | --- | --- |
| Dacia — notices | [https://www.user-manual.dacia.com/fr/notices](https://www.user-manual.dacia.com/fr/notices) | 1 passages |
| Renault Maroc | [https://www.renault.ma/](https://www.renault.ma/) | 4 passages |
| Hyundai Maroc | [https://www.hyundai.com/ma/fr](https://www.hyundai.com/ma/fr) | 4 passages |
| Peugeot Maroc | [https://www.peugeot.ma/nos-modeles/2008.html](https://www.peugeot.ma/nos-modeles/2008.html) | 14 passages |
| Volkswagen Maroc | [https://www.volkswagen.ma/fr/nos-modeles/Nouveau-caddy.html](https://www.volkswagen.ma/fr/nos-modeles/Nouveau-caddy.html) | 2 passages |
| ADEME | [https://agirpourlatransition.ademe.fr/particuliers/economiser/carburant/ecoconduite-solution-consommer-moins-carburant-limiter-emissions-co2?ept-name=NGC_Website&ept-publisher=NGC_](https://agirpourlatransition.ademe.fr/particuliers/economiser/carburant/ecoconduite-solution-consommer-moins-carburant-limiter-emissions-co2?ept-name=NGC_Website&ept-publisher=NGC_) | Non indexée : robots.txt inaccessible ou accès interdit ; aucun contournement |
| Sécurité routière — ONISR | [https://www.onisr.securite-routiere.gouv.fr/etudes-et-recherches/la-securite-routiere-dans-le-monde/international/eco-conduite-du-projet-serres-au-projet-europeen-ecodriver](https://www.onisr.securite-routiere.gouv.fr/etudes-et-recherches/la-securite-routiere-dans-le-monde/international/eco-conduite-du-projet-serres-au-projet-europeen-ecodriver) | 6 passages |
| Service Public | [https://www.service-public.gouv.fr/particuliers/vosdroits/F33371?successfulSubscription=true](https://www.service-public.gouv.fr/particuliers/vosdroits/F33371?successfulSubscription=true) | 26 passages |
| NARSA | [https://www.narsa-securiteroutiere.ma/fr/le-controle-technique-des-vehicules-une-mesure-indispensable/](https://www.narsa-securiteroutiere.ma/fr/le-controle-technique-des-vehicules-une-mesure-indispensable/) | 6 passages |
| ACAPS | [https://www.acaps.ma/fr/grand-public/biens/assurance-automobile](https://www.acaps.ma/fr/grand-public/biens/assurance-automobile) | 15 passages |

## Limites et contrôles

L’import lit robots.txt avant la page, espace les requêtes d’au moins deux secondes (davantage si Crawl-delay le demande), refuse les redirections et les pages non HTML, limite la taille et le délai, retire scripts/navigation/formulaires et conserve URL/titre/date/numéro. Le chat utilise seulement les passages des URL encore présentes dans le registre. Un import réussi remplace les anciens passages de la page ; une erreur conserve le dernier import autorisé et sa date. Une URL retirée est écartée immédiatement par le chat puis supprimée à l’import suivant. Les règles administratives françaises sont utilisables uniquement pour une question explicitement française ; les démarches marocaines restent distinctes.

Les pages constructeur sont des catalogues/notices : elles ne constituent pas un programme d’entretien pour toutes les versions. Les réponses chiffrées propres au véhicule demandent son manuel exact. Les définitions sont sélectionnées comme telles, afin de ne pas répondre à « à quoi sert Crit’Air ? » par un prix ni par une réponse sur le filtre à air. Le seuil conservateur peut encore manquer des formulations ; une relecture humaine reste nécessaire.

La consultation interactive et l’accès automatisé peuvent différer : la page ADEME est publiquement consultable mais ses robots n’ont pas autorisé cet import depuis cet environnement. Aucun texte de cette page n’a été inséré manuellement dans la base. Le journal détaillé reste local dans `instance/web-index.log`.

## Ajout du 18 octobre 2026 : ManualsLib

URL consultée : https://www.manualslib.com/ ; FAQ : https://www.manualslib.com/faq.html ; conditions : https://www.manualslib.com/terms.html. Bibliothèque indépendante ajoutée à la demande de l’équipe, sans la qualifier de constructeur officiel. Le registre compte maintenant **10 pages web indexables et 1 portail de manuels à consultation manuelle**.

L’article 17 des conditions interdit les accès automatisés. `acces_automatise: false` empêche l’indexeur de contacter ce site ; la recherche web refuse aussi d’anciens passages éventuellement présents. Les PDF obtenus par l’équipe avec les droits nécessaires peuvent être déclarés par leur page exacte et importés localement, avec contrôle de version et attribution « ManualsLib.com ». Aucun téléchargement automatique ni contournement. Aucun PDF nouveau n’a été récupéré pendant cet ajout.

La recherche a notamment trouvé une page « Renault CLIO 2020 » qui contient une fiche d’instructions de 11 pages, pas le manuel complet du propriétaire : elle n’est pas attribuée au véhicule Clio 2020 enregistré. Aucun changement de ses droits, de son manuel lié ou de sa disponibilité n’est déduit du seul titre d’un résultat.
