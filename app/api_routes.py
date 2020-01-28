from flask import Blueprint, jsonify, redirect, url_for
from flask import request
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from sqlalchemy import and_, or_, distinct
from sqlalchemy.sql import func

from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.ref_geo import BibAreasTypes, LAreas
from app.models.synthese import Synthese, CorAreaSynthese
from app.models.taxonomy import Taxref
from app.models.territory import MVTerritoryGeneralStats, MVAreaNtileLimit
from app.utils import get_geojson_feature, DB

api = Blueprint("api", __name__)


@api.route("/find/area")
def find_area():
    """

    :return:
    """
    try:
        search_term = "%{}%".format(request.args.get("q"))
        qarea = (
            DB.session.query(
                LAreas.id_area.label("id"),
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


@api.route("/area/<id_area>")
def redirect_area(id_area):
    """
    redirect tu human readable territory url based on type_code and area_code from id_area, for select2 searches
    :param id_area:
    :return:
    """
    qarea = (
        DB.session.query(BibAreasTypes.type_code, LAreas.area_code,)
        .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
        .filter(LAreas.id_area == id_area)
    )
    area = qarea.first()
    return redirect(
        url_for(
            "rendered.territory",
            type_code=area.type_code.lower(),
            area_code=area.area_code.lower(),
        )
    )


@api.route("/<type_code>/<area_code>")
def main_area_info(type_code, area_code):
    """
    
    """
    try:
        query = (
            DB.session.query(
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
        query = DB.session.query(
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
            DB.session.query(
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


@api.route("/list_taxa/<int:id_area>", methods=["GET"])
def get_taxa_list(id_area):
    """

    :param type:
    :return:
    """
    try:
        reproduction_id = (
            DB.session.query(TNomenclatures.id_nomenclature)
            .join(
                BibNomenclaturesTypes,
                TNomenclatures.id_type == BibNomenclaturesTypes.id_type,
            )
            .filter(
                and_(
                    BibNomenclaturesTypes.mnemonique.like("STATUT_BIO"),
                    TNomenclatures.cd_nomenclature.like("3"),
                )
            )
        ).first()

        query_territory = (
            DB.session.query(
                Taxref.cd_ref.label("id"),
                LAreas.id_area,
                LAreas.area_code,
                Taxref.cd_ref,
                func.split_part(Taxref.nom_vern, ",", 1).label("nom_vern"),
                Taxref.nom_valide,
                Taxref.group1_inpn,
                Taxref.group2_inpn,
                func.count(distinct(Synthese.id_synthese)).label("count_occtax"),
                func.count(distinct(Synthese.observers)).label("count_observer"),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label("count_dataset"),
                func.max(distinct(func.extract("year", Synthese.date_min))).label(
                    "last_year"
                ),
                func.bool_or(
                    Synthese.id_nomenclature_bio_status == reproduction_id
                ).label("reproduction"),
                func.array_agg(distinct(Synthese.id_nomenclature_bio_status)).label(
                    "bio_status"
                ),
            )
            .select_from(CorAreaSynthese)
            .join(Synthese, Synthese.id_synthese == CorAreaSynthese.id_synthese)
            .join(Taxref, Synthese.cd_nom == Taxref.cd_nom)
            .join(LAreas, LAreas.id_area == CorAreaSynthese.id_area)
            .filter(LAreas.id_area == id_area)
            .group_by(
                LAreas.id_area,
                LAreas.area_code,
                Taxref.cd_ref,
                Taxref.nom_vern,
                Taxref.nom_valide,
                Taxref.group1_inpn,
                Taxref.group2_inpn,
            )
            .order_by(Taxref.group1_inpn, Taxref.group2_inpn, Taxref.nom_valide)
        )
        result = query_territory.all()
        count = len(result)
        datas = []
        for r in result:
            datas.append(r._asdict())
        return jsonify({"count": count, "datas": datas}), 200

    except Exception as e:
        return {"Error": str(e)}, 400
