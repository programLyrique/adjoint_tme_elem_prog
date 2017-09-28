# coding: utf8

import argparse
import json
import datetime
import requests # A installer avec pip3
from requests.compat import quote_plus
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import getpass
import locale
from html.parser import HTMLParser
import py_compile
import os.path
import string

# As we don't check the SSL certificate
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Basic parser to extract links to submitted files in a page
class LinkExtractor(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attr_dict = dict(attrs)
            self.links.append(attr_dict["href"])

    def get_links(self):
        # The first 4 links are not relevant
        return self.links[5:]

# Arguments :
# - date du tme
# - vérifier la syntaxe ou pas des scripts python (ne l'exécute pas)

parser = argparse.ArgumentParser(description="Récupère les TMEs d'une semaine")
parser.add_argument('dateTME', metavar="date", help="Date du TME au format annéeMoisJour. Ex : 2017Sep26")
parser.add_argument('destination', metavar="dossier de destination", help="Dossier où ajouter les fichiers du TME")
parser.add_argument('-s', '--syntax', action="store_true", help="Vérifie la syntaxe de chacun des fichiers")

args = parser.parse_args()

try:
    locale.setlocale(locale.LC_ALL, 'fr_FR')# Nécessaire pour générer les bonnes dates (qui sont en français). N'est pas threadsafe bien sûr...
    tmeDate = datetime.datetime.strptime(args.dateTME, "%Y%b%d")
    locale.resetlocale()
except ValueError:
    print("Erreur du format de la date")
    parser.print_help()
    parser.exit()

if not os.path.exists(args.destination):
    parser.exit("Le dossier de destination des TME n'existe pas.")

# Configuration (json)
# La config est supposée être à côté du script
# - durée: durée en jours après la date du tme autorisée avant de rendre le tme
# - année
# - groupe
# - nombre d'étudiants (permet de faire un test rapide pour savoir si tous ont rendu)
# - nom de l'UE
# - login
# - mot de passe
config={}
try:
    with open('config_adjoint_tme.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("config_adjoint_tme.json n'a pas été trouvé. On utilise donc des valeurs par défaut.")

default_year = str(datetime.date.today().year)

duration = datetime.timedelta(days = config.get("duree", 0))
year = str(config.get("annee", default_year))
group = config.get("groupe", "PCGI12.5") # Default ?
nb_students = config.get("nb_etudiants", 0)
ue_name = config.get("nomUE", "1I001-" + year + "oct")

deadline = tmeDate + duration
print("Récupération des soumissions pour le TME du ", tmeDate, " avec la date limite de rendu au ", deadline)
print("Groupe : ", group)

# Auth
if "login" in config:
    login = config["login"]
else:
    login = input("Login: ")

if "motdepasse" in config:
    password = config["motdepasse"]
else:
    password = getpass.getpass()

auth = requests.auth.HTTPBasicAuth(login, password)

# Build URL for the tme day
base = "https://www.licence.info.upmc.fr/lmd/licence/"
tme_url = base + quote_plus(year) +  "/ue/" + quote_plus(ue_name) + "/devoirs" + year + "/" + quote_plus(group) + "/"


# Now retrieve submissions starting from the most recent ones
submissions = dict() # key: name1-name2 ; elem: tme

one_day = datetime.timedelta(days=1)
currentDate = deadline

while( currentDate >= tmeDate):
    # In French, months do no start by capital letters, but the submission website uses capital letters
    formattedCurrentDate = string.capwords(currentDate.strftime("%Y %b %d")).replace(" ", "")
    url =  tme_url + quote_plus(formattedCurrentDate)

    #Interrogate url of the current day
    response = requests.get(url, auth=auth, verify=False)
    #print("URL: ", url)

    #Is there any tme that were submitted on that day
    if response.status_code != 404:
        #print("Des TMEs ont été soumis le ", currentDate)
        extractor = LinkExtractor()
        extractor.feed(response.text)
        for link in extractor.get_links():
            # Clean the file name
            names = ""
            components = link.split("-")
            if components[1] == "": # One student # name--numbers is split into name, , numbers
                names = components[0]
            else: # Two students name1-name2-numbers is split into name1, name2, numbers
                names = "-".join(components[:2])


            # Le fichier n'a pas été soumis plus récemment
            if names not in submissions:
                res_file = requests.get(url + "/" + link, auth=auth, verify=False)
                submissions[names] = res_file.text

    currentDate = currentDate - one_day

print(len(submissions), "groupes différents ont soumis")

# Compter le nombre d'étudiants
nb_sub_students = sum([len(names.split("-")) for names in submissions.keys()])
print(nb_sub_students, "étudiants ont soumis. ", nb_students, "auraient dû soumettre")

# Enregistrer les fichiers
for filename,text in submissions.items():
    with open(os.path.join(args.destination, filename), "w") as output:
        # On utilise des commentaires python pour l'en-tête de 6 lignes
        i = 0
        lines = text.split("\n", 6)
        for line in lines[:6]:
            output.write("# " + line + "\n")
        output.write(lines[6])

# Tester la syntaxe
if args.syntax:
    print("Test de la syntaxe des soumissions")
    compiled = dict()# To get a better display of passing and not passing submissions
    print("=== Erreurs ===")
    for filename in submissions.keys():
        cfile = py_compile.compile(os.path.join(args.destination, filename))
        compiled[filename] = cfile == None
    print("=== Résumé ===")
    for filename, passed in compiled.items():
        print(filename, ": ", passed)

    # Python considère que True est 1 et False est 0
    print(sum(compiled.values()), "soumissions comportent des erreurs de syntaxe : ")
    for filename, v in filter(lambda pair : not pair[1], compiled.items()):
        print(filename, end=' ')


print("\nBonne correction :) !")
