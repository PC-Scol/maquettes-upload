#!/usr/bin/env python3
"""\
Objet       transférer des arbres maquettes vers Pégase, dans un espace et un environnement de son choix

API utilisées
    OffreDeFormation Externe V1     espaces-externe   /etablissement/{codeStructure}/espaces
    OffreDeFormation V1             maquettes         /etablissement/{codeStructure}/maquette/{id}/importerBase64VersEspace)

Entrée      une succession de lignes représentant chacune un objet JSON complet
Sortie      messages d'information sur le déroulé des opérations

Usage       maquettes-upload.py <ETAB> <ENV> <ESPACE>
  ETAB      Etablissement tel qu'il apparaît dans les urls Pégase (juste avant 'pc-scol.fr')
  ENV       Environnement vers lequel la maquette doit être envoyée
  ESPACE    Nom de l'espace de travail sur l'environnement

Auteur
Alfredo Pereira - 09/24
alfredo.pereira@inalco.fr
"""

usage="""
Usage       {} <ETAB> <ENV> <ESPACE>
  ETAB      Etablissement tel qu'il apparaît dans les urls Pégase (juste avant 'pc-scol.fr')
  ENV       Environnement vers lequel la maquette doit être envoyée
  ESPACE    Nom de l'espace de travail sur l'environnement
"""

import sys
import getpass
import requests
import zlib
import base64
import json
import getopt


argv = sys.argv
commande = argv[0]

#
# Parser les arguments de la commande avec le module getopt
#
try:
    opts, args = getopt.gnu_getopt(argv[1:], "a")
except:
    print(usage.format(commande).strip(), file=sys.stderr)
    sys.exit(1)


for opt, arg in opts:
    if opt == '-a':
        print(usage.format(commande).strip())
        sys.exit(0)

    argv.remove(opt)
    if arg: argv.remove(arg)


#
# Test des paramètres de la commande, on quitte si qqch est bizarre
#

environnements = ['BAS', 'RDD', 'TEST', 'PILOTE', 'PROD']

try:
    commande = sys.argv[0]
    etablissement = sys.argv.pop(1).lower()
    environnement = sys.argv.pop(1).upper()
    code_espace = sys.argv.pop(1).upper()
except:
    print(usage.format(commande).strip(), file=sys.stderr)
    sys.exit(1)

if len(sys.argv) > 1:
    print(usage.format(commande).strip(), file=sys.stderr)
    sys.exit(1)

if environnement not in environnements:
    print('Les environnements autorisés sont', ', '.join(environnements[:-1]), 'ou', environnements[-1])
    sys.exit(1)


#
# Variables globales
#

username = 'svc-api'
instance = environnement.lower() + '-' + etablissement
auth_url = 'https://authn-app.' + instance + '.pc-scol.fr/cas/v1/tickets'
odf_url_api = 'https://odf.' + instance + '.pc-scol.fr/api/odf/v1/etablissement/ETAB00/'
odf_url_espaces  = odf_url_api + 'espaces?page=0&taille=10&r='
odf_url_maquette = odf_url_api + 'maquette/importerBase64VersEspace'


def get_token():
    """Fonction d'identification sur le serveur, le sésame en valeur de retour"""

    password = getpass.getpass(prompt='Mot de passe API pour l\'environnement ' + environnement + ' : ', stream=None)

    response = requests.post(
        auth_url,
        headers = {'content-type': 'application/x-www-form-urlencoded'},
        data = {'username': username, 'password': password, 'token': 'true'}
    )

    if response.status_code == 201:
        return response.text
    else:
        raise Exception(response.status_code)


def get_espace(token, code_espace):
    """Fonction retournant l'id sur l'environnement de l'espace de travail spécifié en commande"""

    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token
    }

    payload = {
        'pageable': {'page': 0, 'taille': 10, 'tri': []}
    }

    response = requests.get(
        odf_url_espaces + code_espace,
        headers = headers,
        params = payload
    )

    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()

        if data['items']:
            #
            # Construction d'un dictionnaire des espaces
            #
            espaces = {espace['code'] : espace['id'] for espace in data['items']}

        try:
            #
            # On retourne, s'il existe, l'id de l'espace passé en commande
            #
            return espaces[code_espace]
        except:
            raise Exception('400')
    else:
        raise Exception(response.status_code)


def envoi_maquette(token, id_espace, maquette64):
    """Fonction d'upload de la maquette sur Pégase"""

    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }

    payload = {
        'espaceId': id_espace,
        'base64Encode': maquette64,
        'checkNomenclatures': False
    }

    response = requests.post(
        odf_url_maquette,
        headers = headers,
        data = json.dumps(payload)
    )

    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()

        try:
            return data['code']
        except:
            raise Exception(data['statusCode'])
    else:
        raise Exception(response.status_code)


def main():
    #
    # On s'identifie
    #
    try:
        token = get_token()
    except Exception as erreur:
        print('Erreur d\'identification sur l\'environnement', environnement, '\n', erreur)
        sys.exit(1)
    else:
        print('Accès à l\'environnement', environnement)

    #
    # On acquiert l'id de l'espace sur lequel procéder à l'envoi de données
    #
    try:
        id_espace = get_espace(token, code_espace)
    except Exception as erreur:
        print('Erreur d\'accès à l\'espace', code_espace, 'sur l\'environnement', environnement, '\n', erreur)
        sys.exit(1)
    else:
        print('L\'espace', code_espace, 'a bien été atteint sur l\'environnement', environnement)


    #
    # On traite l'entrée standard
    #
    for ligne in sys.stdin:
        ligne = ligne.strip()

        try:
            #
            # Tentative de construction d'un objet JSON valide à partir de la donnée chargée afin de vérifier sa cohérence syntaxique
            #
            maquette = json.loads(ligne)
            code = maquette['code']
        except:
            #
            # On passe à la maquette suivante si on a rencontré une erreur
            #
            print('La maquette json contient des erreurs -', ligne[:40] + '...')
            continue


        #
        # Compression de la donnée chargée (gzip) puis encodage en base 64 du résultat
        #
        compressor = zlib.compressobj(wbits=25)
        data = ligne.encode()
        dataz = compressor.compress(data)
        dataz += compressor.flush()
        dataz = base64.b64encode(dataz).decode()

        #
        # Envoi du résultat (chaîne en base 64) vers l'espace de travail
        #
        try:
            racine = envoi_maquette(token, id_espace, dataz)
        except Exception as erreur:
            print(code, ': erreur d\'importation sur l\'environnement', environnement, '/', code_espace, '\n', erreur)
        else:
            print(code, ': maquette correctement importée sur l\'environnement', environnement, '/', code_espace)

        #
        # Fin de main()
        #

if __name__ == '__main__':
	main()
