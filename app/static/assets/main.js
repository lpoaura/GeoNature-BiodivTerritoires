if (debugMode) var debugLog = console.log.bind(window.console)
else var debugLog = function () {
}

// Select2 de Recherche de territoire

function formatArea(area) {
    if (area.loading) {
        return area.text;
    }

    var $container = $(
        "<div class='clearfix'>" +
        "<div><strong><span id='select2-result-area__area_name'></span></strong>" +
        "&nbsp;(" +
        "<span id='select2-result-area__area_code'></span>)" +
        "&nbsp;" +
        "<span class='badge badge-primary text-right' id='select2-result-area__type_name'></span></div>" +
        "</div>"
    );

    $container.find("#select2-result-area__area_name").text(area.area_name);
    $container.find("#select2-result-area__type_name").text(area.type_name);
    $container.find("#select2-result-area__area_code").text(area.area_code);

    return $container;
}

function formatAreaSelection(area) {
    return area.area_name;
}

$(".search-territory-select").select2({
    ajax: {
        url: "/api/find/area",
        dataType: 'json',
        delay: 250,
        data: function (params) {
            return {
                q: params.term, // search term
                page: params.page
            };
        },
        processResults: function (data, params) {
            // parse the results into the format expected by Select2
            // since we are using custom formatting functions we do not need to
            // alter the remote JSON data, except to indicate that infinite
            // scrolling can be used
            params.page = params.page || 1;

            return {
                results: data.datas,
                pagination: {
                    more: (params.page * 30) < data.total_count
                }
            };
        },
        cache: true
    },
    placeholder: 'Recherchez un territoire',
    minimumInputLength: 3,
    templateResult: formatArea,
    templateSelection: formatAreaSelection
});

function hex(c) {
    var s = "0123456789abcdef";
    var i = parseInt(c);
    if (i == 0 || isNaN(c))
        return "00";
    i = Math.round(Math.min(Math.max(0, i), 255));
    return s.charAt((i - i % 16) / 16) + s.charAt(i % 16);
}

/* Convert an RGB triplet to a hex string */
function convertToHex(rgb) {
    return hex(rgb[0]) + hex(rgb[1]) + hex(rgb[2]);
}

/* Remove '#' in color hex string */
function trim(s) {
    return (s.charAt(0) == '#') ? s.substring(1, 7) : s
}

/* Convert a hex string to an RGB triplet */
function convertToRGB(hex) {
    var color = [];
    color[0] = parseInt((trim(hex)).substring(0, 2), 16);
    color[1] = parseInt((trim(hex)).substring(2, 4), 16);
    color[2] = parseInt((trim(hex)).substring(4, 6), 16);
    return color;
}

function generateColor(colorStart, colorEnd, colorCount) {

    // The beginning of your gradient
    var start = convertToRGB(colorStart);

    // The end of your gradient
    var end = convertToRGB(colorEnd);

    // The number of colors to compute
    var len = colorCount;

    //Alpha blending amount
    var alpha = 0.0;

    var out = [];

    for (i = 0; i < len; i++) {
        var c = [];
        alpha += (1.0 / len);
        c[0] = start[0] * alpha + (1 - alpha) * end[0];
        c[1] = start[1] * alpha + (1 - alpha) * end[1];
        c[2] = start[2] * alpha + (1 - alpha) * end[2];
        out.push(convertToHex(c));
    }

    return out;

}

// Exemplo de como usar


var months = ['jan', 'fév', 'mar', 'avr', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc'];

// var tmp = generateColor('#000000', '#ff0ff0', 10);
//
// for (cor in tmp) {
//     $('#result_show').append("<div style='padding:8px;color:#FFF;background-color:#" + tmp[cor] + "'>COLOR " + cor + "° - #" + tmp[cor] + "</div>")
//
// }

$(document).tooltip({
    selector: '[data-toggle="tooltip"]'
});

// Function to help sum array
const add = (a, b) => a + b


const dataTableFr = {
                sEmptyTable: "Aucune donnée disponible dans le tableau",
                sInfo: "Affichage de l'élément _START_ à _END_ sur _TOTAL_ éléments",
                sInfoEmpty: "Affichage de l'élément 0 à 0 sur 0 élément",
                sInfoFiltered: "(filtré à partir de _MAX_ éléments au total)",
                sInfoPostFix: "",
                sInfoThousands: ",",
                sLengthMenu: "Afficher _MENU_ éléments",
                sLoadingRecords: "Chargement...",
                sProcessing: "Traitement...",
                sSearch: "Rechercher :",
                sZeroRecords: "Aucun élément correspondant trouvé",
                oAria: {
                    sSortAscending: ": activer pour trier la colonne par ordre croissant",
                    sSortDescending: ": activer pour trier la colonne par ordre décroissant"
                },
            }