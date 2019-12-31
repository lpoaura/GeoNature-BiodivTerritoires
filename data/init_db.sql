/*******************************
 *   TERRITORY GENERAL STATS   *
 *******************************/
DROP MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE;

CREATE MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats AS
(
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
  , count(DISTINCT synthese.cd_nom)      AS count_taxa
  , count(DISTINCT synthese.id_synthese) AS count_occtax
  , count(DISTINCT synthese.id_dataset)  AS count_dataset
  , count(DISTINCT synthese.date_min)    AS count_date
  , count(DISTINCT observers.observer)   AS count_observer
  , max(date_min)                        AS last_obs
  , l_areas.geom
FROM
    ref_geo.l_areas
        JOIN ref_geo.bib_areas_types ON l_areas.id_type = bib_areas_types.id_type
        JOIN gn_synthese.cor_area_synthese ON l_areas.id_area = cor_area_synthese.id_area
        JOIN gn_synthese.synthese ON cor_area_synthese.id_synthese = synthese.id_synthese
        JOIN observers ON observers.id_area = l_areas.id_area
GROUP BY
    l_areas.id_area
  , bib_areas_types.type_code
  , l_areas.area_code
  , l_areas.area_name
  , l_areas.geom
    );

CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(id_area);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_name);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats(area_code);
CREATE INDEX ON gn_biodivterritory.mv_territory_general_stats USING gist(geom);