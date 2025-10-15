READ ME — Extraction API CPF \& France Travail





OBJECTIF



Automatiser la récupération et la mise en forme de deux sources publiques :



* Catalogue CPF via l’Open Data de la Caisse des Dépôts
* Offres d’emploi via l’API France Travail (ex Pôle Emploi)



Ces scripts produisent des fichiers CSV exploitables pour analyses, tableaux de bord ou intégrations.





CONTENU DU PROJET



* api\_catalogue\_CPF.py -> Extraction du catalogue des formations CPF
* credentials.txt -> Identifiants API France Travail (client/secret)
* request\_FT.py -> Extraction des offres d’emploi France Travail
* formations\_cpf\_paginated.csv -> Résultat de l’extraction CPF
* offres\_emploi.csv -> Résultat de l’extraction France Travail





INSTALLATION



* Cloner le dossier ou copier les fichiers.



&nbsp;	git clone <repo\_url>

&nbsp;	cd <repo>



* Installer les dépendances.

&nbsp;	pip install requests pandas



* Créer le fichier credentials.txt (non versionné) :

&nbsp;	CLIENT\_ID=VotreClientID

&nbsp;	CLIENT\_SECRET=VotreSecret



IMPORTANT : Ne pas partager ce fichier. Utiliser des variables d’environnement si possible.





FONCTIONNEMENT



* Script : api\_catalogue\_CPF.py



&nbsp;	But : interroger l’API Open Data “Mon Compte Formation” et produire un CSV.



&nbsp;	Étapes :

&nbsp;		Appel API : https://opendata.caissedesdepots.fr/api/records/1.0/search/

&nbsp;		Pagination automatique par blocs de 100

&nbsp;		Agrégation des résultats via Pandas

&nbsp;		Export du fichier formations\_cpf\_paginated.csv



&nbsp;	Paramètres internes :

&nbsp;		rows\_per\_page = 100

&nbsp;		max\_records = 10000

&nbsp;		dataset = moncompteformation\_catalogueformation



&nbsp;	Résultat : fichier CSV avec une ligne par formation.



* Script : request\_FT.py



&nbsp;	But : récupérer des offres d’emploi France Travail.



&nbsp;	Étapes :

&nbsp;		Lecture du fichier credentials.txt

&nbsp;		Authentification OAuth2 (client\_credentials)

&nbsp;		Requête API : https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search

&nbsp;		Filtrage par mots-clés et région

&nbsp;		Export du fichier offres\_emploi.csv



&nbsp;	Paramètres par défaut :

&nbsp;		motsCles = "développeur python"

&nbsp;		region = "11" (Île-de-France)

&nbsp;		range = "0-19" (20 offres)



&nbsp;	Colonnes exportées :

&nbsp;		Intitulé, Lieu, Entreprise, Date de publication, Description, URL





UTILISATION



* Extraire le catalogue CPF :

&nbsp;	python api\_catalogue\_CPF.py

&nbsp;	--> Produit formations\_cpf\_paginated.csv



* Extraire les offres d’emploi :

&nbsp;	python request\_FT.py

&nbsp;	--> Produit offres\_emploi.csv





PERSONNALISATION RAPIDE



* Modifier les filtres France Travail :

params = {

"motsCles": "data engineer",

"region": "93",

"range": "0-49",

}



* Étendre la pagination :

for start in range(0, 500, 100):

params\["range"] = f"{start}-{start+99}"

\# GET + concaténation des résultats



* Filtrer le catalogue CPF :

params = {

"dataset": dataset,

"rows": rows\_per\_page,

"start": start,

"q": "python",

}





BONNES PRATIQUES



* Ne jamais versionner credentials.txt.
* Encodage UTF-8-SIG pour compatibilité Excel.
* Gérer les quotas d’API (ajouter time.sleep() si besoin).
* Vérifier l’existence des champs avec .get(..., "").
* Rendre les paramètres dynamiques via variables d’environnement ou arguments CLI.





AMÉLIORATIONS POSSIBLES



* Pagination automatique complète pour France Travail.
* Journalisation horodatée.
* Ajout de filtres thématiques CPF (numérique, santé, etc.).
* Gestion de configuration via .env + python-dotenv.
* Automatisation planifiée (cron, GitHub Actions).





SOURCES OFFICIELLES



* API France Travail : https://api.gouv.fr/les-api/api-france-travail
* Open Data CPF : https://opendata.caissedesdepots.fr/pages/moncompteformation/





LICENCE ET DROITS



Projet éducatif / démonstratif.



Les données appartiennent à leurs sources :

* Caisse des Dépôts — API Mon Compte Formation
* France Travail — API Offres d’emploi
