-- -------------------------------------------------------------------------------------
-- Arborescence CR (Code Rome) / GD (Grand Domaine) / DP (Domaine Professionnel)
-- -------------------------------------------------------------------------------------
SELECT code_grand_domaine, intitule
FROM radarmetier.cr_gd_dp_appellations
WHERE code_grand_domaine is not null 
AND code_domaine_professionnel is null 
and numero_fiche_rome is null
order by code_grand_domaine
;

SELECT code_grand_domaine, code_domaine_professionnel, intitule
FROM radarmetier.cr_gd_dp_appellations
WHERE code_grand_domaine is not null 
AND code_domaine_professionnel is not null 
and numero_fiche_rome is null
order by code_grand_domaine, code_domaine_professionnel
;

SELECT code_grand_domaine, code_domaine_professionnel, numero_fiche_rome, intitule, type_provenance, ogr_rome
FROM radarmetier.cr_gd_dp_appellations
WHERE code_grand_domaine is not null 
AND code_domaine_professionnel is not null 
and numero_fiche_rome is not null
order by code_grand_domaine, code_domaine_professionnel, numero_fiche_rome;

SELECT code_grand_domaine, code_domaine_professionnel, numero_fiche_rome, intitule, libelle_appellation_long, libelle_appellation_court, type_provenance, code_fiche, ogr_rome, ogr_appellation
FROM radarmetier.cr_gd_dp_appellations
WHERE code_grand_domaine is null 
AND code_domaine_professionnel is null 
and numero_fiche_rome is null
and ogr_rome is not null
order by ogr_rome;

-- -------------------------------------------------------------------------------------
-- V1: Test 
SELECT tbl_updated.code_grand_domaine, tbl_src.code_grand_domaine, 
tbl_updated.code_domaine_professionnel, tbl_src.code_domaine_professionnel, 
tbl_updated.numero_fiche_rome, tbl_src.numero_fiche_rome
FROM radarmetier.cr_gd_dp_appellations as tbl_updated
inner join (SELECT code_grand_domaine, code_domaine_professionnel, numero_fiche_rome, intitule, type_provenance, ogr_rome
   FROM radarmetier.cr_gd_dp_appellations
   WHERE code_grand_domaine is not null 
   AND code_domaine_professionnel is not null 
   and numero_fiche_rome is not null) as tbl_src ON( tbl_updated.ogr_rome = tbl_src.ogr_rome)
WHERE tbl_updated.code_grand_domaine is null 
AND tbl_updated.code_domaine_professionnel is null 
and tbl_updated.numero_fiche_rome is null
and tbl_updated.ogr_rome is not null
;

UPDATE radarmetier.cr_gd_dp_appellations 
SET code_grand_domaine = tbl_src.code_grand_domaine, 
code_domaine_professionnel = tbl_src.code_domaine_professionnel, 
numero_fiche_rome = tbl_src.numero_fiche_rome
from (SELECT code_grand_domaine, code_domaine_professionnel, numero_fiche_rome, intitule, type_provenance, ogr_rome
   FROM radarmetier.cr_gd_dp_appellations
   WHERE code_grand_domaine is not null 
   AND code_domaine_professionnel is not null 
   and numero_fiche_rome is not null) as tbl_src
WHERE radarmetier.cr_gd_dp_appellations.code_grand_domaine is null 
AND radarmetier.cr_gd_dp_appellations.code_domaine_professionnel is null 
and radarmetier.cr_gd_dp_appellations.numero_fiche_rome is null
and radarmetier.cr_gd_dp_appellations.ogr_rome is not null
and radarmetier.cr_gd_dp_appellations.ogr_rome = tbl_src.ogr_rome
;

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


-- ALTER TABLE radarmetier.rome_domaine_professionnel ALTER COLUMN code_domaine_professionnel SET NOT NULL;

-- Select schema
SET search_path TO radarmetier;

-- Alter table 'rome_grand_domaine'
ALTER TABLE rome_grand_domaine ADD PRIMARY KEY (code_grand_domaine);

-- Alter table 'rome_domaine_professionnel'
ALTER TABLE rome_domaine_professionnel ADD PRIMARY KEY (code_domaine_professionnel);
ALTER TABLE rome_domaine_professionnel ADD COLUMN IF NOT EXISTS code_grand_domaine CHAR NULL;
CREATE INDEX IF NOT EXISTS rome_domaine_professionnel_code_grand_domaine_idx ON rome_domaine_professionnel (code_grand_domaine);
UPDATE rome_domaine_professionnel SET code_grand_domaine = LEFT(code_domaine_professionnel, 1);

-- Alter table 'rome_referentiel_appellation'
ALTER TABLE rome_referentiel_appellation ADD PRIMARY KEY (code_ogr);
CREATE INDEX IF NOT EXISTS rome_referentiel_appellation_code_rome_idx ON rome_referentiel_appellation (code_rome);
CREATE INDEX IF NOT EXISTS rome_referentiel_appellation_code_domaine_professionnel_idx ON rome_referentiel_appellation (code_domaine_professionnel);
ALTER TABLE rome_referentiel_appellation DROP COLUMN IF EXISTS code_domaine_professionnel;
ALTER TABLE rome_referentiel_appellation ADD COLUMN IF NOT EXISTS code_domaine_professionnel TEXT NULL;
UPDATE rome_referentiel_appellation SET code_domaine_professionnel = LEFT(code_rome, 3);

-- Alter table 'rome_referentiel_code_rome'
ALTER TABLE rome_referentiel_code_rome ADD PRIMARY KEY (code_rome);
CREATE INDEX IF NOT EXISTS rome_referentiel_code_rome_code_ogr_idx ON rome_referentiel_code_rome (code_ogr);

-- Alter table 'rome_item'
ALTER TABLE rome_item ADD PRIMARY KEY (code_ogr);
ALTER TABLE rome_item ALTER COLUMN code_rubrique TYPE int8 USING code_rubrique::int8;
CREATE INDEX IF NOT EXISTS rome_item_code_rubrique_idx ON rome_item (code_rubrique);


-- Alter table 'rome_texte'
CREATE INDEX IF NOT EXISTS rome_texte_code_rome_idx ON rome_texte (code_rome);

-- Alter table 'rome_centre_interet'
ALTER TABLE rome_centre_interet ADD PRIMARY KEY (code_centre_interet);

-- Alter table 'rome_arborescence_centre_interet'
CREATE INDEX IF NOT EXISTS rome_arborescence_centre_interet_code_centre_interet_idx ON rome_arborescence_centre_interet (code_centre_interet);
CREATE INDEX IF NOT EXISTS rome_arborescence_centre_interet_code_rome_idx ON rome_arborescence_centre_interet (code_rome);

-- Alter table 'rome_descriptif_rubrique'
ALTER TABLE rome_descriptif_rubrique ADD PRIMARY KEY (code_rubrique);

-- Alter table 'rome_referentiel_competence'
ALTER TABLE rome_referentiel_competence ADD PRIMARY KEY (code_ogr);
ALTER TABLE rome_referentiel_competence ALTER COLUMN code_ogr_macro_comp TYPE int8 USING code_ogr_macro_comp::int8;



-- Add foreign key
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



-- Test doublon
select code_ogr, count(*) from rome_referentiel_appellation group by code_ogr having count(*) > 1;

select code_ogr, count(*) from rome_referentiel_competence group by code_ogr having count(*) > 1;

