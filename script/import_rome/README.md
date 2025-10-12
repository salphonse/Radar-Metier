# Intégration des données ROME du Data lake (S3) au Data warehouse (PostgreSQL)

## 1 - Initialiser la base de données RADAR-METIER
Une fois la base de données créée et accessible, utiliser les commandes du fichier sql/init_database.sql.

## 2 - Installer les package Python nécessaires
pip install -r requirements.txt

## 3 - Intégration des données ROME
Lancer le script Python import_rome.py (ou utiliser le Notebook import_rome.ipynb)

## 4 - Lier les tables entre elles
Utiliser les commandes du fichier sql/transform_rome.sql afin de créer les clés primaires et les clés étrangères.
