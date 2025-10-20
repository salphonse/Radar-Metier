# RADAR_METIER – Interface Front-End
## Objectif

RADAR_METIER est une application web interactive permettant de prédire un métier à partir des compétences sélectionnées.
Cette interface (HTML / CSS / JavaScript) communique directement avec une API FastAPI hébergée sur Render pour fournir les résultats de prédiction.

# Lien render pour interface web: https://radar-metier-zh10.onrender.com/

## Structure du projet
```
frontend/
├── index.html          # Page principale de l'application
├── style.css           # Feuille de style principale
├── script.js           # Logique côté client (interaction avec l'API)
└── README.md           # Documentation du front-end
```

Installation et exécution en local
Cloner le projet
git clone https://github.com/ton-compte/radar_metier_frontend.git
cd radar_metier_frontend

# Lancer le projet en local

Le projet est statique et ne nécessite aucun serveur backend.
Plusieurs options sont possibles :

Option 1 : Ouvrir directement index.html

Double-clique sur le fichier index.html pour l’ouvrir dans le navigateur.
Cette méthode peut poser des problèmes CORS si l’API est appelée directement depuis le disque.

Option 2 : Utiliser VS Code avec “Go Live”

Ouvre le projet dans Visual Studio Code

Installe l’extension Live Server si nécessaire

Clique sur “Go Live” en bas à droite

L’application sera accessible à l’adresse :

http://localhost:5500

Option 3 : Utiliser un serveur local Python
python -m http.server 8000


Puis ouvrir le navigateur à l’adresse :

http://localhost:8000

## Déploiement sur Render
1. Créer un site statique

Connecte-toi sur https://render.com

Clique sur “New +” → “Static Site”

Connecte ton dépôt GitHub contenant le front-end

2. Paramètres Render

| Paramètre	| Valeur |
|-----------|--------|
| Root Directory | / |
| Publish Directory | / |
| Build Command | (laisser vide) |
| Environment | Static Site |

## Détails techniques

Technologies : HTML5, CSS3, JavaScript (Vanilla)

Design : Thème sombre avec effets lumineux et animations



## Fonctionnalités principales :

Sélection dynamique des domaines, macro-compétences et compétences

Gestion interactive des compétences sélectionnées

Appel API vers le backend

Affichage des métiers prédits avec indice de fiabilité



Auteur

Projet : RADAR_METIER
Développé par : Equipe M2i - 0325 
Année : 2025
