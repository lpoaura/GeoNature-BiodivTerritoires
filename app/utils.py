from flask import current_app
from flask_admin import Admin
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.shape import from_shape, to_shape
from geojson import Feature
from shapely.geometry import asShape
from sqlalchemy import String
from sqlalchemy import func, select
from sqlalchemy.sql.functions import GenericFunction

DB = SQLAlchemy()
admin = Admin(name="GnBT", template_mode="bootstrap3")
assets = Environment()


def create_schemas(db):
    """create db schemas at first launch

    :param db: db connection
    """
    schemas = ["gn_biodivterritory"]
    for schema in schemas:
        print("create DB schema {}".format(schema))
        db.session.execute("CREATE SCHEMA IF NOT EXISTS {}".format(schema))
    db.session.commit()


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
    """ return a geojson feature from WKB

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


class RefNomenclatureGetIdNomenclature(GenericFunction):
    __function_args__ = {"schema": "ref_nomenclatures"}
    type = String
    package = "nomenclature"
    name = "get_id_nomenclature"
    identifier = "get_id_nomenclature"
    schema_name = "ref_nomenclatures"


print("TEST FUNCTION", select([func.nomenclature.get_id_nomenclature()]))
print(
    "TEST FUNCTION RESULT",
    select([func.nomenclature.get_id_nomenclature("STATUT_BIO", "3")]),
)
