INSERT INTO
    gn_biodivterritory.l_areas_type_selection (id_type)
SELECT id_type
FROM
    ref_geo.bib_areas_types
WHERE
        type_code IN
        ('ZC', 'ZNIEFF2', 'ZNIEFF1', 'APB', 'RNN', 'RNR', 'ZPS', 'SIC', 'ZICO', 'RNCFS', 'RIPN', 'SCEN', 'SCL', 'PNM',
         'PNR', 'RBIOL', 'RBIOS', 'RNC', 'SRAM', 'AA', 'ZSC', 'PSIC', 'PEC', 'UG', 'COM', 'DEP');
