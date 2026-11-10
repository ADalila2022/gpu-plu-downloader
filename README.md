# GPU PLU Downloader 0.3.0 — version de test

## Installation
Dans QGIS : Extensions > Installer/Gérer les extensions > Installer depuis un ZIP.
Sélectionner gpu_plu_downloader_0.3.0.zip. Si une ancienne version est chargée,
redémarrer QGIS après installation, puis activer GPU PLU Downloader.

## Test conseillé
1. Rechercher Châteauroux (ou 36000), sélectionner Châteauroux (36044).
2. Rechercher les documents : PLUi Châteauroux Métropole doit apparaître.
3. Choisir un dossier existant et vide, dédié au téléchargement.
4. Télécharger et charger les SHP. Le PLUi complet peut être volumineux.
L'arborescence et les pièces écrites sont conservées. Seuls les SHP situés
sous Donnees_geographiques sont chargés dans QGIS.

## Modifications
- Interface centrée sur la commune ; suppression du choix EPCI/SIREN.
- Recherche géographique API Carto au centre communal, filtrage PLU/PLUi
  publiés et déduplication par identifiant GPU.
- Téléchargement via /api/document/{documentId}/download.
- Messages HTTP détaillés ; dossier vide obligatoire pour éviter les mélanges.
- Fermeture du dialogue bloquée pendant une opération réseau.

## Vérifications et limites
Recherche réelle concluante sur Châteauroux et Charenton-le-Pont.
Premiers octets ZIP de Châteauroux vérifiés via la route de téléchargement.
Tests locaux : parsing/filtrage, arborescence, SHP, protection ZIP.
Pas de téléchargement complet ni de test de chargement dans une session QGIS.
La recherche au centre communal peut manquer un document applicable à une
portion différente de la commune : couverture complète à améliorer ensuite.
La priorité INSEE puis code postal de la version précédente reste inchangée.
Pas d'annulation ni de reprise des téléchargements.

## Organisation du code
- __init__.py : classFactory, point d'entrée QGIS.
- gpu_plu_downloader.py : intégration QGIS et ouverture du dialogue.
- gpu_plu_downloader_dialog.py : interface et orchestration.
- worker.py : opérations en thread.
- api.py : HTTP, téléchargement, extraction et détection des SHP.
L'interface est construite en Python ; aucun fichier Qt Designer .ui n'est requis.

## Avant publication sur le dépôt officiel
Renseigner l'adresse email réelle et l'URL réelle du dépôt source dans metadata.txt.
Choisir une licence et inclure le fichier LICENSE correspondant. Ces informations
ne sont pas inventées dans cette version locale. La compatibilité minimale 3.22
est héritée du prototype et doit être validée sur les versions ciblées.
