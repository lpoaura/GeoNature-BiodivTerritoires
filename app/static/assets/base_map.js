var baseLayers = {
  //'carte': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}),
  carte: {
    layer: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      minZoom: 0,
      maxZoom: 18,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      tileSize: 256, // les tuiles du Géooportail font 256x256px
    }),
    title: "Carte",
  },
  ortho: {
    layer: L.tileLayer(
      "https://wxs.ign.fr/" +
        "pratique" +
        "/geoportail/wmts?&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/jpeg&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}",
      {
        minZoom: 0,
        maxZoom: 18,
        attribution: "IGN-F/Geoportail",
        tileSize: 256, // les tuiles du Géooportail font 256x256px
      }
    ),
    title: "Orthophotographie",
  },
  pollum: {
    layer: L.tileLayer.wms("https://data.lpo-aura.org/geoserver/wms?", {
      layers: "opendata:pollum_aura",
      minZoom: 0,
      maxZoom: 18,
      attribution:
        'Pollution lumineuse généré d\'après les données de <a href="https://ngdc.noaa.gov/eog/viirs/download_dnb_composites.html" target="_blank" data-toggle="tooltip" title="Lien vers les données source"><b>Earth Observation Group, NOAA National Centers for Environmental Information (NCEI)</b></a>',
      tileSize: 256, // les tuiles du Géooportail font 256x256px
    }),
    title: "Pollution lumineuse",
    url_info: "/pollum",
  },
  clc: {
    layer: L.tileLayer.wms(
      "http://wxs.ign.fr/corinelandcover/geoportail/r/wms?",
      {
        layers: "LANDCOVER.CLC18_FR",
        minZoom: 0,
        maxZoom: 18,
        attribution: "Corine Land Cover 2018",
        tileSize: 256, // les tuiles du Géooportail font 256x256px
      }
    ),
    title: "Corine Land Cover",
    url_info: "/clc",
  },
};
//
// var baseLayers = {};
//
// populateBaseLayer = function (layer) {
//     debugLog('layerData', layer);
//     var layer_datas = {};
//     if (layer.type === 'wms') {
//         var loadMethod = L.tileLayer.wms(layer.url, layer.options);
//     } else {
//         var loadMethod = L.tileLayer(layer.url, layer.options);
//     }
//     ;
//
//     layer_datas[layer] = loadMethod;
//     if (layer.url_info) {
//         layer_datas['url_info'] = layer.url_info
//     }
//     ;
//     layer_datas['title'] = layer.title;
//     debugLog(layer.name, layer_datas);
//     baseLayers[layer.name] = layer_datas
// };
//
// baseLayersList.forEach(layer => populateBaseLayer(layer));
//
// debugLog('<baseLayers>',baseLayers);
// debugLog( '<firstLayer>', Object.keys(baseLayers)[0]);

var mapValues = {
  baseLayerType: Object.keys(baseLayers)[0],
  baseLayerInfoControl: null,
};

var baseLayerControl = L.control({ position: "bottomleft" });

baseLayerControl.onAdd = function () {
  var div = L.DomUtil.create("div", "base_layer_control");
  var keys = Object.keys(baseLayers);
  var options = "";
  for (var i = 0; i < keys.length; i++) {
    options =
      options +
      '<option value="' +
      keys[i] +
      '">' +
      baseLayers[keys[i]].title +
      "</option>";
  }
  div.innerHTML +=
    '<select class="custom-select custom-select-sm mb-3" id="situationBaseLayerSelect" name="title">' +
    options +
    "</select>";
  return div;
};

function baseMap(idAttr) {
  map = L.map(idAttr).setView([45, 5], 10);
  debugLog("<baseLayer>", baseLayers[mapValues.baseLayerType]);
  var baseLayer = baseLayers[mapValues.baseLayerType].layer;
  baseLayer.addTo(map);

  baseLayerControl.addTo(map);

  $(document).on("change", "#situationBaseLayerSelect", function () {
    debugLog(this.value);
    baseLayer.removeFrom(map);
    baseLayer = baseLayers[this.value].layer;
    baseLayer.addTo(map);
    if (mapValues.baseLayerInfoControl !== null) {
      map.removeControl(mapValues.baseLayerInfoControl);
    }
    mapValues.baseLayerInfoControl = L.control({ position: "bottomleft" });
    if ("url_info" in baseLayers[this.value]) {
      var url = baseLayers[this.value].url_info;
      mapValues.baseLayerInfoControl.onAdd = function () {
        var div = L.DomUtil.create("div", "base_layer_info");
        div.innerHTML =
          '<a type="button" class="btn btn-sm btn-info" style="color: whitesmoke" id="baseLayerInfo" data-toggle="tooltips" target="_blank" href="' +
          url +
          '" title="Informations relatives à la couche de fond">Infos</a>';
        return div;
      };
      mapValues.baseLayerInfoControl.addTo(map);
    }
  });

  return map;
}

var territoryStyle = {
  color: "#ea09b9",
  weight: 3,
  opacity: 0.65,
  fillOpacity: 0,
};
