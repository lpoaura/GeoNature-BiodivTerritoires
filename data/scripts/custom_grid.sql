
/***************************************************
 *   OUTILS POUR CREER DES MAILLES PERSONNALISEES  *
 ***************************************************/


/* Create required type */

DROP TYPE IF EXISTS public.T_GRID CASCADE
;

CREATE TYPE public.T_GRID AS
(
    gcol INT4,
    grow INT4,
    geom GEOMETRY
)
;

/* Drop function is exists */
DROP FUNCTION IF EXISTS ref_geo.st_squaregrid(GEOMETRY, NUMERIC, NUMERIC, BOOLEAN)
;

/* Now create the function */
CREATE OR REPLACE FUNCTION ref_geo.st_squaregrid(p_geometry GEOMETRY, p_tilesizex NUMERIC, p_tilesizey NUMERIC
                                                , p_point BOOLEAN DEFAULT TRUE)
    RETURNS SETOF T_GRID AS
$BODY$
DECLARE
    v_mbr   GEOMETRY;
    v_srid  INT4;
    v_halfx NUMERIC := p_tilesizex / 2.0;
    v_halfy NUMERIC := p_tilesizey / 2.0;
    v_locol INT4;
    v_hicol INT4;
    v_lorow INT4;
    v_hirow INT4;
    v_grid  T_GRID;
BEGIN
    IF (p_geometry IS NULL)
    THEN
        RETURN
        ;
    END IF;
    v_srid := st_srid(p_geometry);
    v_mbr := st_envelope(p_geometry);
    v_locol := trunc((st_xmin(v_mbr) / p_tilesizex) :: NUMERIC);
    v_hicol := ceil((st_xmax(v_mbr) / p_tilesizex) :: NUMERIC) - 1;
    v_lorow := trunc((st_ymin(v_mbr) / p_tilesizey) :: NUMERIC);
    v_hirow := ceil((st_ymax(v_mbr) / p_tilesizey) :: NUMERIC) - 1;

    FOR v_col IN v_locol..v_hicol
        LOOP
            FOR v_row IN v_lorow..v_hirow
                LOOP
                    v_grid.gcol := v_col;
                    v_grid.grow := v_row;

                    IF (p_point)
                    THEN
                        v_grid.geom := st_setsrid(
                                st_makepoint((v_col * p_tilesizex) + v_halfx,
                                             (v_row * p_tilesizey) + v_halfy),
                                v_srid);
                    ELSE
                        v_grid.geom := st_setsrid(
                                st_makeenvelope((v_col * p_tilesizex),
                                                (v_row * p_tilesizey),
                                                (v_col * p_tilesizex) + p_tilesizex,
                                                (v_row * p_tilesizey) + p_tilesizey),
                                v_srid);
                    END IF;
                    RETURN NEXT v_grid;
                END LOOP;
        END LOOP;
END;
$BODY$ LANGUAGE plpgsql
    IMMUTABLE
    COST 100
    ROWS 1000
;

/*  Assign ownership */
    ALTER FUNCTION ref_geo.st_squaregrid(GEOMETRY, NUMERIC, NUMERIC, BOOLEAN)
    OWNER TO postgres
;



CREATE INDEX index_l_areas_area_name ON ref_geo.l_areas(area_name)
;

CREATE INDEX index_l_areas_area_code ON ref_geo.l_areas(area_code)
;

CREATE INDEX index_l_areas_id_type ON ref_geo.l_areas(id_type)
;

/***********************************************
 * CREATION D'UN MAILLAGE DE 500m              *
 ***********************************************/


INSERT INTO
    ref_geo.bib_areas_types(type_name, type_code, type_desc)
VALUES
('Mailles0.5*0.5', 'M0.5', 'Mailles (non officielles de 500m basées sur le référentiel RGF93 - 2154)')

INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
WITH
    area AS (SELECT
                 st_simplify(st_union(geom), 100) AS geom
             FROM
                 ref_geo.l_areas
             WHERE
                     left(area_code, 2) IN ('01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'))
--             WHERE LEFT(area_code, 2) IN ('07'))
SELECT
    bib_areas_types.id_type
  , 'Maille 500m l' || grow || 'c' || gcol AS name
  , 'l' || grow || 'c' || gcol             AS code
  , st_multi(sg.geom)                      AS geom
  , st_centroid(sg.geom)                   AS centroid
  , 'auto-généré'                          AS source
  , 'auto-genéré'                          AS comment
  , now()                                  AS tscreate
  , now()                                  AS tsupdate
FROM
    ref_geo.st_squaregrid(
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
