/***************************************************
 *   OUTILS POUR CREER DES MAILLES PERSONNALISEES  *
 ***************************************************/


/* Create required type */
DROP TYPE IF EXISTS public.T_GRID CASCADE
;

CREATE TYPE public.T_GRID AS (
    gcol INT4,
    grow INT4,
    geom GEOMETRY
    );

/* Drop function is exists */
DROP FUNCTION IF EXISTS ref_geo.ST_SquareGrid(GEOMETRY, NUMERIC, NUMERIC, BOOLEAN);

/* Now create the function */
CREATE OR REPLACE FUNCTION ref_geo.ST_SquareGrid(p_geometry GEOMETRY, p_TileSizeX NUMERIC, p_TileSizeY NUMERIC
                                                , p_point BOOLEAN DEFAULT TRUE)
    RETURNS SETOF T_GRID AS
$BODY$
DECLARE
    v_mbr   GEOMETRY;
    v_srid  INT4;
    v_halfX NUMERIC := p_TileSizeX / 2.0;
    v_halfY NUMERIC := p_TileSizeY / 2.0;
    v_loCol INT4;
    v_hiCol INT4;
    v_loRow INT4;
    v_hiRow INT4;
    v_grid  T_GRID;
BEGIN
    IF (p_geometry IS NULL)
    THEN
        RETURN
        ;
    END IF;
    v_srid := ST_SRID(p_geometry);
    v_mbr := ST_Envelope(p_geometry);
    v_loCol := trunc((ST_XMIN(v_mbr) / p_TileSizeX) :: NUMERIC);
    v_hiCol := CEIL((ST_XMAX(v_mbr) / p_TileSizeX) :: NUMERIC) - 1;
    v_loRow := trunc((ST_YMIN(v_mbr) / p_TileSizeY) :: NUMERIC);
    v_hiRow := CEIL((ST_YMAX(v_mbr) / p_TileSizeY) :: NUMERIC) - 1;

    FOR v_col IN v_loCol..v_hiCol
        LOOP
            FOR v_row IN v_loRow..v_hiRow
                LOOP
                    v_grid.gcol := v_col;
                    v_grid.grow := v_row;

                    IF (p_point)
                    THEN
                        v_grid.geom := ST_SetSRID(
                                ST_MakePoint((v_col * p_TileSizeX) + v_halfX,
                                             (v_row * p_TileSizeY) + V_HalfY),
                                v_srid);
                    ELSE
                        v_grid.geom := ST_SetSRID(
                                ST_MakeEnvelope((v_col * p_TileSizeX),
                                                (v_row * p_TileSizeY),
                                                (v_col * p_TileSizeX) + p_TileSizeX,
                                                (v_row * p_TileSizeY) + p_TileSizeY),
                                v_srid);
                    END IF;
                    RETURN NEXT v_grid;
                END LOOP;
        END LOOP;
END;
$BODY$ LANGUAGE plpgsql
    IMMUTABLE
    COST 100
    ROWS 1000;

/*  Assign ownership */
    ALTER FUNCTION ref_geo.ST_SquareGrid(GEOMETRY, NUMERIC, NUMERIC, BOOLEAN)
    OWNER TO postgres;

/***********************************************
 * CREATION D'UN MAILLAGE DE 500m              *
 ***********************************************/

SELECT *
FROM ref_geo.bib_areas_types;

INSERT INTO ref_geo.bib_areas_types(type_name, type_code, type_desc)
VALUES ('Mailles0.5*0.5', 'M0.5', 'Mailles (non officielles de 500m basées sur le référentiel RGF93 - 2154)')

INSERT INTO ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date,
                            meta_update_date)
WITH area AS (SELECT st_simplify(st_union(geom), 100) AS geom
              FROM ref_geo.l_areas
--              WHERE LEFT(area_code, 2) IN ('01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'))
              WHERE LEFT(area_code, 2) IN ('07'))
SELECT bib_areas_types.id_type
     , 'Maille 500m l' || grow || 'c' || gcol AS NAME
     , 'l' || grow || 'c' || gcol             AS code
     , st_multi(sg.geom)                      AS geom
     , st_centroid(sg.geom)                   AS centroid
     , 'auto-généré'                          AS source
     , 'auto-genéré'                          AS comment
     , now()                                  AS tscreate
     , now()                                  AS tsupdate
FROM ref_geo.ST_SquareGrid(
            (SELECT geom FROM area)
    , 500
    , 500
    , FALSE) AS sg
   , ref_geo.bib_areas_types
   , area
WHERE type_code LIKE 'M0.5'
  AND st_intersects(st_buffer(area.geom, 1000), sg.geom)
;

DROP TABLE IF EXISTS public.test;
CREATE TABLE public.test AS
WITH area AS (SELECT st_simplify(st_union(geom), 100) AS geom
              FROM ref_geo.l_areas
--              WHERE LEFT(area_code, 2) IN ('01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'))
              WHERE LEFT(area_code, 2) IN ('07'))
SELECT row_number() OVER ()                   AS id
     , bib_areas_types.id_type
     , 'Maille 500m l' || grow || 'c' || gcol AS name
     , 'l' || grow || 'c' || gcol             AS code
     , sg.geom                                AS geom
     , st_centroid(sg.geom)                   AS centroid
     , 'auto-généré'                          AS source
     , 'auto-genéré'                          AS comment
     , now()                                  AS tscreate
     , now()                                  AS tsupdate
FROM ref_geo.ST_SquareGrid(
            (SELECT geom FROM area)
    , 500
    , 500
    , FALSE) AS sg
   , ref_geo.bib_areas_types
   , area
WHERE type_code LIKE 'M0.5'
  AND st_intersects(st_buffer(area.geom, 1000), sg.geom)
;

ALTER TABLE public.test
    ADD PRIMARY KEY (id);
CREATE INDEX ON public.test USING gist (geom);
CREATE INDEX ON public.test USING gist (centroid);

SELECT populate_geometry_columns();



/*******************************
 *   TERRITORY GENERAL STATS   *
 *******************************/

-- UPDATE gn_synthese.synthese
-- SET
--     the_geom_local = the_geom_local;

INSERT INTO gn_synthese.cor_area_synthese (id_synthese, id_area)
SELECT s.id_synthese AS id_synthese
     , a.id_area     AS id_area
FROM ref_geo.l_areas a
         JOIN gn_synthese.synthese s ON public.ST_INTERSECTS(s.the_geom_local, a.geom)
WHERE a.id_type = (SELECT id_type FROM ref_geo.bib_areas_types WHERE type_code LIKE 'M0.5');



DROP
    MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
    -- (
-- WITH
--     observers AS (
--         SELECT DISTINCT
--             cor_area_synthese.id_area
--           , unaccent(trim(regexp_split_to_table(synthese.observers, ','))) AS observer
--         FROM
--             gn_synthese.synthese
--                 JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
--     )
SELECT l_areas.id_area
     , bib_areas_types.type_code
     , l_areas.area_code
     , l_areas.area_name
     , count(DISTINCT synthese.cd_nom)      AS count_taxa
     , count(DISTINCT synthese.id_synthese) AS count_occtax
     , count(DISTINCT synthese.id_dataset)  AS count_dataset
     , count(DISTINCT synthese.date_min)    AS count_date
     , count(DISTINCT synthese.observers)   AS count_observer
     , max(date_min)                        AS last_obs
     , l_areas.geom                         AS geom_local
     , st_transform(l_areas.geom, 4326)     AS geom_4326
FROM ref_geo.l_areas
         JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
         JOIN gn_synthese.cor_area_synthese ON l_areas.id_area = cor_area_synthese.id_area
         JOIN gn_synthese.synthese ON cor_area_synthese.id_synthese = synthese.id_synthese
--         JOIN observers ON observers.id_area = l_areas.id_area
GROUP BY l_areas.id_area
       , bib_areas_types.type_code
       , l_areas.area_code
       , l_areas.area_name
       , l_areas.geom;


CREATE UNIQUE INDEX ON gn_biodivterritory.mv_territory_general_stats (id_area);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (type_code);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (area_name);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (area_code);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist (geom_local);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist (geom_4326);

SELECT populate_geometry_columns();

SELECT type_code, count(*)
FROM gn_synthese.cor_area_synthese
         JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
         JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
GROUP BY type_code;


DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_area_ntile_limit CASCADE;
CREATE MATERIALIZED VIEW gn_biodivterritory.mv_area_ntile_limit AS
(
WITH occtax AS (
    SELECT id_area
         , type_code
         , count_occtax                          AS count
         , NTILE(5) OVER (ORDER BY count_occtax) AS ntile
    FROM gn_biodivterritory.mv_territory_general_stats)
   , taxa AS (
    SELECT id_area
         , type_code
         , count_taxa                          AS count
         , NTILE(5) OVER (ORDER BY count_taxa) AS ntile
    FROM gn_biodivterritory.mv_territory_general_stats)
   , observer AS (
    SELECT id_area
         , type_code
         , count_observer                          AS count
         , NTILE(5) OVER (ORDER BY count_observer) AS ntile
    FROM gn_biodivterritory.mv_territory_general_stats)
   , date AS (
    SELECT id_area
         , type_code
         , count_date                          AS count
         , NTILE(5) OVER (ORDER BY count_date) AS ntile
    FROM gn_biodivterritory.mv_territory_general_stats)
   , u AS (
    SELECT 'occtax' AS type, MIN(count) AS min, max(count) AS max, ntile
    FROM occtax
    GROUP BY ntile
    UNION
    SELECT 'taxa', MIN(count), max(count), ntile
    FROM taxa
    GROUP BY ntile
    UNION
    SELECT 'observer', MIN(count), max(count), ntile
    FROM observer
    GROUP BY ntile
    UNION
    SELECT 'date', MIN(count), max(count), ntile
    FROM date
    GROUP BY ntile
)
SELECT row_number() OVER () AS id, *
FROM u
ORDER BY type
       , ntile);


/*******************************
 *   Territory species list    *
 *******************************/


/* Création de la table de statuts BDC Statuts */
DROP TABLE IF EXISTS taxonomie.bib_bdc_type_statut;
CREATE TABLE taxonomie.bib_bdc_type_statut
(
    id_type_statut    VARCHAR(50) PRIMARY KEY NOT NULL,
    cd_type_statut    VARCHAR(50),
    lb_type_statut    VARCHAR(254),
    regroupement_type VARCHAR(254),
    thematique        VARCHAR(50),
    type_value        VARCHAR(20)
);


CREATE TABLE IF NOT EXISTS taxonomie.taxref_bdc_statuts
(
    id_taxref_bdc     SERIAL PRIMARY KEY,
    cd_nom            INTEGER REFERENCES taxonomie.taxref (cd_nom),
    cd_ref            INTEGER REFERENCES taxonomie.taxref (cd_nom),
    cd_sup            INTEGER REFERENCES taxonomie.taxref (cd_nom),
    cd_type_statut    VARCHAR(50) REFERENCES taxonomie.bib_bdc_type_statut (id_type_statut),
    lb_type_statut    VARCHAR(254),
    regroupement_type VARCHAR(100),
    code_statut       VARCHAR(10),
    label_statut      VARCHAR(50),
    rq_statut         VARCHAR(1000),
    cd_sig            VARCHAR(50),
    cd_doc            INTEGER,
    lb_nom            VARCHAR(50),
    lb_auteur         VARCHAR(254),
    nom_complet_html  VARCHAR(254),
    nom_valide_html   VARCHAR(254),
    regne             VARCHAR(50),
    phylum            VARCHAR(50),
    classe            VARCHAR(50),
    ordre             VARCHAR(50),
    famille           VARCHAR(50),
    group1_inpn       VARCHAR(50),
    group2_inpn       VARCHAR(50),
    lb_adm_tr         VARCHAR(50),
    niveau_admin      VARCHAR(50),
    cd_iso3166_1      VARCHAR(50),
    cd_iso3166_2      VARCHAR(50),
    full_citation     VARCHAR(50),
    doc_url           VARCHAR(254),
    thematique        VARCHAR(50),
    type_value        VARCHAR(50),
    id_area           INTEGER REFERENCES ref_geo.l_areas (id_area)
);


/* Déjà présent dans taxonomie.bib_taxref_categories_fr */
DROP TABLE IF EXISTS taxonomie.bib_redlist_categories;
CREATE TABLE taxonomie.bib_redlist_categories
(
    code_category  VARCHAR(2) PRIMARY KEY,
    sup_category   VARCHAR(30),
    threatened     boolean default false,
    priority_order INT,
    name_fr        varchar(100),
    desc_fr        varchar(254),
    name_en        varchar(100),
    desc_en        varchar(254)
);

INSERT INTO taxonomie.bib_redlist_categories(code_category, threatened, sup_category, priority_order)
SELECT DISTINCT id_categorie_france        AS code_category
              , CASE
                    WHEN id_categorie_france IN ('CR', 'EN', 'VU')
                        THEN TRUE
                    ELSE FALSE END         AS threatened
              , CASE
                    WHEN id_categorie_france IN ('CR', 'EN', 'VU')
                        THEN 'threatened'
                    WHEN id_categorie_france IN ('RE', 'EW', 'EX')
                        THEN 'extinct'
                    ELSE 'other' END       AS sup_category
              , CASE id_categorie_france
                    WHEN 'EX' THEN 10
                    WHEN 'EW' THEN 20
                    WHEN 'RE' THEN 30
                    WHEN 'CR' THEN 40
                    WHEN 'EN' THEN 50
                    WHEN 'VU' THEN 60
                    WHEN 'NT' THEN 70
                    WHEN 'LC' THEN 80
                    WHEN 'DD' THEN 90
                    WHEN 'NE' THEN 100
                    WHEN 'NA' THEN 110 end AS priority_order
FROM taxonomie.taxref_liste_rouge_fr;


CREATE TABLE taxonomie.bib_redlist_source
(
    id_source   serial primary key,
    name_source varchar(254),
    desc_source text,
    url_source  varchar(254),
    context     varchar(50),
    area_name   varchar(50),
    area_code   varchar(50),
    area_type   varchar(50),
    priority    INTEGER
);

/* Optional matching with */
create table taxonomie.cor_redlist_source_area
(
    id_cor_redlist_source_area serial primary key,
    id_area                    integer references ref_geo.l_areas (id_area),
    id_source                  integer references taxonomie.bib_redlist_source (id_source)
);

DROP TABLE IF EXISTS taxonomie.redlist;
CREATE TABLE taxonomie.redlist
(
    id_redlist   SERIAL  NOT NULL PRIMARY KEY,
    status_order INTEGER,
    cd_nom       INTEGER references taxonomie.taxref (cd_nom),
    cd_ref       INTEGER references taxonomie.taxref (cd_nom),
    category     CHAR(2) NOT NULL REFERENCES taxonomie.bib_taxref_categories_lr (id_categorie_france),
    criteria     VARCHAR(50),
    id_source    integer references taxonomie.bib_redlist_source (id_source)
);

ALTER TABLE taxonomie.red

/* Insertion de la source UICN France*/
insert into taxonomie.bib_redlist_source (name_source, area_code)
select distinct liste_rouge_source, 'FR'
from taxonomie.taxref_liste_rouge_fr;

insert into taxonomie.bib_redlist_source(name_source, area_code)
values ('Liste rouge mondiale des espèces menacées (2019.1)', 'WORLD'),
       ('Liste rouge européenne des espèces menacées (2019.1)', 'EUROPE');

insert into taxonomie.redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
select ordre_statut, taxref.cd_nom, taxref.cd_ref, id_categorie_france, criteres_france, id_source
from taxonomie.taxref_liste_rouge_fr
         join taxonomie.bib_redlist_source on liste_rouge_source = bib_redlist_source.name_source
         join taxonomie.taxref on taxref_liste_rouge_fr.cd_nom = taxref.cd_nom;

insert into taxonomie.redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
select ordre_statut,
       taxref.cd_nom,
       taxref.cd_ref,
       case
           when categorie_lr_mondiale like 'LR/%' then upper(right(categorie_lr_mondiale, 2))
           else categorie_lr_mondiale end as categorie_lr_mondiale,
       null,
       id_source
from taxonomie.taxref_liste_rouge_fr
         join taxonomie.taxref
              on taxref_liste_rouge_fr.cd_nom = taxref.cd_nom,
     (select id_source from taxonomie.bib_redlist_source where area_code like 'WORLD') as source
where length(categorie_lr_mondiale) > 0;


insert into taxonomie.redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
select ordre_statut,
       taxref.cd_nom,
       taxref.cd_ref,
       case
           when categorie_lr_europe like 'LR/%' then upper(right(categorie_lr_europe, 2))
           else categorie_lr_europe end as categorie_lr_mondiale,
       null,
       id_source
from taxonomie.taxref_liste_rouge_fr
         join taxonomie.taxref
              on taxref_liste_rouge_fr.cd_nom = taxref.cd_nom,
     (select id_source from taxonomie.bib_redlist_source where area_code like 'EUROPE') as source
where length(categorie_lr_europe) > 0;


/* Taxons problématiques (pb de correspondance TaxRef) */
select count(*)
from taxonomie.taxref_liste_rouge_fr;

select taxref_liste_rouge_fr.*
from taxonomie.taxref_liste_rouge_fr
where taxref_liste_rouge_fr.cd_nom not in (select cd_nom from taxonomie.taxref);

/*
cd_nom 2967 cité Tetrao urogallus urogallus est en fait Tetrao urogallus crassirostris (cd_nom 886111)
cd_nom 199314 cité Pterodroma madeira est une sous-espèce de Pterodroma mollis (espèce des iles de Madère)

 */

INSERT INTO ref_geo.bib_areas_types (type_name, type_code, type_desc)
values ('Régions', 'REG', 'Type région'),
       ('Pays', 'PAY', 'Type pays');

insert into ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date,
                            meta_update_date)
select t.id_type,
       'France',
       'FR',
       st_makevalid(st_union(geom)),
       st_centroid(st_makevalid(st_union(geom))),
       'SQL - Union des communes',
       null,
       now(),
       now()
from ref_geo.l_areas,
     (select t1.id_type from ref_geo.bib_areas_types t1 where type_code like 'PAY') as t
where l_areas.id_type = (select t2.id_type from ref_geo.bib_areas_types as t2 where t2.type_code like 'COM')
group by t.id_type;

select t.id_type,
       'Auvergne-Rhône-Alpes',
       'R84',
       st_makevalid(st_union(geom)),
       st_centroid(st_makevalid(st_union(geom))),
       'SQL - Union des communes',
       null,
       now(),
       now()
from ref_geo.l_areas,
     (select t1.id_type from ref_geo.bib_areas_types t1 where type_code like 'REG') as t
where l_areas.id_type = (select t2.id_type from ref_geo.bib_areas_types as t2 where t2.type_code like 'COM')
  and left(l_areas.area_code, 2) in ('03', '15', '43', '63', '01', '07', '26', '38', '42', '69', '73', '74')
group by t.id_type;

select t.id_type,
       'Auvergne',
       'R83',
       st_makevalid(st_union(geom)),
       st_centroid(st_makevalid(st_union(geom))),
       'SQL - Union des communes',
       null,
       now(),
       now()
from ref_geo.l_areas,
     (select t1.id_type from ref_geo.bib_areas_types t1 where type_code like 'REG') as t
where l_areas.id_type = (select t2.id_type from ref_geo.bib_areas_types as t2 where t2.type_code like 'COM')
  and left(l_areas.area_code, 2) in ('03', '15', '43', '63')
group by t.id_type;

select t.id_type,
       'Rhône-Alpes',
       'R82',
       st_makevalid(st_union(geom)),
       st_centroid(st_makevalid(st_union(geom))),
       'SQL - Union des communes',
       null,
       now(),
       now()
from ref_geo.l_areas,
     (select t1.id_type from ref_geo.bib_areas_types t1 where type_code like 'REG') as t
where l_areas.id_type = (select t2.id_type from ref_geo.bib_areas_types as t2 where t2.type_code like 'COM')
  and left(l_areas.area_code, 2) in ('01', '07', '26', '38', '42', '69', '73', '74')
group by t.id_type;



insert into taxonomie.cor_redlist_source_area(id_area, id_source)

select *
from ref_geo.bib_areas_types;
