# Catalogue marocain — sources et méthode

Consultation : **17 octobre 2026**. Les données sont des faits reformulés, sans descriptions commerciales, prix ni extraits de manuels reproduits. Aucune API payante, aucun dataset tiers importé.

## Choix des cinq marques

Le périmètre statistique retenu est celui des **véhicules particuliers neufs (VP)**, pour comparer des chiffres homogènes. Le catalogue peut aussi contenir un utilitaire de ces mêmes marques lorsque sa présence est attestée sur le site marocain.

Sources primaires :

- [AIVAM, bilan 2022](https://www.aivam.ma/sites/default/files/2023-10/Performance%20du%20marche%CC%81%20automobile%20au%20Maroc%20en%202022.pdf), page 7 du PDF : volumes VP 2021 et 2022.
- [AIVAM, bilan 2024](https://www.aivam.ma/sites/default/files/2025-01/Bilan%20Aivam%202024.pdf), page 16 du PDF : volumes VP 2022, 2023 et 2024. Le top 5 du marché total figure aussi page 15.
- [Index de documentation AIVAM](https://www.aivam.ma/fr/documentation-et-etudes).

Calcul reproductible du cumul VP 2021–2024 à partir de ces deux bilans (les années ne sont comptées qu’une fois) :

| Marque | 2021 | 2022 | 2023 | 2024 | Cumul |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dacia | 44 029 | 38 885 | 33 830 | 39 331 | 156 075 |
| Renault | 20 386 | 21 545 | 22 553 | 23 697 | 88 181 |
| Hyundai | 12 008 | 13 197 | 13 884 | 11 898 | 50 987 |
| Peugeot | 12 230 | 11 435 | 12 026 | 10 517 | 46 208 |
| Volkswagen | 6 929 | 5 741 | 8 699 | 10 336 | 31 705 |

Le cumul Opel sur ces mêmes années est de 29 086, inférieur à Volkswagen. Les ordres annuels varient : Volkswagen n’était pas cinquième chaque année. La sélection porte sur le cumul documenté, pas sur une position annuelle constante.

Corroboration sectorielle pour 2025 : [Tomobile360 / Challenge Auto, bilan 2025 citant AIVAM](https://www.tomobile360.ma/actu/marche-automobile-maroc-2025-records-2026), publié le 6 avril 2026, donne le même groupe de cinq marques VP. Cette source secondaire ne publie pas tous les volumes ; les valeurs manquantes ne sont pas reconstituées à partir de pourcentages arrondis.

**Limite confirmée : le classement cumulé exhaustif 2021–2026 n’est pas établi.** L’année 2026 est en cours à la consultation. La sélection opérationnelle est donc fondée sur 2021–2024 vérifié et corroborée par 2025, sans prétendre à un classement annuel 2026 définitif. Les séries complémentaires restent à confirmer.

## Sources du catalogue

Chaque ligne de `vehicules_maroc.json` possède son tableau `source`, sa date `consulte_le` et sa `preuve_annee`. Les familles de sources sont :

| Marque | Sources officielles marocaines |
| --- | --- |
| Dacia | [Gamme](https://www.dacia.ma/), fiches Logan, Sandero Stepway, Jogger, Duster et Bigster liées dans chaque entrée |
| Renault | [Gamme marocaine](https://www.renault.ma/), noms et motorisations explicitement associés aux cartes modèles |
| Hyundai | [Gamme marocaine](https://www.hyundai.com/ma/fr), cartes portant une année et fiches locales ; [IONIQ 5 électrique](https://connect.hyundai.ma/) |
| Peugeot | [Gamme marocaine](https://www.peugeot.ma/), pages locales des 208, 2008, 308, 3008, Landtrek, Boxer, Rifter, Partner, 5008 et 408 |
| Volkswagen | [Gamme marocaine](https://www.volkswagen.ma/fr.html), fiches locales des modèles ; aucune motorisation supposée depuis un catalogue étranger |

Pour Sandero 2021 : [communiqué Renault Group du 27 juillet 2021](https://media.renaultgroup.com/renault-group-maroc-annonce-une-nouvelle-etape-pour-son-ecosysteme-dans-le-royaume/?lang=fra) annonçant la commercialisation au Maroc en septembre 2021. La motorisation locale n’y est pas établie et reste absente.

## Sens des champs et couverture

- `annee` : année attestée, avec son **type de preuve**. `offre_observee` signifie présence sur un site officiel marocain consulté en 2026 ; ce n’est pas une preuve du millésime, de l’année de fabrication ni de toutes les années précédentes. `annee_affichee_constructeur` retranscrit uniquement l’étiquette d’année de la carte Hyundai, qui peut désigner une génération. `communique_date` signale une publication datée.
- `motorisation` : uniquement Essence, Diesel, Hybride, Électrique lorsque l’information locale a été retenue ; sinon `null`, affiché « Non documentée ». Une motorisation actuelle n’est pas propagée à une année passée sans preuve distincte. L’hybride rechargeable reste classé Hybride, sans prétendre à une variante technique précise.
- `periode_commercialisation` et `intervalle_entretien` : `null`, faute de preuve constructeur précise par modèle/année. Aucun intervalle d’entretien n’est proposé par ce catalogue.
- Les appellations commerciales « Nouveau » sont retirées lorsqu’elles ne distinguent pas un modèle ; « Nouvelle Clio » est conservée à part puisque les deux gammes Clio sont simultanément présentées avec des motorisations différentes.
- Le catalogue couvre **53 appellations et 77 combinaisons**, avec **20 motorisations absentes**. La couverture 2021–2025 est partielle. Il ne constitue ni une liste exhaustive de toutes les anciennes gammes, ni une certification des millésimes vendus au Maroc.
- Une annonce d’ouverture future des commandes ne suffit pas à déclarer une motorisation disponible. Le Bigster hybride est ainsi exclu en raison de cette mention dans la fiche officielle, malgré sa présentation en page d’accueil.

Les recherches encore ouvertes sont consignées dans un fichier de travail conservé uniquement dans le projet. Ce fichier n’est pas nécessaire au lancement et est exclu de la livraison ; les limites validées ci-dessus restent, elles, livrées avec le dataset.
