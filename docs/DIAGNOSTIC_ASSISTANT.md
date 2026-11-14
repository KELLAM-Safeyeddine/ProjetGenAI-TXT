# Inventaire Dacia et diagnostic de l’assistant — 24/10/2026

## État réellement vérifié

**47 PDF trouvés : 8 Dacia validés et importés, 39 PDF d’autres marques rejetés du périmètre. Aucun PDF Dacia trouvé n’a été rejeté. Les deux copies Sandero/Stepway 2026 ont le même contenu commun : huit fichiers et sept contenus PDF distincts.** Les fichiers exclus sont conservés. La liste des modèles n’est plus codée en dur : `manual_inventory.scan_manuals` fournit le catalogue partagé par le formulaire, la validation et le chat. `manual_policy` conserve seulement l’égalité exacte normalisée et la règle de marque Dacia.

| Marque | Modèle | Année | Pages PDF | Passages actifs | Bloqués pour contrôle visuel | Source revérifiée le 24/10/2026 |
| --- | --- | --- | --- | --- | --- | --- |
| Dacia | Bigster | 2026 | 430 | 1721 | 82 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/3819/pdf) |
| Dacia | Duster | 2026 | 440 | 1738 | 83 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4161/pdf) |
| Dacia | Jogger | 2026 | 422 | 1643 | 94 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4452/pdf) |
| Dacia | Logan | 2026 | 374 | 1448 | 91 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4630/pdf) |
| Dacia | Sandero Stepway | 2026 | 384 | 1486 | 97 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/2528/pdf) |
| Dacia | Sandero | 2021 | 402 | 1292 | 58 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4030/pdf) |
| Dacia | Sandero | 2026 | 384 | 1486 | 97 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/2528/pdf) |
| Dacia | Spring | 2026 | 286 | 1078 | 69 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/3692/pdf) |

Total : **11892 passages actifs, 11221 utilisables et 671 exclus de la recherche pour contrôle visuel**. **179851 anciens passages conservés inactifs.** La présence d’un index ne prouve pas une extraction parfaite de chaque tableau. Le journal `instance/manual-import.log` liste les pages à revoir. Les deux blocs de prose Bigster des pages PDF 355/356 ont été comparés aux images rendues ; leur levée de réserve est liée aux empreintes exactes du PDF et du bloc. Tous les autres blocs signalés restent bloqués.

La pagination Sandero 2021 est de type chapitre.page : par exemple PDF 198 → page imprimée **2.56**. Elle est conservée comme chaîne, sans appliquer le décalage Bigster. Trois passages de cette notice n’ont pas de pagination imprimée détectable ; ils sont annoncés comme non identifiés, jamais inventés. Pour Bigster, PDF 198 → page imprimée 196 reste validé.

## Reproduction avant modification

Application source en fonctionnement sur `http://127.0.0.1:5001`. Un compte temporaire a ajouté un Bigster 2026 et posé « Quelle est la pression des pneus ? ». L’API renvoyait HTTP 200, statut `orientation`, aucune référence et le message générique invitant à voir un mécanicien. Les comptes de recette ont ensuite été supprimés, sans modifier les comptes existants.

## Chaîne vérifiée et cause exacte

1. **Configuration : correcte sur ce poste.** Fournisseur Groq retenu (`openai/gpt-oss-20b`), clé et URL présentes. Aucun secret reproduit dans ce rapport. OpenAI garde la priorité si configuré. Les appels natifs et de synthèse ont réussi ; aucun timeout, quota ou rejet d’authentification n’a été observé lors de la reproduction.
2. **Import :** seul Bigster était actif (1 721 passages), alors que sept autres PDF Dacia étaient physiquement présents et encore interdits par les anciens indicateurs. Le scan les a confrontés aux couvertures et aux périodes des pages officielles, avec contrôle d’empreinte.
3. **Recherche : cause principale.** Un sommaire, des messages d’alerte et une table d’anomalies évincaient la consigne d’entretien. Les paragraphes utiles des pages PDF 355/356 étaient tous bloqués par la réserve globale liée à une illustration de l’étiquette. Les sommaires sont maintenant exclus ; les chapitres d’alerte sont moins prioritaires pour une demande d’entretien qui ne parle pas d’alerte. Les alertes restent consultables quand la question les concerne. Le seuil de pertinence et les filtres de version ne sont pas abaissés. La demande originale côté serveur fixe ce classement.
4. **Synthèse et contrôle :** le modèle classait une réponse partielle utile comme `orientation`, dont le texte est remplacé par le message de prudence. Le contrat explique maintenant qu’un emplacement et une méthode de vérification sourcés constituent une réponse utile, même sans valeur précise. Autre faux rejet constaté : l’année du libellé véhicule était interprétée comme un nombre technique non sourcé. Seul le libellé complet vérifié par le serveur est distingué ; des pressions/quantités/intervalles inventés, même égaux à l’année, sont toujours rejetés. Tests positifs et négatifs ajoutés.
5. **Affichage : correct.** L’API et l’historique renvoient les références vérifiées. Test réel dans le navigateur : réponse et lignes « Source » visibles, véhicule Bigster conservé à la reprise de l’historique, aucune erreur/alerte JavaScript enregistrée. Les champs et réponses passent toujours par l’échappement ou `textContent`.

## Résultat après correction

Même question, même version : statut **`reponse`**, source **`manuel`**, indication concrète de l’étiquette à lire et de la vérification à froid. Les pages imprimées **353/354**, PDF **355/356**, chapitre **Conseils pratiques**, section **PNEUMATIQUES**, sont citées par le serveur. Deux autres essais réels réussis : niveau d’huile Duster 2026 (pages imprimées 339/343/340) et Sandero 2021 (page imprimée 4.4, PDF 288). Chaque réponse utilise uniquement le modèle et l’année sélectionnés.

Aucune pression universelle n’est inventée ; une correction conditionnelle ne devient pas une pression de base. L’avertissement professionnel obligatoire est conservé.

## Tests et limites

- **221 tests pytest réussis en 95,08 secondes** : `.work/venv/Scripts/python.exe -m pytest -q`.
- Découverte d’un modèle fictif Lodgy 2020 hors de l’ancienne liste, création acceptée puis combinaison absente refusée ; PDF non identifiable signalé ; année de dossier seule refusée ; Sandero/Stepway distincts ; PDF retiré bloquant immédiatement la création et l’accès documentaire ; référence avec page imprimée ; numérique et identité ; sécurité des réserves de lecture.
- Évaluation conservant les questions : **78/78 comportements conformes**, avec modèle factice. Ce score ne mesure pas la qualité sémantique d’un modèle réel.
- Vérification réelle HTTP/LLM et navigateur : question pneus répondue et historique affiché avec références ; cascade Sandero 2021/2026 puis Duster 2026 vérifiée.
- Aucun PDF suivi par Git ; aucune modification du registre des sources web autorisées, aucun recours à la FAQ ou au web dans le dialogue. CSRF, propriété des véhicules/conversations et avertissements inchangés.
- Docker non relancé : moteur Docker Desktop arrêté. Le service web conserve le montage des PDF en lecture seule ; procédure d’import ponctuel ci-dessous.

## Actions restantes

Aucune clé à fournir pour le poste source actuel : sa configuration privée fonctionne. Sur un autre poste, renseigner un fournisseur, un modèle et une URL dans la configuration privée puis redémarrer ; sans configuration, les utilisateurs voient une indisponibilité neutre. Des diagnostics explicites sont maintenant inscrits dans les logs de démarrage, sans clé.

Relire un échantillon des réponses générées et les pages d’extraction signalées avant utilisation. Les 671 passages douteux restent bloqués. Les autres membres doivent fournir leurs copies autorisées des PDF et lancer l’import ; la livraison ne contient ni PDF ni base locale.

## Procédure d’ajout

Placer uniquement les PDF dont l’équipe dispose du droit d’usage dans `data/manuels/` (ou le dossier Flask `MANUALS_DIR`). Arborescence recommandée : `dacia/<modele>/<annee>/manuel.pdf`. Un nom explicite comme `Dacia_Lodgy_2020.pdf` est aussi accepté si la couverture confirme le modèle et la marque. Le scan est récursif, insensible à la casse de l’extension, sans réseau ni OCR.

L’année doit apparaître dans le nom du fichier ou la couverture ; **un dossier nommé 2026 ne suffit pas**. Lorsque le PDF ne porte aucune année, renseigner une preuve vérifiée `preuve_identite` : URL officielle exacte, URL PDF effectivement proposée, modèle/année, date de consultation, début/fin de validité et SHA-256 du fichier. L’équipe doit vérifier ces informations sur la page officielle ; le scan ne les invente pas et ne navigue pas automatiquement. Les huit preuves actuelles ont été revérifiées le 24/10/2026. Une période partielle ne garantit pas toutes les éditions ni tous les équipements d’une année.

Un PDF sans modèle/année identifiables, chiffré, corrompu, sans texte, en conflit avec la couverture ou en double pour le même triplet est rejeté avec une raison. Aucun manuel d’une autre marque n’est activé. Les modèles multiples d’une couverture ne créent pas automatiquement de nouveaux triplets : l’identité déclarée ou nommée doit être confirmée. Les copies Sandero et Stepway 2026 contiennent le même document commun, qui cite explicitement les deux modèles.

```bash
flask --app run lister-manuels-dacia
flask --app run import-manuels
flask --app run lister-manuels-dacia
```

`import-manuels` scanne tous les PDF, importe les Dacia identifiés et actualise atomiquement `data/manuels/index.json`. Les anciens indicateurs `pret_import` ne constituent plus une liste figée ; l’identification du fichier fait autorité. Les entrées rejetées/absentes restent désactivées et les anciens passages archivés, sans suppression. Le catalogue et les validations serveur sont recalculés depuis les fichiers identifiés ; sans PDF admissible, aucun véhicule ne peut être ajouté. Sans index actif correspondant au modèle ET à l’année, le chat annonce le manuel absent. Après remplacement d’un PDF, relancer l’import avant utilisation.

Sous Docker, le service web conserve son montage des PDF **en lecture seule**. L’import doit pouvoir mettre à jour le manifeste : utiliser un conteneur ponctuel avec le montage autorisé en écriture pour cette commande, puis consulter depuis le service web :

```bash
docker compose run --rm --volume ./data/manuels:/app/data/manuels:rw web flask import-manuels
docker compose exec web flask lister-manuels-dacia
```

Le compte du conteneur (UID 10001 sous Linux) doit pouvoir écrire le manifeste dans le dossier hôte. Aucun PDF n’est incorporé à Git, à l’image ou à la livraison ; les membres doivent placer leurs PDF sur leur poste. Le scan et le modèle ne téléchargent aucun manuel. Référence de la commande ponctuelle : [documentation Docker Compose](https://docs.docker.com/reference/cli/docker/compose/run/). Cette commande Docker n’a pas été exécutée lors de cette recette, le moteur étant arrêté.


## PDF conservés mais rejetés du périmètre

| Fichier local relatif à `data/manuels/` | Raison |
| --- | --- |
| `hyundai/elantra/2024/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/i10/2021/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/i10/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/i20/2022/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/i20/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/ioniq-5/2022/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/ioniq-5/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/ioniq-6/2024/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/ioniq-6/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/kona/2024/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/kona/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/santa-fe/2025/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/santa-fe/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/sonata/2024/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/sonata/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/tucson-plug-in-hybrid/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/tucson/2024/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `hyundai/tucson/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/2008/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/208/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/3008/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/308/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/408/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/5008/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/boxer/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/landtrek/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/partner/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `peugeot/rifter/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/arkana/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/austral/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/captur/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/clio/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/express/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/kangoo/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/kardian/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/megane-e-tech/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/nouvelle-clio/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/rafale/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
| `renault/renault-5/2026/manuel.pdf` | Marque déclarée non Dacia : hors périmètre. |
