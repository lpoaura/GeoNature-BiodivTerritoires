from flask import Blueprint, abort, jsonify, redirect, render_template
from geoalchemy2 import func
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from sqlalchemy import and_
from app.utils import json_resp
import config
from app import db
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.ref_geo import BibAreasTypes, LAreas

api = Blueprint("api", __name__)


@api.route("/<type_code>/<area_code>")
def main_area_info(type_code, area_code):
    """
    
    """
    qterritory = (
        db.session.query(
            BibAreasTypes.type_name,
            BibAreasTypes.type_desc,
            LAreas.area_name,
            LAreas.area_code,
        )
        .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
        .filter(
            and_(BibAreasTypes.type_code == type_code.upper()),
            LAreas.area_code == area_code,
        )
    )
    result = qterritory.one()
    data = result._asdict()
    return jsonify(data)


@api.route("/type")
def datas_types():
    """
    
    """
    qdatatype = db.session.query(
        BibDatasTypes.type_protocol,
        BibDatasTypes.type_name,
        TReleasedDatas.data_name,
        TReleasedDatas.data_desc,
    ).join(
        TReleasedDatas, BibDatasTypes.id_type == TReleasedDatas.id_type, isouter=True
    )
    result = qdatatype.first()
    data = result._asdict()
    return jsonify(data)


@api.route("/geom/<type_code>/<area_code>", methods=["GET"])
@json_resp
def get_geojson_area(type_code, area_code):
    """Get one enabled municipality by insee code
        ---
        tags:
          - Reférentiel géo
        parameters:
          - name: insee
            in: path
            type: string
            required: true
            default: none
            properties:
              area_name:
                type: string
                description: Municipality name
              area_code:
                type: string
                description: Municipality insee code
              geometry:
                type: geometry
        responses:
          200:
            description: A municipality
        """
    try:
        qterritory = (
            db.session.query(
                BibAreasTypes.type_desc,
                LAreas.area_name,
                LAreas.area_code,
                func.ST_Transform(LAreas.geom, 4326).label('geom')
            )
            .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
            .filter(
                and_(BibAreasTypes.type_code == type_code.upper()),
                LAreas.area_code == area_code,
            )
        )
        result = qterritory.one()._asdict()
        geometry = to_shape(qterritory.geom)
        feature = Feature(geometry=to_shape(qterritory.geom))
        feature["properties"]["area_name"] = qterritory.area_name
        feature["properties"]["area_code"] = qterritory.area_code
        return feature
    except Exception as e:
        return {"message": str(e)}, 400
