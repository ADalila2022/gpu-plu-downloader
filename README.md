# GPU PLU Downloader

Extension QGIS permettant de rechercher et de télécharger les données d’un Plan Local d’Urbanisme (PLU) ou d’un Plan Local d’Urbanisme intercommunal (PLUi) depuis le Géoportail de l’Urbanisme (GPU), puis de charger les couches géographiques dans QGIS.

> **Version expérimentale**
> Cette version est en cours de validation. Le téléchargement complet et le chargement des couches dans QGIS restent à valider.

## Fonctionnalités

Le plugin permet :

- de rechercher une commune par son nom, son code INSEE ou son code postal ;
- de sélectionner la commune dans une liste de résultats ;
- de rechercher les PLU et PLUi publiés couvrant le point central de cette commune ;
- de télécharger l’archive complète du document sélectionné ;
- d’extraire l’archive en conservant son arborescence et ses pièces écrites ;
- de rechercher les fichiers shapefile dans les sous-dossiers `Donnees_geographiques` ;
- de charger les couches valides dans un groupe dédié dans QGIS.

La recherche des documents utilise le module Urbanisme de l’API Carto de l’IGN. Le téléchargement utilise l’API du Géoportail de l’Urbanisme.

## Utilisation

1. Saisir le nom, le code INSEE ou le code postal d’une commune.
2. Cliquer sur **Rechercher la commune**, puis sélectionner le résultat souhaité.
3. Cliquer sur **Rechercher les documents GPU**.
4. Sélectionner le PLU ou le PLUi proposé.
5. Choisir un dossier de destination existant et vide.
6. Cliquer sur **Télécharger et charger les SHP**.

Les pièces écrites sont conservées sur disque. Seules les couches shapefile situées sous `Donnees_geographiques` sont chargées dans QGIS.

## Limites de la version actuelle

- La recherche géographique utilise le point central de la commune. Elle ne garantit pas l’identification de tous les documents couvrant une partie de son territoire.
- Seuls les documents de type PLU et PLUi publiés sont proposés.
- Lorsqu’une commune relève d’un PLUi, l’archive téléchargée correspond au document intercommunal complet.
- Un dossier existant et vide est obligatoire pour chaque téléchargement.
- Pour une saisie numérique de cinq chiffres, le plugin recherche d’abord un code INSEE, puis un code postal. Certains codes peuvent donc être ambigus.
- L’annulation et la reprise des téléchargements ne sont pas disponibles.
- Aucune symbologie automatique n’est appliquée aux couches.
- Les archives dont la taille décompressée dépasse 4 Gio sont refusées.

La recherche a été vérifiée sur Châteauroux et Charenton-le-Pont. L’accès à l’archive ZIP de Châteauroux a également été vérifié. Ces contrôles ne constituent pas une validation complète du fonctionnement dans QGIS.

## Compatibilité

- Version minimale déclarée : **QGIS 3.22**.
- La compatibilité effective reste à valider sur les versions de QGIS ciblées.
- Une connexion Internet est nécessaire pour la recherche et le téléchargement.

## Installation

Pendant la phase de test, installer le plugin depuis son archive ZIP :

`Extensions > Installer/Gérer les extensions > Installer depuis un ZIP`

Sélectionner l’archive du plugin, puis activer **GPU PLU Downloader**.

Après le remplacement d’une version déjà chargée, redémarrer QGIS pour utiliser le nouveau code.

## Ressources

- Géoportail de l’Urbanisme : https://www.geoportail-urbanisme.gouv.fr/
- API GPU : https://www.geoportail-urbanisme.gouv.fr/api/
- API Carto — module Urbanisme : https://apicarto.ign.fr/api/doc/gpu

## Licence

Ce projet est distribué sous licence **GNU General Public License v3.0 (GPL-3.0)**.

Voir le fichier `LICENSE`.

## Auteur

**Dalila AMIAR MEFTAH (GEOMA-SIG)**
