/*********************************CR***********************
 *   CREATION DES PRINCIPALES TABLES DE L'APPLIUCATION  *
 ********************************************************/
/* Create dedicated db schema named gn_biodivterritory */
CREATE SCHEMA gn_biodivterritory;


/* INFO: Editable content: table for categories */
CREATE TABLE IF NOT EXISTS gn_biodivterritory.bib_dynamic_pages_category (
    id_category serial NOT NULL,
    category_name varchar,
    category_desc varchar,
    PRIMARY KEY (id_category)
);


/* INFO: Editable content: table for pages */
CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_dynamic_pages (
    id_page serial NOT NULL,
    id_category integer,
    title varchar,
    link_name varchar,
    navbar_link boolean,
    navbar_link_order integer,
    url varchar,
    short_desc varchar,
    ts_create timestamp without time zone,
    ts_update timestamp without time zone,
    creator varchar,
    is_active boolean,
    content text,
    PRIMARY KEY (id_page),
    FOREIGN KEY (id_category) REFERENCES gn_biodivterritory.bib_dynamic_pages_category (id_category),
    UNIQUE (link_name),
    UNIQUE (url)
);


/****************************************************************
 *   LISTING DATA TYPE                                          *
 ****************************************************************/
/* INFO: available data type */
CREATE TABLE IF NOT EXISTS gn_biodivterritory.bib_datas_types (
    id_type serial NOT NULL,
    type_name varchar,
    type_protocol varchar,
    type_desc varchar,
    PRIMARY KEY (id_type)
);


/* */
CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_released_datas (
    id_data_release serial NOT NULL,
    id_type integer,
    data_name varchar,
    data_desc text,
    data_url varchar,
    PRIMARY KEY (id_data_release),
    FOREIGN KEY (id_type) REFERENCES gn_biodivterritory.bib_datas_types (id_type)
);

CREATE TABLE IF NOT EXISTS gn_biodivterritory.l_areas_type_selection (
    id_selection serial NOT NULL,
    id_type integer,
    searchable boolean,
    PRIMARY KEY (id_selection),
    UNIQUE (id_type),
    FOREIGN KEY (id_type) REFERENCES ref_geo.bib_areas_types (id_type)
);

COMMENT ON COLUMN gn_biodivterritory.l_areas_type_selection.id_type IS 'reference to area id_type usable for app';

COMMENT ON COLUMN gn_biodivterritory.l_areas_type_selection.searchable IS 'searchable area from API with autocomplete';

CREATE TABLE IF NOT EXISTS taxonomie.bib_c_redlist_source (
    id_source serial NOT NULL,
    name_source varchar,
    version varchar,
    desc_source varchar,
    url_source varchar,
    context varchar,
    area_name varchar,
    area_code varchar,
    area_type varchar,
    priority integer,
    PRIMARY KEY (id_source)
);

COMMENT ON TABLE taxonomie.t_c_redlist IS 'Liste des sources de statuts de liste rouge';

CREATE TABLE IF NOT EXISTS taxonomie.t_c_redlist (
    id_redlist serial NOT NULL,
    status_order integer,
    cd_nom integer,
    cd_ref integer,
    category varchar,
    criteria varchar,
    id_source integer REFERENCES taxonomie.bib_c_redlist_source (id_source),
    PRIMARY KEY (id_redlist)
);

COMMENT ON TABLE taxonomie.t_c_redlist IS 'Liste des statuts de liste rouge par taxons';

CREATE TABLE IF NOT EXISTS taxonomie.bib_c_redlist_categories (
    code_category varchar NOT NULL,
    threatened boolean,
    sup_category varchar,
    priority_order integer,
    name_fr varchar,
    desc_fr varchar,
    PRIMARY KEY (code_category)
);

COMMENT ON TABLE taxonomie.bib_c_redlist_categories IS 'Liste des catégories de statuts de liste rouge';

CREATE TABLE IF NOT EXISTS gn_biodivterritory.t_max_threatened_status (
    cd_nom serial NOT NULL,
    threatened boolean NOT NULL,
    redlist_statut varchar,
    redlist_context varchar,
    id_source integer,
    PRIMARY KEY (cd_nom),
    FOREIGN KEY (id_source) REFERENCES taxonomie.bib_c_redlist_source (id_source)
);


/* Création des zonages régionaux et nationaux pour associer aux listes rouges */
INSERT INTO ref_geo.bib_areas_types (type_name, type_code, type_desc)
    VALUES ('Régions', 'REG', 'Type région'), ('Pays', 'PAY', 'Type pays')
ON CONFLICT
    DO NOTHING;


/***************************************************
 *   CREATION D'UNE TABLE DE RECHERCHE DES ZONAGES  *
 *  La variable _areas est issue de la commande psql
 *  psql -v _areas=$AREAS monscript.sql
 ***************************************************/
INSERT INTO gn_biodivterritory.l_areas_type_selection (id_type)
SELECT
    id_type
FROM
    ref_geo.bib_areas_types
WHERE
    type_code IN (
        SELECT
            unnest(string_to_array(:'_areas', ' ')))
ON CONFLICT
    DO NOTHING;

DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_l_areas_autocomplete;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_l_areas_autocomplete AS (
    SELECT DISTINCT
        l_areas.id_area AS id,
        bib_areas_types.type_name AS type_name,
        lower(unaccent (l_areas.area_name)) AS search_area_name,
        bib_areas_types.type_desc AS type_desc,
        bib_areas_types.type_code AS type_code,
        l_areas.area_name AS area_name,
        l_areas.area_code AS area_code
    FROM
        ref_geo.bib_areas_types
    LEFT OUTER JOIN ref_geo.l_areas ON l_areas.id_type = ref_geo.bib_areas_types.id_type
    NATURAL JOIN gn_synthese.cor_area_synthese
    JOIN gn_biodivterritory.l_areas_type_selection ON l_areas.id_type = l_areas_type_selection.id_type
WHERE
    cor_area_synthese.id_area IS NOT NULL
    AND l_areas_type_selection.searchable);

CREATE UNIQUE INDEX index_unique_search_area_id_area ON gn_biodivterritory.mv_l_areas_autocomplete (id);

CREATE INDEX index_search_area_code ON gn_biodivterritory.mv_l_areas_autocomplete (area_code);

CREATE INDEX index_search_area_name_trgm ON gn_biodivterritory.mv_l_areas_autocomplete USING gist (search_area_name gist_trgm_ops);


/*******************************
 *   GLOBAL GENERAL STATS      *
 *******************************/
DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_general_stats;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_general_stats AS
WITH count_occtax AS (
    SELECT
        count(*) AS count
    FROM ( SELECT DISTINCT
            id_synthese
        FROM
            gn_synthese.synthese) AS t
),
count_observer AS (
    SELECT
        count(*) AS count
    FROM ( SELECT DISTINCT
            observers
        FROM
            gn_synthese.synthese) AS t
),
count_taxa AS (
    SELECT
        count(*) AS count
    FROM ( SELECT DISTINCT
            cd_ref
        FROM
            gn_synthese.synthese
            JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom
                AND taxref.id_rang = 'ES') AS t
),
count_dataset AS (
    SELECT
        count(*) AS count
    FROM ( SELECT DISTINCT
            id_dataset
        FROM
            gn_synthese.synthese) AS t
)
SELECT
    row_number() OVER () AS id,
        count_occtax.count AS count_occtax,
        count_observer.count AS count_observer,
        count_taxa.count AS count_taxa,
        count_dataset.count AS count_dataset
    FROM
        count_occtax,
        count_observer,
        count_dataset,
        count_taxa;


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
SET enable_hashjoin = OFF;

RESET enable_mergejoin;

RESET enable_nestloop;

DROP MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE;

-- CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
-- (
--     )
-- ;
-- EXPLAIN (
--     COSTS,
--     VERBOSE,
--     FORMAT JSON
-- ) DROP MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE;
-- CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
-- WITH observers AS (
--     SELECT DISTINCT
--         cor_area_synthese.id_area,
--         unaccent (trim(regexp_split_to_table(synthese.observers, ','))) AS observer
--     FROM
--         gn_synthese.synthese
--         JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
-- )
-- SELECT
--     l_areas.id_area,
--     bib_areas_types.type_code,
--     l_areas.area_code,
--     l_areas.area_name,
--     count(DISTINCT synthese.cd_nom) FILTER (WHERE taxref.id_rang LIKE 'es') AS count_taxa,
--     count(DISTINCT synthese.id_synthese) AS count_occtax,
--     count(DISTINCT synthese.cd_nom) FILTER (WHERE bib_c_redlist_categories.threatened
--         AND bib_c_redlist_source.area_code LIKE 'FR'
--         AND taxref.id_rang LIKE 'es') AS count_threatened,
--     count(DISTINCT synthese.id_dataset) AS count_dataset,
--     count(DISTINCT synthese.date_min) AS count_date,
--     count(DISTINCT synthese.observers) AS count_observer,
--     max(date_min) AS last_obs,
--     l_areas.geom AS geom_local,
--     st_transform (l_areas.geom, 4326) AS geom_4326
-- FROM
--     ref_geo.l_areas
-- JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
-- JOIN gn_synthese.cor_area_synthese ON l_areas.id_area = cor_area_synthese.id_area
-- JOIN gn_synthese.synthese ON cor_area_synthese.id_synthese = synthese.id_synthese
-- JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom
-- --             JOIN ref_nomenclatures.t_nomenclatures nom_df
-- --                  on synthese.id_nomenclature_diffusion_level = nom_df.id_nomenclature
-- JOIN taxonomie.bib_taxref_rangs ON taxref.id_rang LIKE bib_taxref_rangs.id_rang
--     LEFT JOIN taxonomie.t_c_redlist ON taxref.cd_nom = t_c_redlist.cd_nom
--     JOIN taxonomie.bib_c_redlist_categories ON t_c_redlist.category = bib_c_redlist_categories.code_category
--     JOIN taxonomie.bib_c_redlist_source ON t_c_redlist.id_source = bib_c_redlist_source.id_source
--     JOIN observers ON observers.id_area = l_areas.id_area
-- WHERE
--     bib_taxref_rangs.id_rang LIKE 'es'
--     --       AND nom_df.cd_nomenclature like '5'
-- GROUP BY
--     l_areas.id_area,
--     bib_areas_types.type_code,
--     l_areas.area_code,
--     l_areas.area_name,
--     l_areas.geom;
DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_territory_general_stats CASCADE;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
-- WITH
--     explain observers AS (
--         explain
--         SELECT DISTINCT
--             cor_area_synthese.id_area
--           , unaccent(trim(regexp_split_to_table(synthese.observers, ','))) AS observer
--             FROM
--                 gn_synthese.synthese
--                     JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
--     )
-- EXPLAIN
--     (ANALYZE, VERBOSE)
SELECT
    l_areas.id_area,
    bib_areas_types.type_code,
    l_areas.area_code,
    l_areas.area_name,
    count(DISTINCT synthese.id_synthese) AS count_data,
    count(DISTINCT taxref.cd_ref) AS count_taxa,
    count(DISTINCT taxref.cd_ref) FILTER (WHERE gn_biodivterritory.t_max_threatened_status.threatened = TRUE) AS count_threatened,
    count(DISTINCT synthese.id_synthese) AS count_occtax,
    count(DISTINCT synthese.id_dataset) AS count_dataset,
    count(DISTINCT synthese.date_min) AS count_date,
    count(DISTINCT synthese.observers) AS count_observer,
    max(date_min) AS last_obs,
    l_areas.geom AS geom_local,
    st_transform (l_areas.geom, 4326) AS geom_4326
FROM
    gn_synthese.synthese
    JOIN gn_synthese.cor_area_synthese ON synthese.id_synthese = cor_area_synthese.id_synthese
    JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
    JOIN gn_biodivterritory.l_areas_type_selection ON l_areas_type_selection.id_type = l_areas.id_type
    JOIN ref_geo.bib_areas_types ON l_areas_type_selection.id_type = bib_areas_types.id_type
    --             JOIN observers ON observers.id_area = l_areas.id_area
    JOIN taxonomie.taxref ON synthese.cd_nom = taxref.cd_nom
    LEFT OUTER JOIN gn_biodivterritory.t_max_threatened_status ON gn_biodivterritory.t_max_threatened_status.cd_nom = taxonomie.taxref.cd_ref
    --             LEFT JOIN taxonomie.t_c_redlist ON taxref.cd_nom = t_c_redlist.cd_nom
    --             JOIN taxonomie.bib_c_redlist_categories ON t_c_redlist.category = bib_c_redlist_categories.code_category
    --             JOIN taxonomie.bib_c_redlist_source ON t_c_redlist.id_source = bib_c_redlist_source.id_source
WHERE
    taxref.id_rang LIKE 'ES'
    AND taxref.cd_nom = taxref.cd_ref
    AND synthese.id_nomenclature_diffusion_level = ref_nomenclatures.get_id_nomenclature ('NIV_PRECIS', '5')
    AND l_areas.id_type IN (
        SELECT
            id_type
        FROM
            gn_biodivterritory.l_areas_type_selection)
    --       AND synthese.date_min < now()::date
    --       AND cor_area_synthese.id_area = 2191792
    --         and cor_area_synthese.id_area = 5271
GROUP BY
    l_areas.id_area,
    l_areas.area_code,
    l_areas.area_name,
    bib_areas_types.type_code,
    l_areas.geom;

SELECT
    count(*)
FROM
    gn_synthese.cor_area_synthese
WHERE
    id_area = 2191871;

CREATE UNIQUE INDEX ON gn_biodivterritory.mv_territory_general_stats (id_area);

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (type_code);

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (area_name);

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats (area_code);

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist (geom_local);

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist (geom_4326);

SELECT
    populate_geometry_columns ();

-- SELECT type_code, count(*)
-- FROM
--     gn_synthese.cor_area_synthese
--         JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
--         JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
-- GROUP BY
--     type_code;
DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_area_ntile_limit CASCADE;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_area_ntile_limit AS (
    WITH occtax AS (
        SELECT
            id_area,
            type_code,
            count_occtax AS count,
            ntile(5) OVER (ORDER BY count_occtax) AS ntile
        FROM
            gn_biodivterritory.mv_territory_general_stats),
        taxa AS (
            SELECT
                id_area,
                type_code,
                count_taxa AS count,
                ntile(5) OVER (ORDER BY count_taxa) AS ntile
            FROM
                gn_biodivterritory.mv_territory_general_stats),
            threatened AS (
                SELECT
                    id_area,
                    type_code,
                    count_taxa AS count,
                    ntile(5) OVER (ORDER BY count_threatened) AS ntile
                FROM
                    gn_biodivterritory.mv_territory_general_stats),
                observer AS (
                    SELECT
                        id_area,
                        type_code,
                        count_observer AS count,
                        ntile(5) OVER (ORDER BY count_observer) AS ntile
                    FROM
                        gn_biodivterritory.mv_territory_general_stats),
                    date AS (
                        SELECT
                            id_area,
                            type_code,
                            count_date AS count,
                            ntile(5) OVER (ORDER BY count_date) AS ntile
                        FROM
                            gn_biodivterritory.mv_territory_general_stats),
                        u AS (
                            SELECT
                                'occtax' AS type,
                                min(count) AS min,
                                max(count) AS max,
                                ntile
                            FROM
                                occtax
                            GROUP BY
                                ntile
                            UNION
                            SELECT
                                'taxa',
                                min(count),
                                max(count),
                                ntile
                            FROM
                                taxa
                            GROUP BY
                                ntile
                            UNION
                            SELECT
                                'threatened',
                                min(count),
                                max(count),
                                ntile
                            FROM
                                taxa
                            GROUP BY
                                ntile
                            UNION
                            SELECT
                                'observer',
                                min(count),
                                max(count),
                                ntile
                            FROM
                                observer
                            GROUP BY
                                ntile
                            UNION
                            SELECT
                                'date',
                                min(count),
                                max(count),
                                ntile
                            FROM
                                date
                            GROUP BY
                                ntile
)
                            SELECT
                                row_number() OVER () AS id,
                                *
                            FROM
                                u
                            ORDER BY
                                type,
                                ntile);


/*******************************
 *   Territory species list    *
 **************************MVTerritoryGeneralStats*****/
/* Création de la table de statuts BDC Statuts */
DROP TABLE IF EXISTS taxonomie.bib_c_bdc_type_statut;

CREATE TABLE taxonomie.bib_c_bdc_type_statut (
    id_type_statut varchar(50) PRIMARY KEY NOT NULL,
    cd_type_statut varchar(50),
    lb_type_statut varchar(254),
    regroupement_type varchar(254),
    thematique varchar(50),
    type_value varchar(20)
);

CREATE TABLE IF NOT EXISTS taxonomie.taxref_bdc_statuts (
    id_taxref_bdc serial PRIMARY KEY,
    cd_nom integer REFERENCES taxonomie.taxref (cd_nom),
    cd_ref integer REFERENCES taxonomie.taxref (cd_nom),
    cd_sup integer REFERENCES taxonomie.taxref (cd_nom),
    cd_type_statut varchar(50) REFERENCES taxonomie.bib_c_bdc_type_statut (id_type_statut),
    lb_type_statut varchar(254),
    regroupement_type varchar(100),
    code_statut varchar(10),
    label_statut varchar(50),
    rq_statut varchar(1000),
    cd_sig varchar(50),
    cd_doc integer,
    lb_nom varchar(50),
    lb_auteur varchar(254),
    nom_complet_html varchar(254),
    nom_valide_html varchar(254),
    regne varchar(50),
    phylum varchar(50),
    classe varchar(50),
    ordre varchar(50),
    famille varchar(50),
    group1_inpn varchar(50),
    group2_inpn varchar(50),
    lb_adm_tr varchar(50),
    niveau_admin varchar(50),
    cd_iso3166_1 varchar(50),
    cd_iso3166_2 varchar(50),
    full_citation varchar(50),
    doc_url varchar(254),
    thematique varchar(50),
    type_value varchar(50),
    id_area integer REFERENCES ref_geo.l_areas (id_area)
);


/* Déjà présent dans taxonomie.bib_taxref_categories_fr */
DROP TABLE IF EXISTS taxonomie.bib_c_redlist_categories;

CREATE TABLE taxonomie.bib_c_redlist_categories (
    code_category varchar(2) PRIMARY KEY,
    sup_category varchar(30),
    threatened boolean DEFAULT FALSE,
    priority_order int,
    name_fr varchar(100),
    desc_fr varchar(254),
    name_en varchar(100),
    desc_en varchar(254)
);

INSERT INTO taxonomie.bib_c_redlist_categories (code_category, threatened, sup_category, priority_order)
SELECT DISTINCT
    id_categorie_france AS code_category,
    CASE WHEN id_categorie_france IN ('CR', 'EN', 'VU') THEN
        TRUE
    ELSE
        FALSE
    END AS threatened,
    CASE WHEN id_categorie_france IN ('CR', 'EN', 'VU') THEN
        'threatened'
    WHEN id_categorie_france IN ('RE', 'EW', 'EX') THEN
        'extinct'
    ELSE
        'other'
    END AS sup_category,
    CASE id_categorie_france
    WHEN 'EX' THEN
        10
    WHEN 'EW' THEN
        20
    WHEN 'RE' THEN
        30
    WHEN 'CR' THEN
        40
    WHEN 'EN' THEN
        50
    WHEN 'VU' THEN
        60
    WHEN 'NT' THEN
        70
    WHEN 'LC' THEN
        80
    WHEN 'DD' THEN
        90
    WHEN 'NE' THEN
        100
    WHEN 'NA' THEN
        110
    END AS priority_order
FROM
    taxonomie.taxref_liste_rouge_fr;

CREATE TABLE taxonomie.bib_c_redlist_source (
    id_source serial PRIMARY KEY,
    name_source varchar(254),
    desc_source text,
    url_source varchar(254),
    context varchar(50),
    area_name varchar(50),
    area_code varchar(50),
    area_type varchar(50),
    priority integer
);


/* Optional matching with */
CREATE TABLE taxonomie.cor_c_redlist_source_area (
    id_cor_c_redlist_source_area serial PRIMARY KEY,
    id_area integer REFERENCES ref_geo.l_areas (id_area),
    id_source integer REFERENCES taxonomie.bib_c_redlist_source (id_source)
);

DROP TABLE IF EXISTS taxonomie.t_c_redlist;

CREATE TABLE taxonomie.t_c_redlist (
    id_redlist serial NOT NULL PRIMARY KEY,
    status_order integer,
    cd_nom integer REFERENCES taxonomie.taxref (cd_nom),
    cd_ref integer REFERENCES taxonomie.taxref (cd_nom),
    category char(2) NOT NULL REFERENCES taxonomie.bib_taxref_categories_lr (id_categorie_france),
    criteria varchar(50),
    id_source integer REFERENCES taxonomie.bib_c_redlist_source (id_source)
);


/* Insertion de la source UICN France*/
INSERT INTO taxonomie.bib_c_redlist_source (name_source, area_code, area_name)
SELECT DISTINCT
    liste_rouge_source,
    'FR',
    'France métropolitaine'
FROM
    taxonomie.taxref_liste_rouge_fr;

INSERT INTO taxonomie.bib_c_redlist_source (name_source, area_code, area_name)
    VALUES ('Liste rouge mondiale des espèces menacées (2019.1)', 'WORLD', 'Monde'), ('Liste rouge européenne des espèces menacées (2019.1)', 'EUROPE', 'Europe');

INSERT INTO taxonomie.t_c_redlist (status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut,
    taxref.cd_nom,
    taxref.cd_ref,
    id_categorie_france,
    criteres_france,
    id_source
FROM
    taxonomie.taxref_liste_rouge_fr
    JOIN taxonomie.bib_c_redlist_source ON liste_rouge_source = bib_c_redlist_source.name_source
    JOIN taxonomie.taxref ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom;

INSERT INTO taxonomie.t_c_redlist (status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut,
    taxref.cd_nom,
    taxref.cd_ref,
    CASE WHEN categorie_lr_mondiale LIKE 'LR/%' THEN
        upper(
        RIGHT (categorie_lr_mondiale, 2))
    ELSE
        categorie_lr_mondiale
    END AS categorie_lr_mondiale,
    NULL,
    id_source
FROM
    taxonomie.taxref_liste_rouge_fr
    JOIN taxonomie.taxref ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom,
    (
        SELECT
            id_source
        FROM
            taxonomie.bib_c_redlist_source
        WHERE
            area_code LIKE 'WORLD') AS source
WHERE
    length(categorie_lr_mondiale) > 0;

INSERT INTO taxonomie.t_c_redlist (status_order, cd_nom, cd_ref, category, criteria, id_source)
SELECT
    ordre_statut,
    taxref.cd_nom,
    taxref.cd_ref,
    CASE WHEN categorie_lr_europe LIKE 'LR/%' THEN
        upper(
        RIGHT (categorie_lr_europe, 2))
    ELSE
        categorie_lr_europe
    END AS categorie_lr_mondiale,
    NULL,
    id_source
FROM
    taxonomie.taxref_liste_rouge_fr
    JOIN taxonomie.taxref ON taxref_liste_rouge_fr.cd_nom = taxref.cd_nom,
    (
        SELECT
            id_source
        FROM
            taxonomie.bib_c_redlist_source
        WHERE
            area_code LIKE 'EUROPE') AS source
WHERE
    length(categorie_lr_europe) > 0;

DO $$
DECLARE
    arrow RECORD;
BEGIN
    FOR arrow IN ( SELECT DISTINCT
            cd_ref
        FROM
            taxonomie.t_c_redlist)
        LOOP
            INSERT INTO gn_biodivterritory.t_max_threatened_status (cd_nom, threatened, redlist_statut, redlist_context, id_source)
            SELECT
                cd_nom,
                threatened,
                t_c_redlist.category,
                bib_c_redlist_source.context,
                bib_c_redlist_source.id_source
            FROM
                taxonomie.bib_c_redlist_categories,
                taxonomie.bib_c_redlist_source,
                taxonomie.t_c_redlist
            WHERE
                taxonomie.t_c_redlist.cd_ref = arrow.cd_ref
                AND taxonomie.bib_c_redlist_source.id_source = taxonomie.t_c_redlist.id_source
                AND taxonomie.bib_c_redlist_categories.code_category = taxonomie.t_c_redlist.category
            ORDER BY
                taxonomie.bib_c_redlist_source.priority,
                taxonomie.bib_c_redlist_categories.priority_order
            LIMIT 1;
        END LOOP;
END;
$$
