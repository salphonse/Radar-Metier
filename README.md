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
python -m pip install sqlalchemy