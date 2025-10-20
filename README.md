# Radar-Metier

## Description
Application web 

Ce guide explique comment installer **Git** et **Python**, puis cloner et exécuter le projet en local.

## Préparation de l'environnement:

### 🐍 1. Installer Python
```
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3-venv
```

Vous pouvez vérifier ou est installé Python avec cette commande:
```
where python
```

### 🐈‍⬛ 2. Installer Git
```
sudo apt install git-all
```


## Pré-requis de ce projet

### 📂 1. Cloner le repo GitHub
```
cd ~/Workspace
git clone git@github.com:salphonse/Radar-Metier.git
```

### 📦 2. Créer un environement virtuel Python
```
cd ~/Workspace/Radar-Metier
python3 -m venv venv
source venv/bin/activate
```

### 🧩 3. Installer les paquets requis
```
python3 -m pip install -r requirements.txt
```
Vous pouvez vérifier la liste des paquets installés:
```
python3 -m pip list
```

## Configurer les accès
### ⚙️ Créer un fichier .env
Il faut créer un fichier `.env` dans le répertoire `settings` afin de stocker les informations sensibles tel que les clés d'accès.
Il doit contenir les information suivantes:
```
# PostgreSQL - supabase.com
DB_USER=postgres.xxxxxxxxxxxxxx
DB_PASSWORD=********
DB_HOST=aws-0-eu-west-3.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_SCHEMA=radarmetier

# S3 Supabase
S3_ACCESS_KEY_ID = 0123456789ABCDEF0123456789ABCDEF
S3_SECRET_ACCESS_KEY = 0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
S3_ENDPOINT_URL = https://bhckzdwrhhfaxbidmwpm.supabase.co/storage/v1/s3
S3_REGION = eu-west-3
```

## La base de données
### 💾 Importation des données

Suivez les instructions du README pour initialiser la base de ddonnées et importer les données ROME:
[https://github.com/salphonse/Radar-Metier/tree/main/script/import_rome](https://github.com/salphonse/Radar-Metier/tree/main/script/import_rome)  


## Accéder à l'API industrialisée
### 🤖 Modèle de Machine Learning
Pour accéder au dépot de l'industrialisation du modèle ML:

API : [https://github.com/salphonse/Radar-Metier-ML/tree/Back-end](https://github.com/salphonse/Radar-Metier-ML/tree/Back-end)  
Front : [https://github.com/salphonse/Radar-Metier-ML/tree/Front-end](https://github.com/salphonse/Radar-Metier-ML/tree/Front-end)  

### 🤖 Modèle de Deep Learning
Pour accéder au dépot de l'industrialisation du modèle DL:

API : [https://github.com/salphonse/Radar-Metier/tree/main/Industrialisation/back-end](https://github.com/salphonse/Radar-Metier/tree/main/Industrialisation/back-end)  
Front : [https://github.com/salphonse/Radar-Metier/tree/main/Industrialisation/front-end](https://github.com/salphonse/Radar-Metier/tree/main/Industrialisation/front-end)  

