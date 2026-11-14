# FAQ générale — règle courante du 25 octobre 2026

Sans véhicule sélectionné, `answer_service` consulte d’abord `data/faq_generale.json`. Avec véhicule, seul le manuel exact reste utilisé ; l’absence de manuel ou de passage ne déclenche pas cette FAQ. La règle antérieure de désactivation totale est explicitement annulée dans [CHANGEMENTS.md](CHANGEMENTS.md).

## Contenu livré

Quarante fiches existantes réécrites, zéro nouvelle entrée, distinctes de l’ancienne FAQ archivée. Chaque fiche possède un identifiant unique, une catégorie, une question, une réponse détaillée de 150 à 300 mots (`reponse`), des mots-clés et un risque valide. Aucun chiffre, constructeur ou norme technique n’est présent dans ce fichier. Les seize fiches à risque élevé recommandent explicitement un mécanicien. Répartition des risques : sept faibles, dix-sept moyens, seize élevés.

| Catégorie | Entrées |
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
| Caractéristiques propres au modèle | 3 |
| Démarrage difficile | 2 |
| Contrôle technique | 2 |
| **Total** | **40** |

La recherche réutilise le moteur FAQ existant : `search_response`, normalisation et synonymes partagés, mots-clés et TF-IDF/cosinus. Aucun second moteur, fournisseur ou dépendance n’est ajouté. Le seuil existant reste 0,45. Les champs facultatifs `variantes`, `ancrages` et `exclusions` précisent la portée d’une fiche : les ancrages exigent un terme du sujet et les exclusions évitent de confondre un sujet voisin non couvert. Ces contrôles s’appliquent aux fiches qui les déclarent ; les anciens corpus ne changent pas. Ils ne constituent pas un diagnostic.

L’assistant répond directement, sans label de mode ni source FAQ affichée, puis termine par une seule phrase vers un mécanicien. Les références de fiche restent des métadonnées API, sans véhicule ni page. Les questions précises reçoivent une explication générale et une invitation à choisir le véhicule si nécessaire. Un repli honnête et bref suit la même clôture ; un hors sujet reçoit une seule phrase de refus. Les actions de sécurité sont dans le contenu, sans bandeau. Le nouveau format et les limites sont détaillés dans [FORMAT_REPONSES.md](FORMAT_REPONSES.md).

Le fichier est validé et chargé directement, sans import SQL ni clé de modèle. L’ancienne commande `import-faq` et l’administration concernent toujours l’archive `data/faq.json`, qui n’alimente pas ces réponses. La FAQ ne reçoit ni historique documentaire, ni passages, ni fournisseur. Les contrôles d’accès, CSRF, messages textuels et échappement sont conservés. Le sélecteur de véhicule est désormais juste au-dessus du champ de question.

## Vérification factuelle et relecture humaine

Sources officielles consultées le **24 octobre 2026**, utilisées comme repères généraux, sans reprendre leurs valeurs ni transformer des règles françaises en règles marocaines :

- [Sécurité routière — checklist du véhicule](https://www.securite-routiere.gouv.fr/sites/default/files/2020-09/checklist-voiture-2020_exe_.pdf) : vérifications visuelles des pneus, éclairage, essuie-glaces et équipements de sécurité.
- [Sécurité routière — préparation d’un long trajet](https://www.securite-routiere.gouv.fr/sites/default/files/2019-01/deplongtrajet_2014_bd.pdf) : état du véhicule et contrôles généraux avant départ.
- [Sécurité routière — siège enfant](https://www.securite-routiere.gouv.fr/sites/default/files/2024-05/siege_affiche_sd_0.pdf) : installation adaptée et respect des consignes du siège et du véhicule, sans âge ni taille dans la FAQ.
- [ADEME — écoconduite](https://agirpourlatransition.ademe.fr/particuliers/economiser/carburant/ecoconduite-solution-consommer-moins-carburant-limiter-emissions-co2) : anticipation, conduite souple, chargement et climatisation, sans économie chiffrée annoncée.
- [Service Public — contrôle technique](https://www.service-public.gouv.fr/particuliers/vosdroits/F2878) : distinction entre contrôle et entretien. Aucun délai, document requis ou obligation française n’est transposé au Maroc.

Le registre web de l’application n’est pas élargi : ces vérifications de rédaction ne déclenchent aucune recherche web dans le chat.

Aucune affirmation jugée incertaine n’a été ajoutée. Restent volontairement hors de la FAQ : délais et pièces administratives propres au Maroc, tarifs, compatibilité précise d’une huile ou d’une ampoule, caractéristiques chiffrées et causes mécaniques déduites d’un bruit ou d’une couleur de liquide. Ces sujets demandent une source spécifique avant enrichissement.

Une relecture par un professionnel reste à organiser, en priorité sur les fiches à risque élevé : pneus, freinage, alertes rouges/huile/charge, airbags et fuites. La fiche de voyant rouge vise une alerte inconnue en circulation ; elle ne prétend pas que tout pictogramme rouge, dans toute situation, signifie la même panne. Les conseils sont généraux et ne remplacent pas un diagnostic.

## Recette reproductible

```powershell
python -m pytest -q
flask --app run evaluer-chatbot --rapport .work/evaluation-faq-generale.md
```

L’évaluation conserve les formulations, identifiants, catégories et contextes des soixante-dix-huit questions. Seules les attentes sans véhicule ont été adaptées, avec archivage des anciennes valeurs dans `attendu_avant_faq_generale`. Pour les sujets couverts, l’identifiant de fiche est contrôlé ; pour les sujets précis non couverts, le comportement attendu est un repli honnête. Les essais avec véhicule conservent le modèle factice et quatre pages de manuel fictif ; aucun appel payant ou réseau n’est effectué. Le score n’est pas une mesure de la qualité d’un vrai modèle ni de la couverture de tous les manuels.

Les résultats exacts de cette campagne figurent dans [recette.md](recette.md). Les rapports générés restent locaux et sont exclus de la livraison ; le code, la FAQ générale, les tests et cette documentation sont livrés sans PDF ni secret.


### Résultats de la campagne précédente du 24 octobre

- Suite complète : **247 réussis en 62,96 s**, zéro échec, zéro ignoré ; dont vingt-six nouveaux cas de FAQ générale.
- Évaluation : **78/78 comportements conformes**, zéro échec restant, aucune question reformulée pour améliorer le score. Les replis honnêtes sont comptés comme tels ; ce résultat ne mesure pas la qualité d’un modèle réel.
- Docker Engine arrêté : démarrage et santé Docker non revérifiés. La livraison conserve les fichiers Docker et aucun PDF ni secret.


### Recette du format courant, 25 octobre

Quarante fiches réécrites de 187 à 209 mots, sans nouvelle entrée. Suite complète : **311 réussis en 209,41 s** ; gardes après dernier renforcement : **106 réussis en 13,22 s** ; évaluation : **78/78 comportements conformes**. Sécurité dans les paragraphes, sans libellé, source FAQ ou bandeau affichés. Rapport détaillé : [FORMAT_REPONSES.md](FORMAT_REPONSES.md).
