from flask import Blueprint, abort, jsonify, redirect, render_template
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from sqlalchemy import and_, or_
from app.utils import get_geojson_feature
from app import db
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.ref_geo import BibAreasTypes, LAreas
from sqlalchemy.sql import func
from flask import request
from app.models.territory import MVTerritoryGeneralStats, MVAreaNtileLimit

api = Blueprint("api", __name__)


@api.route("/find/area")
def find_area():
    """

    :return:
    """
    try:
        search_term = "%{}%".format(request.args.get("q"))
        qarea = (
            db.session.query(
                BibAreasTypes.type_name,
                BibAreasTypes.type_desc,
                BibAreasTypes.type_code,
                LAreas.area_name,
                LAreas.area_code,
            )
            .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
            .filter(
                or_(
                    func.unaccent(LAreas.area_name).ilike(func.unaccent(search_term)),
                    func.unaccent(LAreas.area_code).ilike(func.unaccent(search_term)),
                )
            )
            .limit(20)
        )
        result = qarea.all()
        count = len(result)
        datas = []
        for r in result:
            datas.append(r._asdict())
        return {"count": count, "datas": datas}, 200
    except Exception as e:
        return {"Error": str(e)}, 400


@api.route("/<type_code>/<area_code>")
def main_area_info(type_code, area_code):
    """
    
    """
    try:
        query = (
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
        result = query.one()
        data = result._asdict()
        return jsonify(data)
    except Exception as e:
        return {"Error": str(e)}, 400


@api.route("/type")
def datas_types():
    """
    
    """
    try:
        query = db.session.query(
            BibDatasTypes.type_protocol,
            BibDatasTypes.type_name,
            TReleasedDatas.data_name,
            TReleasedDatas.data_desc,
        ).join(
            TReleasedDatas,
            BibDatasTypes.id_type == TReleasedDatas.id_type,
            isouter=True,
        )
        result = query.first()
        data = result._asdict()
        return jsonify(data)
    except Exception as e:
        return {"Error": str(e)}, 400


@api.route("/geom/<type_code>/<area_code>", methods=["GET"])
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
        query = (
            db.session.query(
                BibAreasTypes.type_desc,
                LAreas.area_name,
                LAreas.area_code,
                func.ST_Transform(LAreas.geom, 4326).label("geom"),
            )
            .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
            .filter(
                and_(BibAreasTypes.type_code == type_code.upper()),
                LAreas.area_code == area_code,
            )
        ).limit(1)
        result = query.one()
        geometry = get_geojson_feature(result.geom)
        feature = Feature(geometry=to_shape(result.geom))
        feature["properties"]["area_name"] = result.area_name
        feature["properties"]["area_code"] = result.area_code
        return feature
    except Exception as e:
        return {"Error": str(e)}, 400


@api.route("/grid_data/<id_area>/<buffer>/<grid>", methods=["GET"])
def get_grid_datas(id_area, buffer, grid):
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
        qarea = LAreas.query.filter(LAreas.id_area == id_area)
        area = qarea.one()
        qgrid = MVTerritoryGeneralStats.query.filter(
            MVTerritoryGeneralStats.type_code == grid
        ).filter(
            func.ST_Intersects(
                MVTerritoryGeneralStats.geom_local, func.ST_Buffer(area.geom, buffer),
            )
        )
        print("get_grid_datas Query:", qgrid)
        datas = qgrid.all()
        print("RESULT", datas)
        features = []
        for d in datas:
            features.append(d.as_geofeature("geom_4326", "id_area"))
        return FeatureCollection(features)
    except Exception as e:
        return {"Error": str(e)}, 400


@api.route("/territory/conf/ntile/<type>", methods=["GET"])
def get_occtax_ntile(type):
    """

    :param type:
    :return:
    """
    query = MVAreaNtileLimit.query.filter_by(type=type).order_by(MVAreaNtileLimit.ntile)
    ntiles = query.all()
    datas = []
    for r in ntiles:
        datas.append(r.as_dict())
    return jsonify(datas)


@api.route("/territory/conf/ntile/", methods=["GET"])
def get_ntile():
    """

    :param type:
    :return:
    """
    query = MVAreaNtileLimit.query.order_by(MVAreaNtileLimit.type).order_by(
        MVAreaNtileLimit.ntile
    )
    ntiles = query.all()
    datas = []
    for r in ntiles:
        datas.append(r.as_dict())
    return jsonify(datas)
