INSERT INTO
    gn_biodivterritory.l_areas_type_selection (id_type)
SELECT id_type
FROM
    ref_geo.bib_areas_types
WHERE
        type_code IN (select unnest(string_to_array(:'_areas',' ')))
ON CONFLICT DO NOTHING;
