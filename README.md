# Radar-Metier
Radar métier permet d'orienter les personnes en recherche de formation ou d'emploi

Add SQL User:
CREATE ROLE load_user WITH
	LOGIN
	SUPERUSER
	CREATEDB
	CREATEROLE
	INHERIT
	NOREPLICATION
	BYPASSRLS
	CONNECTION LIMIT -1
	PASSWORD 'xxxxxx';
COMMENT ON ROLE load_user IS 'Load data user';

Préparation de l'environnement:
# Installer Python
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3-venv

# Vérifier ou est installé Python
where python

# Créer un environement virtuel
cd myproject
python3 -m venv venv
source venv/bin/activate

# Lister les paquets installés
python3 -m pip list

# Installer les paquets requis
python3 -m pip install -r requirements.txt

# Mise à jour des dépendances
python3 -m pip install --upgrade -r requirements.txt

python3 -m pip install sqlalchemy