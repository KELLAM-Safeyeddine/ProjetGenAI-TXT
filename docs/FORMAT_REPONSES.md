# Format des réponses et contenu de la FAQ — 25 octobre 2026

## Emplacement du sélecteur : constat avant modification

La section « rétablissement de la FAQ générale sans véhicule » du 24 octobre dans [CHANGEMENTS.md](CHANGEMENTS.md) consigne le déplacement près du champ de question. [PLAN_IMPLEMENTATION.md](PLAN_IMPLEMENTATION.md) indique que le sélecteur accompagne la saisie. Le README décrivait la sélection à cet emplacement et les deux parcours. La demande antérieure du groupe était explicitement : « Proposer le sélecteur de véhicule à côté de la question ». Cela explique la modification réalisée ; aucun autre motif de conception ne doit être supposé.

Les recherches dans les commentaires des routes, du template et de `chat.js` n’ont fourni aucune justification supplémentaire. `git log --all --` sur ces fichiers n’a retourné aucun commit ; `git rev-parse --verify HEAD` échoue et `git rev-list --all --count` donne zéro. Plusieurs fichiers sont dans l’index ou non suivis, mais cela ne constitue pas un historique de commits. Il est impossible de citer un auteur, une date de commit ou un diff historique validé.

**Proposition : conserver le sélecteur près de la question**, avant les suggestions et la zone de saisie, afin de respecter cette demande antérieure. Son emplacement et son ordre dans le DOM n’ont pas été modifiés pendant cette évolution. Le texte de l’option vide devient simplement « Aucun véhicule ». Un retour dans la colonne latérale reste soumis à la validation du groupe ; il n’est pas réalisé.

## Règle courante

Sans véhicule : recherche locale dans la FAQ générale uniquement, sans modèle distant, manuel ou web. Une réponse utile explique le sujet, les possibilités sans diagnostic, les gestes autorisés, les signes à observer et les erreurs à éviter. Elle se termine une seule fois par « Pour plus d’informations, consultez un mécanicien. ». Aucun préfixe de mode, aucune ligne de source FAQ et aucun bandeau ne sont affichés. Les identifiants et scores restent des métadonnées API, pas du texte ajouté dans l’interface.

Avec véhicule : recherche du manuel exact, toujours après contrôle de propriété. Aucun recours à la FAQ. La synthèse développe uniquement les informations effectivement présentes dans les passages, sans inventer des étapes pour atteindre une longueur. Elle ne reçoit aucune phrase finale générique vers un mécanicien. Les consignes de contrôle professionnel liées à un danger restent dans le contenu ; elles ne sont pas une formule de clôture informative.

La dernière ligne d’une réponse documentaire est construite côté serveur :

```text
Source : manuel Dacia Bigster 2026, page imprimée 196, page PDF 198, chapitre La conduite, section …
```

Une seule ligne peut réunir plusieurs références, séparées par un point-virgule. Section, provenance ou langue sont conservées quand elles sont utiles. Une pagination imprimée inconnue est explicitement indiquée comme non identifiée ; aucun numéro n’est inventé. `reply` inclut la ligne finale et `source_line` reste disponible comme métadonnée. Le navigateur évite de l’afficher une seconde fois.

Sans fiche pertinente : réponse brève invitant à préciser l’équipement ou le symptôme, ou à choisir un véhicule, suivie de la phrase finale. Hors sujet : une seule phrase polie rappelant l’automobile, sans source ni formule supplémentaire. Une clarification peut poser une question. Sans manuel, sans passage exploitable ou en cas d’indisponibilité : message honnête, sans référence inventée ni recours à la FAQ. Les actions de sécurité restent présentes si le sujet les nécessite. Ces cas ne prétendent pas être des réponses documentaires sourcées.

## Fiches et répartition

**Aucune nouvelle entrée : quarante fiches existantes entièrement réécrites.** Leur réponse passe de `reponse_courte` à `reponse`. Chaque réponse stockée contient de **187 à 209 mots**, clôture incluse. Le chargement impose entre 150 et 300 mots, un identifiant unique, des champs non vides, un risque valide et une seule phrase finale. Les mots-clés, variantes, ancrages et exclusions restent associés aux mêmes fiches ; le moteur TF-IDF et son seuil ne changent pas.

| Catégorie | Fiches enrichies |
| --- | ---: |
| Entretien courant | 6 |
| Pneus | 5 |
| Voyants | 4 |
| Batterie | 3 |
| Freins | 3 |
| Sécurité des passagers | 3 |
| Conduite économique | 3 |
| Fuite de liquide | 3 |
| Climatisation | 3 |
| Caractéristiques du modèle | 3 |
| Démarrage difficile | 2 |
| Contrôle technique | 2 |
| **Total** | **40** |

Risque : sept faibles, dix-sept moyens, seize élevés. Aucun chiffre, couple, pression, capacité, type d’huile ou norme universels n’est ajouté. Les questions précises expliquent la notion et les conditions générales, puis proposent le véhicule lorsqu’une indication exacte est nécessaire.

## Sécurité : présentation supprimée, actions conservées

| Ancienne présentation retirée de la page de chat | Remplacement concret |
| --- | --- |
| Bandeau « Des repères documentés, jamais un diagnostic » et liste générale d’organes | Consignes adaptées au sujet, dans les paragraphes de réponse |
| Paragraphe suffixé « Sécurité : ne reprenez pas la route… » | `inline_safety` ajoute une consigne liée au risque seulement si le contenu n’en comporte pas déjà une |
| Explications « Réponse générale… », « Sans véhicule, posez… », état FAQ/manuels et source de fiche sous la réponse | Contenu direct ; choix visible dans le sélecteur, sans annonce de mode |
| Phrase générale du pied de page « Conseils généraux, sans diagnostic… » | Masquée uniquement sur la page de chat ; aucune consigne d’action supprimée |

- Freins : arrêt en sécurité, absence d’essai supplémentaire sur route, contrôle avant reprise si fonctionnement anormal (`freins_bruit`, `freins_pedale`, `freins_vibration`).
- Pneus et direction : immobilisation si dommage ou comportement anormal, pas de regonflage considéré comme réparation, vérification avant reprise (`pression_pneus`, `usure_pneus`, `pneu_endommage`, `pneu_perte`, `vibrations_roues` et garde de direction).
- Airbags : pas d’intervention sur le système ou son câblage ; vérification professionnelle avant reprise en cas de dommage ou d’alerte (`airbag`, `siege_enfant` et garde dédiée).
- Voyants rouges et huile : arrêt en sécurité ; pour l’alerte d’huile, couper le moteur et ne pas redémarrer avant vérification (`voyant_rouge`, `voyant_huile`).
- Carburant : immobiliser, couper le moteur, éloigner flammes et étincelles, assistance et absence de redémarrage (`fuite_carburant`).
- Fournisseur indisponible, manuel absent ou repli : les mêmes gardes adaptées au sujet restent actives, même sans réponse documentaire.

**Aucune règle d’action de sécurité n’est supprimée.** Le texte de présentation et la répétition des avertissements génériques sont supprimés, ainsi que la phrase informative finale sur le parcours manuel, à la demande du groupe. Le contrôle professionnel lié à un danger reste obligatoire. Aucun accès aux comptes, CSRF, ORM, échappement ou contrôle des références et valeurs n’est assoupli.

Les anciens messages ne sont pas réécrits en base. Leur présentation enlève l’ancien libellé, conserve les consignes sous forme de phrases et masque la source FAQ ; les références historiques restent enregistrées. Aucune référence documentaire nouvelle n’est créée pendant cette présentation.

## Vérifications factuelles et relecture

Aucune valeur technique incertaine n’est ajoutée. Les explications de causes restent des possibilités générales, sans diagnostic. Restent exclus : calendrier et pièces administratives propres au Maroc, tarifs, produits précis, valeurs mécaniques, conversions d’éclairage et causes certaines de pannes.

Les quarante fiches ne sont pas présentées comme validées par un professionnel. Relecture prioritaire des seize fiches à risque élevé : pneus, freinage, alertes rouges/huile/charge, airbags, fuites, refroidissement et couple de serrage. Les fiches batterie, démarrage, choix d’huile, retenue d’enfant et fusible demandent également une relecture pour vérifier que les limites de manipulation sont assez claires. Les caractéristiques exactes et procédures d’intervention restent propres au véhicule.

Repères vérifiés le 25 octobre, sans modification du registre web de l’application :

- [Dacia, batterie : dépannage](https://www.user-manual.dacia.com/fr/d%C3%A9pannage/batterie-depannage-0) : compatibilité, risques de branchement et interdiction de débrancher moteur tournant ; aucune tension ou procédure de raccordement transposée en règle générale.
- [Notice officielle, témoins et huile](https://www.user-manual.dacia.com/sites/dacia/files/documents/2026-04/NU%201449-6_FR-avec%20compression.pdf) : distinction entre alerte et rappel, arrêt et contrôle ; aucun emprunt de valeur ou attribution à une autre version.
- [Checklist Sécurité routière](https://www.securite-routiere.gouv.fr/sites/default/files/2020-09/checklist-voiture-2020_exe_.pdf) : texte indexé officiel consulté pour les pneus, visibilité, éclairage et retenues ; l’ouverture directe du PDF a répondu en erreur pendant cette vérification. Aucune norme chiffrée n’est reprise.
- [ADEME, écoconduite](https://agirpourlatransition.ademe.fr/particuliers/economiser/carburant/ecoconduite-solution-consommer-moins-carburant-limiter-emissions-co2) : anticipation, charge et consommation d’énergie, sans promesse chiffrée.

Les résultats exacts de tests et les vérifications sur l’application sont consignés dans [recette.md](recette.md). La livraison est régénérée depuis le projet, sans PDF, base, clé privée ni rapport temporaire.


## Résultats de recette

- Suite complète : **311 tests réussis en 209,41 s**, zéro échec, zéro ignoré. Sortie locale : `.work/pytest-format-final.txt`.
- Après renforcement de la consigne en cas d’alerte rouge/huile, **106 tests ciblés réussis en 13,22 s** (`test_response_format.py` et `test_answer_policy.py`). Les soixante-quatre nouveaux cas vérifient notamment les quarante réponses réelles de la FAQ, le format des sources, les libellés interdits, les risques, les replis et l’historique sans réécriture.
- Évaluation existante : **78/78 comportements conformes**, mêmes questions et attentes de sujets, avec les nouveaux contrôles de format. FAQ réelle et modèle factice pour les manuels ; aucun crédit consommé par cette évaluation. Ce score n’est pas une évaluation humaine de la pertinence automobile.
- Essai du fournisseur configuré avec le manuel local Bigster : réponse documentaire de **135 mots**, trois références vérifiées, dernière ligne de source présente, aucun libellé interdit ni clôture informative vers un mécanicien. La longueur du parcours manuel dépend des passages, sans compléter les informations manquantes.
- Parcours HTTP complet réel avec véhicule : inscription, ajout, entretien, discussion, déconnexion/reconnexion et historique conservé, CSRF actif. Compte temporaire supprimé.
- Parcours HTTP FAQ réel : réponse détaillée et clôture unique, aucun bandeau sur la page, sélecteur dans le même bloc, refus hors sujet en une phrase et réponse conservée après reconnexion. Compte temporaire supprimé.
- L’application source a été relancée sur le port 5001 ; `/health` répond en HTTP 200. Aucun démarrage Docker n’est revendiqué pour cette évolution.
