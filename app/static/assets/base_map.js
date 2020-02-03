var baseLayers = {
    //'carte': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}),
    'carte':
        {
            layer: L.tileLayer('https://wxs.ign.fr/' + 'pratique' + '/geoportail/wmts?&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
                {
                    minZoom: 0,
                    maxZoom: 18,
                    attribution: "IGN-F/Geoportail",
                    tileSize: 256 // les tuiles du Géooportail font 256x256px
                }
            ), image: '/static/images/carte.png'
            , title: 'Carte'
        }
    ,
    'ortho': {
        layer: L.tileLayer('https://wxs.ign.fr/' + 'pratique' + '/geoportail/wmts?&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            {
                minZoom: 0,
                maxZoom: 18,
                attribution: "IGN-F/Geoportail",
                tileSize: 256 // les tuiles du Géooportail font 256x256px
            }
        ), image: '/static/images/ortho.png'
        , title: 'Orthophotographie'
    },
    'polllum': {
        layer: L.tileLayer.wms('https://bdd.fauneauvergnerhonealpes.org/geoserver/opendata/wms?',
            {
                layers: "opendata:Intensite lumineuse",
                minZoom: 0,
                maxZoom: 18,
                attribution: "Pollution lumineuse",
                tileSize: 256 // les tuiles du Géooportail font 256x256px
            }
        ), image: '/static/images/polllum.png'
        , title: 'Pollution lumineuse'
    },
    'clc': {
        layer: L.tileLayer.wms('http://wxs.ign.fr/corinelandcover/geoportail/r/wms?', {
                layers: "LANDCOVER.CLC18_FR",
                minZoom: 0,
                maxZoom: 18,
                attribution: "CLC",
                tileSize: 256 // les tuiles du Géooportail font 256x256px
            }
        ), image: '/static/images/ortho.png',
        title: 'CLC'
    }
};

var mapValues = {
    'baseLayerType': 'carte'
};

baseLayerControl = L.control({position: 'bottomleft'});
// baseLayerControl.onAdd = function () {
//     var div = L.DomUtil.create('div', 'base_layer_control');
//     div.innerHTML += '<img src="/static/images/ortho.png" id="baseLayerControlImage" data-toggle="tooltip" data-placement="top" title="Changer de fond de carte" width="50" height="50"/>';
//     return div
// };

baseLayerControl.onAdd = function () {
    var div = L.DomUtil.create('div', 'base_layer_control');
    keys = Object.keys(baseLayers);
    options = '';
    for (var i = 0; i < keys.length; i++) {
        console.log(keys[i], baseLayers[keys[i]].desc);
        options = options + '<option value="' + keys[i] + '">' + baseLayers[keys[i]].title + '</option>'
    }
    console.log('<options>', options)
    div.innerHTML += '<select class="custom-select custom-select-sm mb-3" id="situationBaseLayerSelect" name="title">'
        + options
        + '</select>';
    return div
};


// [Carte d'état des connaissances du territoire] <FOND DE CARTE> : Switch du fond : carte vs ortho


function baseMap(idAttr) {
    map = L.map(idAttr).setView([45, 5], 10);
    var baseLayer = baseLayers[mapValues.baseLayerType].layer;
    baseLayer.addTo(map);

    baseLayerControl.addTo(map);

    map.on('baselayerchange', function (e) {
        console.log('<baselayerchange>', e.layer);
    });

    $(document).on('change', '#situationBaseLayerSelect', function () {
        console.log(this.value);
        baseLayer.removeFrom(map);
        baseLayer = baseLayers[this.value].layer;
        baseLayer.addTo(map);
    });

    // $(document).on('click', '.base_layer_control', function () {
    //     if (mapValues.baseLayerType == 'carte') {
    //         $("#baseLayerControlImage").attr('src', "/static/images/carte.png");
    //         map.removeLayer(baseLayers[mapValues.baseLayerType.layer]);
    //         mapValues.baseLayerType = 'ortho';
    //         baseLayers[mapValues.baseLayerType.layer].addTo(map);
    //     } else if {
    //         $("#baseLayerControlImage").
    //     attr('src', "/static/images/ortho.png");
    //     map.removeLayer(baseLayers[mapValues.baseLayerType.layer]);
    //     mapValues.baseLayerType = 'carte';
    //     baseLayers[mapValues.baseLayerType.layer].addTo(map);
    // }
    // });


    return map

}


var territoryStyle = {
    "color": "#ea09b9",
    "weight": 3,
    "opacity": 0.65,
    "fillOpacity": 0
};
