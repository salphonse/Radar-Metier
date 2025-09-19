# Radar-Metier
Radar métier permet d'orienter les personnes en recherche d'une' formation ou d'un emploi.

# Préparation de l'environnement:
## Installer Python
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3-venv

## Vérifier ou est installé Python
where python

## Créer un environement virtuel
cd myproject
python3 -m venv venv
source venv/bin/activate

## Lister les paquets installés
python3 -m pip list

## Installer les paquets requis
python3 -m pip install -r requirements.txt

## Mise à jour des dépendances
python3 -m pip install --upgrade -r requirements.txt