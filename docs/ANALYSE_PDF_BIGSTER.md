> Complément courant : deux blocs de prose des pages PDF 355/356 ont été vérifiés visuellement et liés à leurs empreintes ; Bigster conserve 1 721 passages dont 82 bloqués, soit 1 639 utilisables. Les autres réserves ci-dessous restent applicables. Les huit Dacia locaux sont désormais importés ; rapport complet dans [DIAGNOSTIC_ASSISTANT.md](DIAGNOSTIC_ASSISTANT.md).

# Analyse structurelle du PDF Bigster — 24 octobre 2026

- Document local : `data/manuels/dacia/bigster/2026/manuel.pdf`.
- Titre PDF : `NU 1626-3 R1310` ; 430 pages ; 566,929 × 419,528 points ; non chiffré.
- `pdfinfo` disponible ; `pdffonts` absent. La couche texte a été confirmée par extraction de mots/caractères et inspection des ressources de polices (aucun OCR).
- Polices observées sur la page PDF 198 :

  - `/AAAAAG+Arial-BoldMT` : incorporée = True.
  - `/AAAAAH+NotoSansSymbols2-Regular-Identity-H` : incorporée = True.
  - `/AAAAAD+ArialMT` : incorporée = True.
  - `/AAAAAE+Arial-BoldMT` : incorporée = True.
  - `/AAAAAF+ArialMT` : incorporée = True.

## Mise en page et choix du parseur

La page PDF 198 affiche deux colonnes principales et deux encadrés latéraux. L’ordre brut par ligne mélangerait des avertissements sur le centre de gravité, des conseils de pneumatiques et des conseils d’utilisation. Les mots sont donc séparés par bandes géométriques, avec une véritable gouttière de huit points minimum, et les encadrés sont extraits à part. Le test interdit explicitement ces mélanges.

Le pied de page donne 196 ; le décalage PDF moins page imprimée égal à 2 est corroboré sur plusieurs pages avant utilisation en repli. Les deux orientations du pied (« 196 - La conduite » ou « Caractéristiques techniques - 403 ») sont reconnues.

La page PDF 405 contient un tableau des masses : en-têtes Versions / 4x2 / 4x4. Les cellules fusionnées sont identifiées par leur boîte, pas à partir d’un simple vide. Le tableau est un passage atomique. La table numérique de la page PDF 404 est aussi conservée, même si elle contient peu de lettres.

Les mots coupés sont recollés ; les flèches et leur cible sortent du texte mais la cible demeure en métadonnées. Les chapitres, sections, variantes et pages restent associés au même bloc. Les encadrés/listes/tableaux ne sont jamais découpés à la limite arbitraire de 700 caractères. Les éventuels blocs trop grands pour le budget du modèle sont écartés, jamais tronqués.

## Limites contrôlées

18 pages demandent une revue visuelle : 119, 200, 201, 204, 353, 354, 355, 356, 357, 358, 359, 360, 362, 363, 366, 386, 388, 389. Leurs passages ne sont pas utilisés pour répondre. Les pages sans texte suffisant ne déclenchent aucun OCR automatique. Le traitement géométrique est plus fiable que l’ancien flux pypdf non zoné sur les pages examinées, mais ne constitue pas une garantie de transcription parfaite de chaque schéma/tableau du document.

Le dépôt conserve seulement l’extrait géométrique JSON de deux pages pour les régressions. Le test d’intégration lit quelques pages du PDF local s’il est disponible. Aucun fichier PDF constructeur complet n’est ajouté au dépôt ni à la livraison.

Documentation technique utilisée : [pdfplumber](https://github.com/jsvine/pdfplumber), consultée le 24/10/2026. Bilan d’import et tests : [recette.md](recette.md).
