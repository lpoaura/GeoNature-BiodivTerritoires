var baseLayers = {
    //'carte': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}),
    'carte': L.tileLayer('https://wxs.ign.fr/' + 'pratique' + '/geoportail/wmts?&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
        {
            minZoom: 0,
            maxZoom: 18,
            attribution: "IGN-F/Geoportail",
            tileSize: 256 // les tuiles du Géooportail font 256x256px
        }
    )
    ,
    'ortho': L.tileLayer('https://wxs.ign.fr/' + 'pratique' + '/geoportail/wmts?&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
        {
            minZoom: 0,
            maxZoom: 18,
            attribution: "IGN-F/Geoportail",
            tileSize: 256 // les tuiles du Géooportail font 256x256px
        }
    )
};

var mapValues = {
    'baseLayerType': 'carte'
};

baseLayerControl = L.control({position: 'bottomleft'});
baseLayerControl.onAdd = function () {
    var div = L.DomUtil.create('div', 'base_layer_control');
    div.innerHTML += '<img src="/static/images/ortho.png" id="baseLayerControlImage" data-toggle="tooltip" data-placement="top" title="Changer de fond de carte" width="50" height="50"/>';
    return div
};


// [Carte d'état des connaissances du territoire] <FOND DE CARTE> : Switch du fond : carte vs ortho


function baseMap(idAttr) {
    map = L.map(idAttr).setView([45, 5], 10);
    baseLayers[mapValues.baseLayerType].addTo(map);

    baseLayerControl.addTo(map);

    map.on('baselayerchange', function (e) {
        console.log('<baselayerchange>', e.layer);
    });

    $(document).on('click', '.base_layer_control', function () {
        if (mapValues.baseLayerType == 'carte') {
            $("#baseLayerControlImage").attr('src', "/static/images/carte.png");
            map.removeLayer(baseLayers[mapValues.baseLayerType]);
            mapValues.baseLayerType = 'ortho';
            baseLayers[mapValues.baseLayerType].addTo(map);
        } else {
            $("#baseLayerControlImage").attr('src', "/static/images/ortho.png");
            map.removeLayer(baseLayers[mapValues.baseLayerType]);
            mapValues.baseLayerType = 'carte';
            baseLayers[mapValues.baseLayerType].addTo(map);
        }
    });
    return map
}