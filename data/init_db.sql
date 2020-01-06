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

INSERT INTO
    ref_geo.bib_areas_types(type_name, type_code, type_desc)
VALUES
('Mailles0.5*0.5', 'M0.5', 'Mailles (non officielles de 500m basées sur le référentiel RGF93 - 2154)')

INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
WITH
    area AS (SELECT st_simplify(st_union(geom), 100) AS geom
             FROM
                 ref_geo.l_areas
--              WHERE LEFT(area_code, 2) IN ('01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'))
             WHERE LEFT(area_code, 2) IN ('07'))
SELECT
    bib_areas_types.id_type
  , 'Maille 500m l' || grow || 'c' || gcol AS NAME
  , 'l' || grow || 'c' || gcol             AS code
  , st_multi(sg.geom)                      AS geom
  , st_centroid(sg.geom)                   AS centroid
  , 'auto-généré'                          AS source
  , 'auto-genéré'                          AS comment
  , now()                                  AS tscreate
  , now()                                  AS tsupdate
FROM
    ref_geo.ST_SquareGrid(
                (SELECT geom FROM area)
        , 500
        , 500
        , FALSE) AS sg
  , ref_geo.bib_areas_types
  , area
WHERE
    type_code LIKE 'M0.5' AND
    st_intersects(st_buffer(area.geom, 1000), sg.geom)
;

DROP TABLE IF EXISTS public.test;
CREATE TABLE public.test AS
WITH
    area AS (SELECT st_simplify(st_union(geom), 100) AS geom
             FROM
                 ref_geo.l_areas
--              WHERE LEFT(area_code, 2) IN ('01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'))
             WHERE LEFT(area_code, 2) IN ('07'))
SELECT
    row_number() OVER ()                   AS id
  , bib_areas_types.id_type
  , 'Maille 500m l' || grow || 'c' || gcol AS name
  , 'l' || grow || 'c' || gcol             AS code
  , sg.geom                                AS geom
  , st_centroid(sg.geom)                   AS centroid
  , 'auto-généré'                          AS source
  , 'auto-genéré'                          AS comment
  , now()                                  AS tscreate
  , now()                                  AS tsupdate
FROM
    ref_geo.ST_SquareGrid(
                (SELECT geom FROM area)
        , 500
        , 500
        , FALSE) AS sg
  , ref_geo.bib_areas_types
  , area
WHERE
    type_code LIKE 'M0.5' AND
    st_intersects(st_buffer(area.geom, 1000), sg.geom)
;

ALTER TABLE public.test
    ADD PRIMARY KEY (id);
CREATE INDEX ON public.test USING gist(geom);
CREATE INDEX ON public.test USING gist(centroid);

SELECT populate_geometry_columns();



/*******************************
 *   TERRITORY GENERAL STATS   *
 *******************************/

-- UPDATE gn_synthese.synthese
-- SET
--     the_geom_local = the_geom_local;

INSERT INTO
    gn_synthese.cor_area_synthese (id_synthese, id_area)
SELECT
    s.id_synthese AS id_synthese
  , a.id_area     AS id_area
FROM
    ref_geo.l_areas a
        JOIN gn_synthese.synthese s ON public.ST_INTERSECTS(s.the_geom_local, a.geom)
WHERE
        a.id_type = (SELECT id_type FROM ref_geo.bib_areas_types WHERE type_code LIKE 'M0.5');

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
SELECT
    l_areas.id_area
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
FROM
    ref_geo.l_areas
        JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
        JOIN gn_synthese.cor_area_synthese ON l_areas.id_area = cor_area_synthese.id_area
        JOIN gn_synthese.synthese ON cor_area_synthese.id_synthese = synthese.id_synthese
--         JOIN observers ON observers.id_area = l_areas.id_area
GROUP BY
    l_areas.id_area
  , bib_areas_types.type_code
  , l_areas.area_code
  , l_areas.area_name
  , l_areas.geom;


CREATE UNIQUE INDEX ON gn_biodivterritory.mv_territory_general_stats(id_area);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(type_code);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_name);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_code);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist(geom_local);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist(geom_4326);

SELECT populate_geometry_columns();

SELECT type_code, count(*)
FROM
    gn_synthese.cor_area_synthese
        JOIN ref_geo.l_areas ON cor_area_synthese.id_area = l_areas.id_area
        JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
GROUP BY
    type_code;


DROP MATERIALIZED VIEW IF EXISTS gn_biodivterritory.mv_area_ntile_limit CASCADE;
CREATE MATERIALIZED VIEW gn_biodivterritory.mv_area_ntile_limit AS
(
WITH
    occtax AS (
        SELECT
            id_area
          , type_code
          , count_occtax
          , NTILE(5) OVER (ORDER BY count_occtax) AS ntile
        FROM
            gn_biodivterritory.mv_territory_general_stats)
  , taxa AS (
    SELECT
        id_area
      , type_code
      , count_taxa
      , NTILE(5) OVER (ORDER BY count_taxa) AS ntile
    FROM
        gn_biodivterritory.mv_territory_general_stats)
  , u AS (
    SELECT 'occtax' AS type, MIN(count_occtax) AS min, max(count_occtax) AS max, ntile
    FROM occtax
    GROUP BY
        ntile
    UNION
    SELECT 'taxa', MIN(count_taxa), max(count_taxa), ntile
    FROM taxa
    GROUP BY
        ntile
)
SELECT row_number() OVER () as id, *
FROM u
ORDER BY
    type
  , ntile);