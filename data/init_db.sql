/*******************************
 *   TERRITORY GENERAL STATS   *
 *******************************/
DROP MATERIALIZED VIEW gn_biodivterritory.mv_territory_general_stats CASCADE;

create materialized view gn_biodivterritory.mv_territory_general_stats as
(
with observers as (
    select distinct cor_area_synthese.id_area,
                    unaccent(trim(regexp_split_to_table(synthese.observers, ','))) as observer
    from gn_synthese.synthese
             join gn_synthese.cor_area_synthese on synthese.id_synthese = cor_area_synthese.id_synthese
)
select l_areas.id_area,
       count(distinct synthese.cd_nom)     as count_taxa,
       count(synthese.id_synthese)         as count_occtax,
       count(distinct synthese.id_dataset) as count_dataset,
       count(distinct synthese.date_min)   as count_date,
       count(distinct observers.observer)  as count_observer

from ref_geo.l_areas
         join gn_synthese.cor_area_synthese on l_areas.id_area = cor_area_synthese.id_area
         join gn_synthese.synthese on cor_area_synthese.id_synthese = synthese.id_synthese
         join observers on observers.id_area = l_areas.id_area
group by l_areas.id_area
    );

/***********************************
 *   TERRITORY GEO GENERAL STATS   *
 ***********************************/

create materialized view gn_biodivterritory.mv_territory_geo_general_stats as
(
    with observers as (
        select distinct cor_area_synthese.id_area,
                        unaccent(trim(regexp_split_to_table(synthese.observers, ','))) as observer
        from gn_synthese.synthese
                 join gn_synthese.cor_area_synthese on synthese.id_synthese = cor_area_synthese.id_synthese
    )
)