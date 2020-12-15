/********************************************************
 *   CREATION DES PRINCIPALES TABLES DE L'APPLIUCATION  *
 ********************************************************/

CREATE SCHEMA gn_biodivterritory;

CREATE TABLE IF NOT EXISTS gn_biodivterritory.bib_dynamic_pages_category (
    id_category   SERIAL NOT NULL,
    category_name VARCHAR,
    category_desc VARCHAR,
    PRIMARY KEY (id_category)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_dynamic_pages (
    id_page           SERIAL NOT NULL,
    id_category       INTEGER,
    title             VARCHAR,
    link_name         VARCHAR,
    navbar_link       BOOLEAN,
    navbar_link_order INTEGER,
    url               VARCHAR,
    short_desc        VARCHAR,
    ts_create         TIMESTAMP WITHOUT TIME ZONE,
    ts_update         TIMESTAMP WITHOUT TIME ZONE,
    creator           VARCHAR,
    is_active         BOOLEAN,
    content           TEXT,
    PRIMARY KEY (id_page),
    FOREIGN KEY (id_category) REFERENCES gn_biodivterritory.bib_dynamic_pages_category(id_category),
    UNIQUE (link_name),
    UNIQUE (url)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.bib_datas_types (
    id_type       SERIAL NOT NULL,
    type_name     VARCHAR,
    type_protocol VARCHAR,
    type_desc     VARCHAR,
    PRIMARY KEY (id_type)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_released_datas (
    id_data_release SERIAL NOT NULL,
    id_type         INTEGER,
    data_name       VARCHAR,
    data_desc       TEXT,
    data_url        VARCHAR,
    PRIMARY KEY (id_data_release),
    FOREIGN KEY (id_type) REFERENCES gn_biodivterritory.bib_datas_types(id_type)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.l_areas_type_selection (
    id_selection SERIAL NOT NULL,
    id_type      INTEGER,
    PRIMARY KEY (id_selection),
    UNIQUE (id_type),
    FOREIGN KEY (id_type) REFERENCES ref_geo.bib_areas_types(id_type)
);

CREATE TABLE IF NOT EXISTS taxonomie.t_redlist (
    id_redlist   SERIAL NOT NULL,
    status_order INTEGER,
    cd_nom       INTEGER,
    cd_ref       INTEGER,
    category     VARCHAR,
    criteria     VARCHAR,
    id_source    INTEGER,
    PRIMARY KEY (id_redlist)
);

CREATE TABLE IF NOT EXISTS taxonomie.bib_redlist_source (
    id_source   SERIAL NOT NULL,
    name_source VARCHAR,
    desc_source VARCHAR,
    url_source  VARCHAR,
    context     VARCHAR,
    area_name   VARCHAR,
    area_code   VARCHAR,
    area_type   VARCHAR,
    priority    INTEGER,
    PRIMARY KEY (id_source)
);

CREATE TABLE IF NOT EXISTS taxonomie.bib_redlist_categories (
    code_category  VARCHAR NOT NULL,
    threatened     BOOLEAN,
    sup_category   VARCHAR,
    priority_order INTEGER,
    name_fr        VARCHAR,
    desc_fr        VARCHAR,
    PRIMARY KEY (code_category)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_max_threatened_status (
    cd_nom          SERIAL  NOT NULL,
    threatened      BOOLEAN NOT NULL,
    redlist_statut  VARCHAR,
    redlist_context VARCHAR,
    id_source       INTEGER,
    PRIMARY KEY (cd_nom),
    FOREIGN KEY (id_source) REFERENCES taxonomie.bib_redlist_source(id_source)
);

/* Création des zonages régionaux et nationaux pour associer aux listes rouges */
INSERT INTO
    ref_geo.bib_areas_types (type_name, type_code, type_desc)
VALUES
    ('Régions', 'REG', 'Type région')
  , ('Pays', 'PAY', 'Type pays')
ON CONFLICT DO NOTHING
;


/***************************************************
 *   CREATION D'UNE TABLE DE RECHERCHE DES ZONAGES  *
 *  La variable _areas est issue de la commande psql
 *  psql -v _areas=$AREAS monscript.sql

  ***************************************************/

INSERT INTO
    gn_biodivterritory.l_areas_type_selection (id_type)
SELECT
    id_type
FROM
    ref_geo.bib_areas_types
WHERE
    type_code IN (SELECT unnest(string_to_array(:'_areas', ' ')))
ON CONFLICT DO NOTHING
;


DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_l_areas_autocomplete
;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_l_areas_autocomplete AS
(
SELECT DISTINCT
    l_areas.id_area                    AS id
  , bib_areas_types.type_name          AS type_name
  , lower(unaccent(l_areas.area_name)) AS search_area_name
  , bib_areas_types.type_desc          AS type_desc
  , bib_areas_types.type_code          AS type_code
  , l_areas.area_name                  AS area_name
  , l_areas.area_code                  AS area_code
FROM
    ref_geo.bib_areas_types
        LEFT OUTER JOIN ref_geo.l_areas ON l_areas.id_type = ref_geo.bib_areas_types.id_type
        NATURAL JOIN gn_synthese.cor_area_synthese
        JOIN gn_biodivterritory.l_areas_type_selection ON l_areas.id_type = l_areas_type_selection.id_type
WHERE
    cor_area_synthese.id_area IS NOT NULL
    )
;


CREATE UNIQUE INDEX index_unique_search_area_id_area ON gn_biodivterritory.mv_l_areas_autocomplete(id)
;

CREATE INDEX index_search_area_code ON gn_biodivterritory.mv_l_areas_autocomplete(area_code)
;

CREATE INDEX index_search_area_name_trgm ON gn_biodivterritory.mv_l_areas_autocomplete USING gist(search_area_name gist_trgm_ops)
;

/*******************************
 *   GLOBAL GENERAL STATS      *
 *******************************/

DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_general_stats
;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_general_stats AS
WITH
    count_occtax AS (SELECT count(*) AS count FROM (SELECT DISTINCT id_synthese FROM gn_synthese.synthese) AS t)
  , count_observer AS (SELECT count(*) AS count FROM (SELECT DISTINCT observers FROM gn_synthese.synthese) AS t)
  , count_taxa AS (SELECT
                       count(*) AS count
                   FROM
                       (SELECT DISTINCT
                            cd_ref
                        FROM
                            gn_synthese.synthese
                                JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom) AS t)
  , count_dataset AS (SELECT count(*) AS count FROM (SELECT DISTINCT id_dataset FROM gn_synthese.synthese) AS t)
SELECT
    row_number() OVER () AS id
  , count_occtax.count   AS count_occtax
  , count_observer.count AS count_observer
  , count_taxa.count     AS count_taxa
  , count_dataset.count  AS count_dataset
FROM
    count_occtax
  , count_observer
  , count_dataset
  , count_taxa
;

/*******************************
 *   TERRITORY GENERAL STATS   *
 *******************************/

-- UPDATE gn_synthese.synthese
-- SET
--     the_geom_local = the_geom_local;
--
-- INSERT INTO
--     gn_synthese.cor_area_synthese (id_synthese, id_area)
-- SELECT
--     s.id_synthese AS id_synthese
--   , a.id_area     AS id_area
-- FROM
--     ref_geo.l_areas a
--         JOIN gn_synthese.synthese s ON public.ST_INTERSECTS(s.the_geom_local, a.geom)
-- WHERE
--         a.id_type = (SELECT id_type FROM ref_geo.bib_areas_types WHERE type_code LIKE 'M0.5');

SET enable_hashjoin = OFF
;

RESET enable_mergejoin
;

RESET enable_nestloop
;


DROP
    MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE
;

-- CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
-- (
--     )
;

EXPLAIN (COSTS, VERBOSE, FORMAT JSON)

DROP
    MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE
;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS

WITH
    observers AS (
        SELECT DISTINCT
            cor_area_synthese.id_area
          , unaccent(trim(regexp_split_to_table(synthese.observers, ','))) AS observer
        FROM
            gn_synthese.synthese
                JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
    )
SELECT
    l_areas.id_area
  , bib_areas_types.type_code
  , l_areas.area_code
  , l_areas.area_name
  , count(DISTINCT synthese.cd_nom)                                                             AS count_taxa
  , count(DISTINCT synthese.id_synthese)                                                        AS count_occtax
  , count(DISTINCT synthese.cd_nom)
    FILTER (WHERE bib_redlist_categories.threatened AND bib_redlist_source.area_code LIKE 'FR') AS count_threatened
  , count(DISTINCT synthese.id_dataset)                                                         AS count_dataset
  , count(DISTINCT synthese.date_min)                                                           AS count_date
  , count(DISTINCT synthese.observers)                                                          AS count_observer
  , max(date_min)                                                                               AS last_obs
  , l_areas.geom                                                                                AS geom_local
  , st_transform(l_areas.geom, 4326)                                                            AS geom_4326
FROM
    ref_geo.l_areas
        JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
        JOIN gn_synthese.cor_area_synthese ON l_areas.id_area = cor_area_synthese.id_area
        JOIN gn_synthese.synthese ON cor_area_synthese.id_synthese = synthese.id_synthese
        JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom
        --             JOIN ref_nomenclatures.t_nomenclatures nom_df
--                  on synthese.id_nomenclature_diffusion_level = nom_df.id_nomenclature
        JOIN taxonomie.bib_taxref_rangs ON taxref.id_rang LIKE bib_taxref_rangs.id_rang
        LEFT JOIN taxonomie.t_redlist ON taxref.cd_nom = t_redlist.cd_nom
        JOIN taxonomie.bib_redlist_categories ON t_redlist.category = bib_redlist_categories.code_category
        JOIN taxonomie.bib_redlist_source ON t_redlist.id_source = bib_redlist_source.id_source
        JOIN observers ON observers.id_area = l_areas.id_area
WHERE
    bib_taxref_rangs.id_rang LIKE 'ES'
--       AND nom_df.cd_nomenclature like '5'
GROUP BY
    l_areas.id_area
  , bib_areas_types.type_code
  , l_areas.area_code
  , l_areas.area_name
  , l_areas.geom
;

DROP
    MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_territory_general_stats CASCADE
;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
WITH
    observers AS (
        SELECT DISTINCT
            cor_area_synthese.id_area
          , unaccent(trim(regexp_split_to_table(synthese.observers, ','))) AS observer
        FROM
            gn_synthese.synthese
                JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
    )

SELECT
    l_areas.id_area
  , bib_areas_types.type_code
  , l_areas.area_code
  , l_areas.area_name
  , count(DISTINCT synthese.id_synthese)                                                        AS count_data
  , count(DISTINCT synthese.cd_nom)                                                             AS count_taxa
  , count(DISTINCT synthese.cd_nom)
    FILTER (WHERE bib_redlist_categories.threatened AND bib_redlist_source.area_code LIKE 'FR') AS count_threatened
  , count(DISTINCT synthese.id_synthese)                                                        AS count_occtax
  , count(DISTINCT synthese.id_dataset)                                                         AS count_dataset
  , count(DISTINCT synthese.date_min)                                                           AS count_date
  , count(DISTINCT observers.observer)                                                          AS count_observer
  , max(date_min)                                                                               AS last_obs
  , l_areas.geom                                                                                AS geom_local
  , st_transform(l_areas.geom, 4326)                                                            AS geom_4326
FROM
    gn_synthese.synthese
        JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
        JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
        JOIN gn_biodivterritory.l_areas_type_selection ON l_areas_type_selection.id_type = l_areas.id_type
        JOIN ref_geo.bib_areas_types ON l_areas_type_selection.id_type = bib_areas_types.id_type
        JOIN observers ON observers.id_area = l_areas.id_area
        JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom
        LEFT JOIN taxonomie.t_redlist ON taxref.cd_nom = t_redlist.cd_nom
        JOIN taxonomie.bib_redlist_categories ON t_redlist.category = bib_redlist_categories.code_category
        JOIN taxonomie.bib_redlist_source ON t_redlist.id_source = bib_redlist_source.id_source
WHERE
    taxref.id_rang LIKE 'ES' AND
    synthese.id_nomenclature_diffusion_level = ref_nomenclatures.get_id_nomenclature('NIV_PRECIS', '5')
GROUP BY
    l_areas.id_area
  , l_areas.area_code
  , l_areas.area_name
  , bib_areas_types.type_code
  , l_areas.geom
;


SELECT *
FROM
    gn_biodivterritory.mv_territory_general_stat
;

CREATE UNIQUE INDEX ON gn_biodivterritory.mv_territory_general_stats(id_area)
;

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(type_code)
;

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_name)
;

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_code)
;

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist(geom_local)
;

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist(geom_4326)
;

SELECT populate_geometry_columns()
;

-- SELECT type_code, count(*)
-- FROM
--     gn_synthese.cor_area_synthese
--         JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
--         JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
-- GROUP BY
--     type_code;


DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_area_ntile_limit CASCADE
;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_area_ntile_limit AS
(
WITH
    occtax AS (
        SELECT
            id_area
          , type_code
          , count_occtax                          AS count
          , ntile(5) OVER (ORDER BY count_occtax) AS ntile
        FROM
            gn_biodivterritory.mv_territory_general_stats)
  , taxa AS (
    SELECT
        id_area
      , type_code
      , count_taxa                          AS count
      , ntile(5) OVER (ORDER BY count_taxa) AS ntile
    FROM
        gn_biodivterritory.mv_territory_general_stats)
  , threatened AS (
    SELECT
        id_area
      , type_code
      , count_taxa                                AS count
      , ntile(5) OVER (ORDER BY count_threatened) AS ntile
    FROM
        gn_biodivterritory.mv_territory_general_stats)
  , observer AS (
    SELECT
        id_area
      , type_code
      , count_observer                          AS count
      , ntile(5) OVER (ORDER BY count_observer) AS ntile
    FROM
        gn_biodivterritory.mv_territory_general_stats)
  , date AS (
    SELECT
        id_area
      , type_code
      , count_date                          AS count
      , ntile(5) OVER (ORDER BY count_date) AS ntile
    FROM
        gn_biodivterritory.mv_territory_general_stats)
  , u AS (
    SELECT
        'occtax'   AS type
      , min(count) AS min
      , max(count) AS max
      , ntile
    FROM
        occtax
    GROUP BY ntile
    UNION
    SELECT
        'taxa'
      , min(count)
      , max(count)
      , ntile
    FROM
        taxa
    GROUP BY ntile
    UNION
    SELECT
        'threatened'
      , min(count)
      , max(count)
      , ntile
    FROM
        taxa
    GROUP BY ntile
    UNION
    SELECT
        'observer'
      , min(count)
      , max(count)
      , ntile
    FROM
        observer
    GROUP BY ntile
    UNION
    SELECT
        'date'
      , min(count)
      , max(count)
      , ntile
    FROM
        date
    GROUP BY ntile
)
SELECT
    row_number() OVER () AS id
  , *
FROM
    u
ORDER BY
    type
  , ntile)
;


/*******************************
 *   Territory species list    *
 *******************************/


/* Création de la table de statuts BDC Statuts */

DROP TABLE IF EXISTS taxonomie.bib_bdc_type_statut
;

CREATE TABLE taxonomie.bib_bdc_type_statut (
    id_type_statut    VARCHAR(50) PRIMARY KEY NOT NULL,
    cd_type_statut    VARCHAR(50),
    lb_type_statut    VARCHAR(254),
    regroupement_type VARCHAR(254),
    thematique        VARCHAR(50),
    type_value        VARCHAR(20)
)
;


CREATE TABLE IF NOT EXISTS taxonomie.taxref_bdc_statuts (
    id_taxref_bdc     SERIAL PRIMARY KEY,
    cd_nom            INTEGER REFERENCES taxonomie.taxref(cd_nom),
    cd_ref            INTEGER REFERENCES taxonomie.taxref(cd_nom),
    cd_sup            INTEGER REFERENCES taxonomie.taxref(cd_nom),
    cd_type_statut    VARCHAR(50) REFERENCES taxonomie.bib_bdc_type_statut(id_type_statut),
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
    id_area           INTEGER REFERENCES ref_geo.l_areas(id_area)
)
;


/* Déjà présent dans taxonomie.bib_taxref_categories_fr */
DROP TABLE IF EXISTS taxonomie.bib_redlist_categories
;

CREATE TABLE taxonomie.bib_redlist_categories (
    code_category  VARCHAR(2) PRIMARY KEY,
    sup_category   VARCHAR(30),
    threatened     BOOLEAN DEFAULT FALSE,
    priority_order INT,
    name_fr        VARCHAR(100),
    desc_fr        VARCHAR(254),
    name_en        VARCHAR(100),
    desc_en        VARCHAR(254)
)
;

INSERT INTO
    taxonomie.bib_redlist_categories(code_category, threatened, sup_category, priority_order)
SELECT DISTINCT
    id_categorie_france  AS code_category
  , CASE
        WHEN id_categorie_france IN ('CR', 'EN', 'VU')
            THEN TRUE
        ELSE FALSE END   AS threatened
  , CASE
        WHEN id_categorie_france IN ('CR', 'EN', 'VU')
            THEN 'threatened'
        WHEN id_categorie_france IN ('RE', 'EW', 'EX')
            THEN 'extinct'
        ELSE 'other' END AS sup_category
  , CASE id_categorie_france
        WHEN 'EX'
            THEN 10
        WHEN 'EW'
            THEN 20
        WHEN 'RE'
            THEN 30
        WHEN 'CR'
            THEN 40
        WHEN 'EN'
            THEN 50
        WHEN 'VU'
            THEN 60
        WHEN 'NT'
            THEN 70
        WHEN 'LC'
            THEN 80
        WHEN 'DD'
            THEN 90
        WHEN 'NE'
            THEN 100
        WHEN 'NA'
            THEN 110 END AS priority_order
FROM
    taxonomie.taxref_liste_rouge_fr
;


CREATE TABLE taxonomie.bib_redlist_source (
    id_source   SERIAL PRIMARY KEY,
    name_source VARCHAR(254),
    desc_source TEXT,
    url_source  VARCHAR(254),
    context     VARCHAR(50),
    area_name   VARCHAR(50),
    area_code   VARCHAR(50),
    area_type   VARCHAR(50),
    priority    INTEGER
)
;

/* Optional matching with */
CREATE TABLE taxonomie.cor_redlist_source_area (
    id_cor_redlist_source_area SERIAL PRIMARY KEY,
    id_area                    INTEGER REFERENCES ref_geo.l_areas(id_area),
    id_source                  INTEGER REFERENCES taxonomie.bib_redlist_source(id_source)
)
;

DROP TABLE IF EXISTS taxonomie.t_redlist
;

CREATE TABLE taxonomie.t_redlist (
    id_redlist   SERIAL  NOT NULL PRIMARY KEY,
    status_order INTEGER,
    cd_nom       INTEGER REFERENCES taxonomie.taxref(cd_nom),
    cd_ref       INTEGER REFERENCES taxonomie.taxref(cd_nom),
    category     CHAR(2) NOT NULL REFERENCES taxonomie.bib_taxref_categories_lr(id_categorie_france),
    criteria     VARCHAR(50),
    id_source    INTEGER REFERENCES taxonomie.bib_redlist_source(id_source)
)
;


/* Insertion de la source UICN France*/
INSERT INTO
    taxonomie.bib_redlist_source (name_source, area_code)
SELECT DISTINCT
    liste_rouge_source
  , 'FR'
FROM
    taxonomie.taxref_liste_rouge_fr
;

INSERT INTO
    taxonomie.bib_redlist_source(name_source, area_code, area_name)
VALUES
    ('Liste rouge mondiale des espèces menacées (2019.1)', 'WORLD', 'Monde')
  , ('Liste rouge européenne des espèces menacées (2019.1)', 'EUROPE', 'Europe')
;

INSERT INTO
    taxonomie.t_redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut
  , taxref.cd_nom
  , taxref.cd_ref
  , id_categorie_france
  , criteres_france
  , id_source
FROM
    taxonomie.taxref_liste_rouge_fr
        JOIN taxonomie.bib_redlist_source ON liste_rouge_source = bib_redlist_source.name_source
        JOIN taxonomie.taxref ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom
;


INSERT INTO
    taxonomie.t_redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut
  , taxref.cd_nom
  , taxref.cd_ref
  , CASE
        WHEN categorie_lr_mondiale LIKE 'LR/%'
            THEN upper(right(categorie_lr_mondiale, 2))
        ELSE categorie_lr_mondiale END AS categorie_lr_mondiale
  , NULL
  , id_source
FROM
    taxonomie.taxref_liste_rouge_fr
        JOIN taxonomie.taxref
             ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom
  , (SELECT id_source FROM taxonomie.bib_redlist_source WHERE area_code LIKE 'WORLD') AS source
WHERE
    length(categorie_lr_mondiale) > 0
;


INSERT INTO
    taxonomie.t_redlist(status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut
  , taxref.cd_nom
  , taxref.cd_ref
  , CASE
        WHEN categorie_lr_europe LIKE 'LR/%'
            THEN upper(right(categorie_lr_europe, 2))
        ELSE categorie_lr_europe END AS categorie_lr_mondiale
  , NULL
  , id_source
FROM
    taxonomie.taxref_liste_rouge_fr
        JOIN taxonomie.taxref
             ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom
  , (SELECT id_source FROM taxonomie.bib_redlist_source WHERE area_code LIKE 'EUROPE') AS source
WHERE
    length(categorie_lr_europe) > 0
;


DO
$$
    DECLARE
        arrow RECORD;
    BEGIN
        FOR arrow IN (SELECT DISTINCT cd_ref FROM taxonomie.t_redlist)
            LOOP
                INSERT INTO
                    gn_biodivterritory.t_max_threatened_status(cd_nom, threatened, redlist_statut, redlist_context, id_source)
                SELECT
                    cd_nom
                  , threatened
                  , t_redlist.category
                  , bib_redlist_source.context
                  , bib_redlist_source.id_source
                FROM
                    taxonomie.bib_redlist_categories
                  , taxonomie.bib_redlist_source
                  , taxonomie.t_redlist
                WHERE
                    taxonomie.t_redlist.cd_ref = arrow.cd_ref AND
                    taxonomie.bib_redlist_source.id_source = taxonomie.t_redlist.id_source AND
                    taxonomie.bib_redlist_categories.code_category = taxonomie.t_redlist.category
                ORDER BY taxonomie.bib_redlist_source.priority, taxonomie.bib_redlist_categories.priority_order
                LIMIT 1;

            END LOOP;
    END;
$$