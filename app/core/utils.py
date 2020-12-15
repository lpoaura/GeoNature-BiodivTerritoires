from flask import current_app
from geoalchemy2.shape import from_shape, to_shape
from geojson import Feature
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from shapely.geometry import asShape
from sqlalchemy import and_

from app.core.env import DB
from app.models.dynamic_content import TDynamicPages, BibDynamicPagesCategory
from app.models.datas import TReleasedDatas, BibDatasTypes
from app.models.taxonomy import (
    TRedlist,
    BibRedlistSource,
    BibRedlistCategories,
    TMaxThreatenedStatus,
)
from app.models.ref_geo import LAreasTypeSelection
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql


def create_tables(db):
    """[summary]

    Args:
        db ([type]): [description]
    """
    db = db
    tables = [
        TDynamicPages.__table__,
        BibDynamicPagesCategory.__table__,
        TReleasedDatas.__table__,
        BibDatasTypes.__table__,
        LAreasTypeSelection.__table__,
        TRedlist.__table__,
        BibRedlistSource.__table__,
        BibRedlistCategories.__table__,
        TMaxThreatenedStatus.__table__,
    ]
    db.metadata.create_all(
        db.engine,
        tables=[
            TDynamicPages.__table__,
            BibDynamicPagesCategory.__table__,
            TReleasedDatas.__table__,
            BibDatasTypes.__table__,
            LAreasTypeSelection.__table__,
            TRedlist.__table__,
            BibRedlistSource.__table__,
            BibRedlistCategories.__table__,
            TMaxThreatenedStatus.__table__,
        ],
    )
    return None


def get_nomenclature_id(mnemonique, cd_nomenclature):
    id_nomenclature = (
        (
            DB.session.query(TNomenclatures.id_nomenclature)
            .join(
                BibNomenclaturesTypes,
                TNomenclatures.id_type == BibNomenclaturesTypes.id_type,
            )
            .filter(
                and_(
                    BibNomenclaturesTypes.mnemonique.like(mnemonique),
                    TNomenclatures.cd_nomenclature.like(cd_nomenclature),
                )
            )
        )
        .first()
        .id_nomenclature
    )
    return id_nomenclature


def geom_from_geojson(data):
    """this function transform geojson geometry into `WKB\
    <https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary>`_\
    data commonly used in PostGIS geometry fields

    :param data: geojson formatted geometry
    :type data: dict

    :return: wkb geometry
    :rtype: str
    """
    try:
        geojson = asShape(data)
        geom = from_shape(geojson, srid=4326)
    except Exception as e:
        current_app.logger.error(
            "[geom_from_geojson] Can't convert geojson geometry to wkb: {}".format(
                str(e)
            )
        )
    return geom


def get_geojson_feature(wkb):
    """return a geojson feature from WKB

    :param wkb: wkb geometry
    :type wkb: str

    :return: geojson
    :rtype: dict
    """
    try:
        geometry = to_shape(wkb)
        feature = Feature(geometry=geometry, properties={})
        return feature
    except Exception as e:
        current_app.logger.error(
            "[get_geojson_feature] Can't convert wkb geometry to geojson: {}".format(
                str(e)
            )
        )


def get_nomenclature(id_nomenclature):
    try:
        query = (
            DB.session.query(
                TNomenclatures.cd_nomenclature,
                TNomenclatures.mnemonique,
                TNomenclatures.definition_fr,
            )
            .filter(TNomenclatures.id_nomenclature == id_nomenclature)
            .first()
        )
        nomenclature = query._asdict()
        return nomenclature
    except Exception as e:
        current_app.logger.error("<get_nomenclature> ERROR: ", e)


def get_redlist_status(cdref):
    query = (
        DB.session.query(
            TRedlist.category,
            TRedlist.criteria,
            BibRedlistSource.context,
            BibRedlistSource.area_name,
            BibRedlistCategories.priority_order,
            BibRedlistCategories.threatened,
        )
        .distinct()
        .filter(TRedlist.cd_ref == cdref)
        .join(BibRedlistSource, BibRedlistSource.id_source == TRedlist.id_source)
        .join(
            BibRedlistCategories,
            BibRedlistCategories.code_category == TRedlist.category,
        )
        .order_by(BibRedlistSource.priority, BibRedlistCategories.priority_order)
        .all()
    )
    list = []
    for r in query:
        list.append(r._asdict())
    return list


def get_max_threatened_status(cdref):
    query = (
        DB.session.query(BibRedlistCategories.threatened)
        .distinct()
        .filter(TRedlist.cd_ref == cdref)
        .filter(BibRedlistSource.id_source == TRedlist.id_source)
        .filter(BibRedlistCategories.code_category == TRedlist.category)
        .order_by(BibRedlistSource.priority, BibRedlistCategories.priority_order)
    )
    print(query)
    result = query.first()
    if result == None:
        return False
    else:
        return result[0]


def redlist_list_is_null(item):
    if len(item["redlist"]) == 0:
        return True
    else:
        return False


def redlist_is_not_null(item):
    if len(item["redlist"]) > 0:
        return True
    else:
        return False


def create_special_pages():
    pages = [
        {
            "url": "footer",
            "link_name": "Footer",
            "navbar_link": False,
            "is_active": False,
            "content": """
            <div class="container-fluid">
                <div class="float-right"><a href="https://www.auvergnerhonealpes.fr/" target="_blank"
                                            title="Région Auvergne-Rhône-Alpes" data-toggle="tooltip"><img
                        src="https://www.auvergnerhonealpes.fr/cms_viewFile.php?idtf=1406&path=logo-partenaire-2017-rvb-pastille-bleue-png.png"
                        height="100px"/></a></div>
                <div class="text-center">
                    <p class="text-muted">
                        <a href="/">Accueil</a> |
                        <a href="/credits" target="_blank">Conception et crédits</a> |
                        <a href="/mentions-legales">Mentions légales</a>
                    <p>
    
                        <div id="clear">
                    <p class="text-muted">
                        Biodiversité des territoires - LPO Auvergne-Rhône-Alpes, 2020
                        <br/>
                        Réalisé avec <a href="https://github.com/lpoaura/GeoNature-BiodivTerritoires" target="_blank">GeoNature-BiodivTerritoires</a>,
                        développé par la <a href="https://auvergne-rhpne-alpes.lpo.fr" target="_blank">LPO
                        Auvergne-Rhône-Alpes</a> avec le soutien financier de la Région Auvergne-Rhône-Alpes
                    </p>
                </div>
            </div>
            """,
        },
        {
            "url": "about",
            "link_name": "A propos",
            "navbar_link": True,
            "navbar_link_order": 1,
            "is_active": True,
        },
        {
            "url": "contact",
            "link_name": "Contact",
            "navbar_link": True,
            "navbar_link_order": 2,
            "is_active": True,
        },
        {
            "url": "credits",
            "link_name": "Crédits",
            "navbar_link": False,
            "is_active": True,
        },
        {
            "url": "mentions-legales",
            "link_name": "Mentions légales",
            "navbar_link": False,
            "is_active": True,
        },
        {
            "url": "home-bonus",
            "link_name": "Complément de l'accueil",
            "navbar_link": False,
            "is_active": False,
            "content": """
            <p> Editez ce contenu dans l'<a href="/admin/tdynamicpages/" target="_blank">interface d'administration</a> (<b>url = home-bonus</b>)</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed 
                do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
                Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris 
                nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor 
                in reprehenderit in voluptate velit esse cillum dolore eu fugiat 
                nulla pariatur. Excepteur sint occaecat cupidatat non proident, 
                sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
            """,
        },
        {
            "url": "datas-intro",
            "link_name": "Introduction de la page Données",
            "navbar_link": False,
            "is_active": False,
            "content": """
            <p>Vous trouverez-ici des ressources OpenData relatives &agrave; cette plateforme:</p>
            <ul>
                <li>Flux de donn&eacute;es&nbsp;;</li>
                <li>Donn&eacute;es t&eacute;l&eacute;chargeables&nbsp;;</li>
                <li>etc.</li>
            </ul>
            """,
        },
        {
            "url": "territory-intro",
            "link_name": "Introduction de la fiche territoire",
            "navbar_link": False,
            "is_active": False,
            "content": "Dans les différents blocs ci-après, vous trouverez des informations de synthèse sur le territoire. Il s'agit des connaissances disponibles qui peuvent s'avérer lacunaires. Le choix a été de mettre en avant les espèces présentant les statuts les plus défavorables.Vous pouvez choisir la distance de recherche des données autour du territoire sélectionné.",
        },
    ]

    for p in pages:
        if len(TDynamicPages.query.filter(TDynamicPages.url == p["url"]).all()) == 0:
            page = TDynamicPages(**p)
            DB.session.add(page)

    DB.session.commit()
