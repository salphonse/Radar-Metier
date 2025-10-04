-- Create schema
CREATE SCHEMA IF NOT EXISTS radarmetier;

-- Select default schema
SET search_path TO radarmetier;

-- Set default date format
SET datestyle = 'ISO, DMY';


-- Table Hard Skill
CREATE TABLE IF NOT EXISTS hard_skills(
	id_hard_skills SERIAL PRIMARY KEY, 
	cathegorie TEXT, 
	description TEXT
);

-- Table lien Formulaire/Hard Skills
CREATE TABLE IF NOT EXISTS lien_formulaire_hard_skills(
	id_lien_formulaire_hard_skills SERIAL PRIMARY KEY, 
	id_utilisateur_formulaire INTEGER, 
	id_hard_skills INTEGER
);

-- Table Soft Skill
CREATE TABLE IF NOT EXISTS soft_skills(
	id_soft_skills SERIAL PRIMARY KEY, 
	cathegorie TEXT, 
	description TEXT
);

-- Table lien Formulaire/Soft Skills
CREATE TABLE IF NOT EXISTS lien_formulaire_soft_skills(
	id_lien_formulaire_soft_skills SERIAL PRIMARY KEY, 
	id_utilisateur_formulaire INTEGER, 
	id_soft_skills INTEGER
);

-- Table Langue
CREATE TABLE IF NOT EXISTS langue(
	id_langue SERIAL PRIMARY KEY, 
	code_langue TEXT,
	nom_langue TEXT
);

-- Table Lien Formulaire/Langue
CREATE TABLE IF NOT EXISTS lien_formulaire_langue(
	id_lien_formulaire_langue SERIAL PRIMARY KEY, 
	id_utilisateur_formulaire INTEGER, 
	id_langue INTEGER, 
	niveau_ecrit TEXT, 
	niveau_oral TEXT
);

-- Table Utilisateur
CREATE TABLE IF NOT EXISTS utilisateur(
	id_utilisateur SERIAL PRIMARY KEY,
	nom TEXT,
	prenom TEXT,
	email TEXT,
	code_postal TEXT,
	ville TEXT,
	date_inscription TIMESTAMP,
	cle_connexion TEXT
);

-- DROP TABLE public.utilisateur_formulaire;

-- Table contenant les données du formulaire utilisateur
CREATE TABLE IF NOT EXISTS utilisateur_formulaire(
	id_utilisateur_formulaire SERIAL PRIMARY KEY,
	id_utilisateur INTEGER,
	profession_actuelle	TEXT,
	profession_visee TEXT,
	secteur_activite_actuel TEXT,	
	secteurs_activites_recherches JSON,	
	competences_actuelles JSON,
	appetences_professionnelles JSON,	
	inappetences_professionnelles JSON,	
	secteur_geographique_recherche TEXT, -- Région, Dep., Ville
	experiences_Extra_professionnelles JSON, 
	experiences_professionnelles JSON,	
	formations_utilisateur JSON,
	formations_recherchees JSON,
	projets_professionnel JSON
	);
