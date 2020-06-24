

INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
SELECT
    t.id_type
  , 'France'
  , 'FR'
  , st_makevalid(st_union(geom))
  , st_centroid(st_makevalid(st_union(geom)))
  , 'SQL - Union des communes'
  , NULL
  , now()
  , now()
FROM
    ref_geo.l_areas
  , (SELECT t1.id_type FROM ref_geo.bib_areas_types t1 WHERE type_code LIKE 'PAY') AS t
WHERE
        l_areas.id_type = (SELECT t2.id_type FROM ref_geo.bib_areas_types AS t2 WHERE t2.type_code LIKE 'COM')
GROUP BY
    t.id_type;

INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
SELECT
    t.id_type
  , 'Auvergne-Rhône-Alpes'
  , 'R84'
  , st_makevalid(st_union(geom))
  , st_centroid(st_makevalid(st_union(geom)))
  , 'SQL - Union des communes'
  , NULL
  , now()
  , now()
FROM
    ref_geo.l_areas
  , (SELECT t1.id_type FROM ref_geo.bib_areas_types t1 WHERE type_code LIKE 'REG') AS t
WHERE
        l_areas.id_type = (SELECT t2.id_type FROM ref_geo.bib_areas_types AS t2 WHERE t2.type_code LIKE 'COM') AND
        left(l_areas.area_code, 2) IN ('03', '15', '43', '63', '01', '07', '26', '38', '42', '69', '73', '74')
GROUP BY
    t.id_type;


INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
SELECT
    t.id_type
  , 'Auvergne'
  , 'R83'
  , st_makevalid(st_union(geom))
  , st_centroid(st_makevalid(st_union(geom)))
  , 'SQL - Union des communes'
  , NULL
  , now()
  , now()
FROM
    ref_geo.l_areas
  , (SELECT t1.id_type FROM ref_geo.bib_areas_types t1 WHERE type_code LIKE 'REG') AS t
WHERE
        l_areas.id_type = (SELECT t2.id_type FROM ref_geo.bib_areas_types AS t2 WHERE t2.type_code LIKE 'COM') AND
        left(l_areas.area_code, 2) IN ('03', '15', '43', '63')
GROUP BY
    t.id_type;

INSERT INTO
    ref_geo.l_areas(id_type, area_name, area_code, geom, centroid, source, comment, meta_create_date, meta_update_date)
SELECT
    t.id_type
  , 'Rhône-Alpes'
  , 'R82'
  , st_makevalid(st_union(geom))
  , st_centroid(st_makevalid(st_union(geom)))
  , 'SQL - Union des communes'
  , NULL
  , now()
  , now()
FROM
    ref_geo.l_areas
  , (SELECT t1.id_type FROM ref_geo.bib_areas_types t1 WHERE type_code LIKE 'REG') AS t
WHERE
        l_areas.id_type = (SELECT t2.id_type FROM ref_geo.bib_areas_types AS t2 WHERE t2.type_code LIKE 'COM') AND
        left(l_areas.area_code, 2) IN ('01', '07', '26', '38', '42', '69', '73', '74')
GROUP BY
    t.id_type;
