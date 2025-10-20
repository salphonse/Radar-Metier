# Test en local:

## CRéer un environnement virtuel pour Python:
> python -m venv venv
### L'actier (sur Windows)
> .\venv\Scripts\activate 
### L'activer (sur Linux et Mac Os X)
> source ./venv/bin/activate
> pip freeze > requirements.txt
> pip install -r requirements.txt
> uvicorn main:app --reload

## Exemple de commandes utilisées avec GitHub:
> git clone https://github.com/salphonse/Radar-Metier
> git add . 
> git commit -m "Ajout de nouveaux fichiers"
> git push origin main

## Documentation Docker pour ajouter variables d'environnement:
https://docs.docker.com/reference/dockerfile/#env

# Pour tester l'API en local:
uvicorn main:app --host "0.0.0.0" --port 8000

## Pour construire l'image, utilisez la commande suivante dans le terminal :
> docker build -t petit-bout-job-api .

## Pour lancer le conteneur, utilisez la commande suivante :
> docker run -d -p 127.0.0.1:8000:8000 petit-bout-job-api
