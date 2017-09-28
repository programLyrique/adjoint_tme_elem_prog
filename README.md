# adjoint_tme

Un script python pour télécharger les TMEs d'une semaine donnée et éventuellement en vérifier rapidement la syntaxe.


## Dépendances

``` bash
pip3 install requests
```

## Usage
adjoint_tme.py [-h] [-s] date "dossier de destination"


Arguments positionnels :
- `date` : Date du TME au format annéeMoisJour. Ex : 2017Sep22
- `dossier de destination` : Dossier où ajouter les fichiers du TME

Arguments optionnels :
-  `-h`, `--help` :afficher l'aide et quitter
-  `-s`, `--syntax` : vérifie la syntaxe de chacun des fichiers

## Fichier de configuration

`config_adjoint_tme.json`

Tous les composants sont optionnels, mais la valeur par défaut ne sera pas toujours raisonnable.

- duree : nombre de jours après la date du TME pendant lesquels les étudiants peuvent encoer soumettre
- annee : année de l'UE
- groupe : groupe. Ex: MIPI11.1
- nb_etudiants : nombre d'étudiants attendus
- nomUE : 1I001-2017oct
- login : demandé par le script si pas précisé
- motdepasse : demandé par le script si pas précisé
