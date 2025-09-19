## Pour construire l'image, utilisez la commande suivante dans le terminal :
> docker build -t petit-bout-job-api .

## Pour lancer le conteneur, utilisez la commande suivante :
> docker run -d -p 8000:8000 petit-bout-job-api
> python -m venv venv
### Pour Windows
> .\venv\Scripts\activate 
### Pour Linux et Mac Os X
> source ./venv/bin/activate
> pip freeze > requirements.txt
> pip install -r requirements.txt
> uvicorn main:app --reload

## Exemple de commandes utilisées avec GitHub:
> git clone https://github.com/Akuma-teck/Radarr-metier
> git add . 
> git commit -m "Ajout de nouveaux fichiers"
> git push origin main

## Documentation Docker pour ajouter variables d'environnement:
https://docs.docker.com/reference/dockerfile/#env