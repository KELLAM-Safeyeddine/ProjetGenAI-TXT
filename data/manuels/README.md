# Manuels Dacia locaux — procédure courante

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


## Inventaire courant

| Marque | Modèle | Année | Pages PDF | Passages | Bloqués | Source officielle |
| --- | --- | --- | --- | --- | --- | --- |
| Dacia | Bigster | 2026 | 430 | 1721 | 82 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/3819/pdf) |
| Dacia | Duster | 2026 | 440 | 1738 | 83 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4161/pdf) |
| Dacia | Jogger | 2026 | 422 | 1643 | 94 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4452/pdf) |
| Dacia | Logan | 2026 | 374 | 1448 | 91 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4630/pdf) |
| Dacia | Sandero Stepway | 2026 | 384 | 1486 | 97 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/2528/pdf) |
| Dacia | Sandero | 2021 | 402 | 1292 | 58 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/4030/pdf) |
| Dacia | Sandero | 2026 | 384 | 1486 | 97 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/2528/pdf) |
| Dacia | Spring | 2026 | 286 | 1078 | 69 | [Notice officielle](https://www.user-manual.dacia.com/fr/notice/3692/pdf) |

Inventaire complet, nombres de passages et motifs de rejet : `docs/DIAGNOSTIC_ASSISTANT.md`.
