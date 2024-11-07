# Objet
Boucle Python faisant appel à l'API d'import de maquettes de Pégase.
Le script lit l'entrée standard du shell à la recherche d'objets JSON pour les téléverser dans Pégase.

> [!NOTE]
> Script testé sur chaque version Pégase depuis la V24
> 
> API utilisées :
> - **1 appel** - OffreDeFormation Externe V1 (**section** espaces-externe, **fonction** /etablissement/{codeStructure}/espaces)
> - **N appels** - OffreDeFormation V1 (**section** maquettes, **fonction** /etablissement/{codeStructure}/maquette/{id}/importerBase64VersEspace)


<p>&nbsp;</p>

# Usage
```bash
  maquettes-upload.py <ETAB> <ENV> <ESPACE>
```

La commande doit contenir les paramètres suivants, dans l'ordre :

| Paramètre | Description |
| --- | --- |
| ETAB | Etablissement tel qu'il apparaît dans les urls Pégase (juste avant 'pc-scol.fr') |
| ENV | Environnement vers lequel la maquette doit être envoyée |
| ESPACE | Nom de l'espace de travail sur l'environnement |

<p>&nbsp;</p>

> [!TIP]
> Le paramètre _ETAB_ est le suffixe établissement des adresses web d'instances d'environnements.
> 
> Par exemple pour l'Inalco, dont l'url BAS est _https://cof.bas-inalco.pc-scol.fr/_, _**ETAB**_ sera _**inalco**_

<p>&nbsp;</p>

# Couplage avec le script de génération de maquettes au format JSON à partir de fichiers Excel
En chaînant le script maquettes-xl2json.py avec le script d'upload vers Pégase maquettes-upload.py, on obtient une fonctionnalité d'upload direct de maquettes au format Excel vers Pégase.

Par exemple :
```bash
  maquettes-xl2json.py maquette-type.xslx | maquettes-upload.py inalco BAS ESPACE-TEST
```
pour téléverser dans Pégase la maquette du fichier maquette-type.xlsx vers l'instance bac à sable (BAS) de l'Inalco, dans l'espace de travail ESPACE-TEST.
