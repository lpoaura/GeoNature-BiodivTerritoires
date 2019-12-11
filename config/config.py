
# -*- coding:utf-8 -*-

# Mettre l'application en mode debug ou pas
modeDebug = True

# Connexion de l'application à la BDD
# Remplacer user, monpassachanger, IPADRESSE (localhost si la BDD est sur le même serveur que l'application), 
# eventuellement le port de la BDD et le nom de la BDD avec l'utilisateur qui a des droits de lecture sur les vues de l'atlas (user_pg dans settings.ini)
database_connection = "postgresql://fcloitre:Philogas80@localhost:5432/gn2dev"

#################################
#################################
### Customisation application ###
#################################
#################################

# Nom du Site
SITE_NAME = "Biodiv'Territoires"
#SITE_NAME = SITE_NAME.encode('utf-8') # Fonction permettant d'encoder ce nom en utf-8, à ne pas modifier



# URL de l'application depuis la racine du domaine
# ex "/atlas" pour une URL: http://mon-domaine/atlas OU "" si l'application est accessible à la racine du domaine
URL_APPLICATION = ""


###########################
###### Cartographie #######
###########################

# Clé IGN si vous utilisez l'API Geoportail pour afficher les fonds cartographiques
IGNAPIKEY = 'myIGNkey';

# Configuration des cartes (centre du territoire, couches CARTE et ORTHO, échelle par défaut...)
MAP = {
    'LAT_LONG': [44.7952, 6.2287],
    'FIRST_MAP': {
            'url' : 'http://gpp3-wxs.ign.fr/'+IGNAPIKEY+'/wmts?LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-EXPRESS.STANDARD&EXCEPTIONS=text/xml&FORMAT=image/jpeg&SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&STYLE=normal&TILEMATRIXSET=PM&&TILEMATRIX={z}&TILECOL={x}&TILEROW={y}',
            'attribution' : '&copy; <a href="http://www.ign.fr/">IGN</a>',
            'tileName' : 'IGN'
    },
    'SECOND_MAP' : {'url' :'https://gpp3-wxs.ign.fr/'+IGNAPIKEY+'/geoportail/wmts?LAYER=ORTHOIMAGERY.ORTHOPHOTOS&EXCEPTIONS=text/xml&FORMAT=image/jpeg&SERVICE=WMTS&VERSION=1.0.0&REQUEST=GetTile&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
            'attribution' : '&copy; <a href="http://www.ign.fr/">IGN</a>',
            'tileName' : 'Ortho IGN'
    },
    'ZOOM' : 10,
    # Pas du slider sur les annees d'observations: 1 = pas de 1 an sur le slider
    'STEP': 1,
    # Couleur et épaisseur des limites du territoire
    'BORDERS_COLOR': '#000000',
    'BORDERS_WEIGHT': 3
}

# Affichage des observations par maille ou point
# True = maille / False = point
AFFICHAGE_MAILLE = False

# Niveau de zoom à partir duquel on passe à l'affichage en point (si AFFICHAGE_MAILLE = False)
ZOOM_LEVEL_POINT = 11

# Limite du  nombre d'observations à partir duquel on passe à l'affichage en cluster
LIMIT_CLUSTER_POINT = 1000

# URL d'accès aux photos et autres médias (URL racine). Par exemple l'url d'accès à Taxhub
# Cette url sera cachée aux utilisateurs de l'atlas
REMOTE_MEDIAS_URL = "http://mondomaine.fr/taxhub/"
# Racine du chemin des fichiers médias stockés dans le champ "chemin" de "atlas.vm_medias"
# Seule cette partie de l'url sera visible pour les utilisateurs de l'atlas
REMOTE_MEDIAS_PATH = "static/medias/"

# URL de TaxHub (pour génération à la volée des vignettes des images).
# Si le service Taxhub n'est pas utilisé, commenter la variable
TAXHUB_URL = "http://mondomaine.fr/taxhub"

#############################
#### Pages statistiques #####
#############################

# Permet de lister les pages statiques souhaitées et de les afficher dynamiquement dans le menu sidebar
# Les pictos se limitent au Glyphicon proposés par Bootstrap (https://getbootstrap.com/docs/3.3/components/)
STATIC_PAGES = {
    'presentation': {'title': u"Présentation de l'atlas", 'picto': 'glyphicon-question-sign', 'order': 0, 'template': 'static/custom/templates/presentation.html'}
}
