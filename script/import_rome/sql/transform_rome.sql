-- -------------------------------------------------------------------------------------
-- Prepare ROME data
-- -------------------------------------------------------------------------------------

-- -------------------------------------------------------------------------------------
-- Table description
-- -------------------------------------------------------------------------------------
-- grand_domaine: 14 grands domaines des codes ROME.
-- domaine_professionnel: 110 domaines professionnels des code ROME.
-- referentiel_appellation: Liste des métiers pour chaque code ROME.
-- referentiel_code_rome: Liste de tous les code ROME.
-- texte: Descriptif de chaque métier et de son accès.

-- rubrique_mobilite: Compatibilité d'un code ROME avec les metiers ciblés.
-- centre_interet: 30 principaux centres d'interet.
-- arborescence_centre_interet: Codes ROME liés à chaque centre d'interet.
-- referentiel_competence: Liste des compétences pregroupées par macro-compétence.
-- item: Définition des compétences
-- descriptif_rubrique: Liste des rubriques (Savoir-faire, Savoir-être professionnels, Savoirs)

-- Create schema
CREATE SCHEMA IF NOT EXISTS radarmetier;
-- Select default schema
SET search_path TO radarmetier;
-- Set default date format
SET datestyle = 'ISO, DMY';

-- Alter table 'rome_grand_domaine'
-- Add primary key
ALTER TABLE rome_grand_domaine ADD PRIMARY KEY (code_grand_domaine);

-- Alter table 'rome_domaine_professionnel'
-- Add primary key
ALTER TABLE rome_domaine_professionnel ADD PRIMARY KEY (code_domaine_professionnel);
-- Add column 'code_grand_domaine'
ALTER TABLE rome_domaine_professionnel ADD COLUMN IF NOT EXISTS code_grand_domaine CHAR NULL;
-- Create index on 'code_grand_domaine' column
CREATE INDEX IF NOT EXISTS rome_domaine_professionnel_code_grand_domaine_idx ON rome_domaine_professionnel (code_grand_domaine);
-- Set value for each row
UPDATE rome_domaine_professionnel SET code_grand_domaine = LEFT(code_domaine_professionnel, 1);

-- Alter table 'rome_referentiel_appellation'
-- Add primary key
ALTER TABLE rome_referentiel_appellation ADD PRIMARY KEY (code_ogr);
-- Create index on 'code_rome' column
CREATE INDEX IF NOT EXISTS rome_referentiel_appellation_code_rome_idx ON rome_referentiel_appellation (code_rome);

-- Add column 'code_domaine_professionnel'
ALTER TABLE rome_referentiel_appellation ADD COLUMN IF NOT EXISTS code_domaine_professionnel TEXT NULL;
-- Create index on 'code_domaine_professionnel' column
CREATE INDEX IF NOT EXISTS rome_referentiel_appellation_code_domaine_professionnel_idx ON rome_referentiel_appellation (code_domaine_professionnel);
-- Set value for each row
UPDATE rome_referentiel_appellation SET code_domaine_professionnel = LEFT(code_rome, 3);

-- Alter table 'rome_referentiel_code_rome'
-- Add primary key
ALTER TABLE rome_referentiel_code_rome ADD PRIMARY KEY (code_rome);
-- Create index on 'code_ogr' column
CREATE INDEX IF NOT EXISTS rome_referentiel_code_rome_code_ogr_idx ON rome_referentiel_code_rome (code_ogr);

-- Alter table 'rome_item'
-- Add primary key
ALTER TABLE rome_item ADD PRIMARY KEY (code_ogr);
-- Change 'code_rubrique' column type to INT8 to matching with 'code_item.code_rubrique' column
ALTER TABLE rome_item ALTER COLUMN code_rubrique TYPE int8 USING code_rubrique::int8;
-- Create index on 'code_rubrique' column
CREATE INDEX IF NOT EXISTS rome_item_code_rubrique_idx ON rome_item (code_rubrique);

-- Alter table 'rome_texte'
-- Create index on 'code_rome' column
CREATE INDEX IF NOT EXISTS rome_texte_code_rome_idx ON rome_texte (code_rome);

-- Alter table 'rome_centre_interet'
-- Add primary key
ALTER TABLE rome_centre_interet ADD PRIMARY KEY (code_centre_interet);

-- Alter table 'rome_arborescence_centre_interet'
-- Create index on 'code_centre_interet' column
CREATE INDEX IF NOT EXISTS rome_arborescence_centre_interet_code_centre_interet_idx ON rome_arborescence_centre_interet (code_centre_interet);
-- Create index on 'code_rome' column
CREATE INDEX IF NOT EXISTS rome_arborescence_centre_interet_code_rome_idx ON rome_arborescence_centre_interet (code_rome);

-- Alter table 'rome_descriptif_rubrique'
-- Add primary key
ALTER TABLE rome_descriptif_rubrique ADD PRIMARY KEY (code_rubrique);

-- Alter table 'rome_referentiel_competence'
-- Add primary key
ALTER TABLE rome_referentiel_competence ADD PRIMARY KEY (code_ogr);
-- Change 'code_ogr_macro_comp' column type to INT8 to matching with 'rome_referentiel_competence.code_ogr' column
ALTER TABLE rome_referentiel_competence ALTER COLUMN code_ogr_macro_comp TYPE int8 USING code_ogr_macro_comp::int8;


-- -------------------------------------------------------------------------------------
-- Add foreign key
-- -------------------------------------------------------------------------------------

ALTER TABLE rome_domaine_professionnel ADD CONSTRAINT rome_domaine_professionnel_rome_grand_domaine_fk
  FOREIGN KEY (code_grand_domaine) REFERENCES rome_grand_domaine(code_grand_domaine);

ALTER TABLE rome_referentiel_appellation ADD CONSTRAINT rome_referentiel_appellation_rome_domaine_professionnel_fk 
  FOREIGN KEY (code_domaine_professionnel) REFERENCES rome_domaine_professionnel(code_domaine_professionnel);
ALTER TABLE rome_referentiel_appellation ADD CONSTRAINT rome_referentiel_appellation_rome_referentiel_code_rome_fk 
  FOREIGN KEY (code_rome) REFERENCES rome_referentiel_code_rome(code_rome);

ALTER TABLE rome_texte ADD CONSTRAINT rome_texte_rome_referentiel_code_rome_fk 
  FOREIGN KEY (code_rome) REFERENCES rome_referentiel_code_rome(code_rome);

ALTER TABLE rome_item ADD CONSTRAINT rome_item_rome_descriptif_rubrique_fk 
  FOREIGN KEY (code_rubrique) REFERENCES rome_descriptif_rubrique(code_rubrique);

ALTER TABLE rome_arborescence_centre_interet ADD CONSTRAINT rome_arborescence_centre_interet_rome_centre_interet_fk 
  FOREIGN KEY (code_centre_interet) REFERENCES rome_centre_interet(code_centre_interet);
ALTER TABLE rome_arborescence_centre_interet ADD CONSTRAINT rome_arborescence_centre_interet_referentiel_code_rome_fk 
  FOREIGN KEY (code_rome) REFERENCES rome_referentiel_code_rome(code_rome);

ALTER TABLE rome_rubrique_mobilite ADD CONSTRAINT rome_rubrique_mobilite_rome_referentiel_code_rome_fk 
  FOREIGN KEY (code_rome) REFERENCES rome_referentiel_code_rome(code_rome);

ALTER TABLE rome_referentiel_competence ADD CONSTRAINT rome_referentiel_competence_rome_item_code_ogr_fk 
  FOREIGN KEY (code_ogr_macro_comp) REFERENCES rome_item(code_ogr);

-- -------------------------------------------------------------------------------------
-- End of file
-- -------------------------------------------------------------------------------------
