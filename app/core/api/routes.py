from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask.wrappers import Response
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from pypnnomenclature.models import TNomenclatures
from sqlalchemy import and_, distinct, or_
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.sql import case, func, funcfilter

from app.core.env import DB, cache
from app.core.utils import (
    get_nomenclature_id,
    get_redlist_status,
    is_secured_area,
)
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.ref_geo import (
    BibAreasTypes,
    LAreas,
    LAreasTypeSelection,
    MVLAreasAutocomplete,
)
from app.models.synthese import CorAreaSynthese, Synthese
from app.models.taxonomy import (
    Taxref,
    TaxrefProtectionEspeces,
    TMaxThreatenedStatus,
)
from app.models.territory import (
    MVAreaNtileLimit,
    MVGeneralStats,
    MVTerritoryGeneralStats,
)

api = Blueprint("api", __name__)

genStats = {}

diffusion_level_id = get_nomenclature_id(
    "NIV_PRECIS", current_app.config["FILTER_CD_NOMENCLATURE_DIFFUSION_LEVEL"]
)
sensitivity_id = get_nomenclature_id(
    "SENSIBILITE", current_app.config["FILTER_CD_NOMENCLATURE_SENSITIVITY"]
)
absent_id = get_nomenclature_id(
    "STATUT_OBS",
    current_app.config["FILTER_NOT_CD_NOMENCLATURE_OBSERVATION_STATUS"],
)

CACHE_TIMEOUT = current_app.config["CACHE_TIMEOUT"]


@api.route("/find/area")
def find_area() -> Response:
    """

    :return:
    """
    try:
        search_name = f"%{request.args.get('q')}%"
        search_code = request.args.get("q")
        query = (
            DB.session.query(
                MVLAreasAutocomplete.id,
                MVLAreasAutocomplete.type_name,
                MVLAreasAutocomplete.type_desc,
                MVLAreasAutocomplete.type_code,
                MVLAreasAutocomplete.area_name,
                MVLAreasAutocomplete.area_code,
            )
            .filter(
                or_(
                    MVLAreasAutocomplete.search_area_name.like(
                        func.unaccent(search_name.lower())
                    ),
                    MVLAreasAutocomplete.area_code == search_code,
                )
            )
            .order_by(func.length(MVLAreasAutocomplete.area_name))
            .limit(20)
        )
        result = query.all()
        count = len(result)
        datas = []
        for r in result:
            datas.append(r._asdict())
        DB.session.commit()
        return {"count": count, "datas": datas}, 200

    except Exception as e:
        current_app.logger.error(f"<find_area> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/area/<id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def redirect_area(id_area: int) -> Response:
    """
    redirect tu human readable territory url based on type_code and area_code
    from id_area, for select2 searches
    :param id_area:
    :return:
    """
    try:
        query = (
            DB.session.query(
                BibAreasTypes.type_code,
                LAreas.area_code,
            )
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
            .filter(LAreas.id_area == id_area)
        )
        area = query.first()
        DB.session.commit()
        return redirect(
            url_for(
                "rendered.territory",
                type_code=area.type_code.lower(),
                area_code=area.area_code.lower(),
            )
        )
    except Exception as e:
        current_app.logger.error(f"<redirect_area> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/homestats")
@cache.cached(timeout=CACHE_TIMEOUT)
def home_stats() -> Response:
    """Home page general stats

    Returns:
        json: General statistics
    """

    try:
        query = DB.session.query(MVGeneralStats)
        stats = query.one()
        DB.session.commit()
        return jsonify(stats.as_dict())
    except Exception as e:
        current_app.logger.error("<home_stats> ERROR:", e)
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/<type_code>/<area_code>")
@cache.cached(timeout=CACHE_TIMEOUT)
def main_area_info(type_code: str, area_code: str) -> Response:
    try:
        query = (
            DB.session.query(
                BibAreasTypes.type_name,
                BibAreasTypes.type_desc,
                LAreas.area_name,
                LAreas.area_code,
            )
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
            .filter(
                and_(BibAreasTypes.type_code == type_code.upper()),
                LAreas.area_code == area_code,
            )
        )
        result = query.one()
        data = result._asdict()
        DB.session.commit()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"<main_area_info> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/surrounding_areas/<string:type_code>/<string:area_code>")
@api.route(
    "/surrounding_areas/<string:type_code>/<string:area_code>/<int:buffer>"
)
@cache.cached(timeout=CACHE_TIMEOUT)
def get_surrounding_area(
    type_code: str, area_code: str, buffer: int = 10000
) -> Response:
    """

    :param type_code:
    :param area_code:
    :return:
    """
    try:
        area = (
            DB.session.query(LAreas.id_area, LAreas.geom).filter(
                LAreas.area_code == area_code,
                BibAreasTypes.type_code == type_code,
            )
        ).first()

        selected_type_codes = DB.session.query(
            LAreasTypeSelection.id_type
        ).all()
        select = []
        for s in selected_type_codes:
            select.append(s[0])

        q_gen_stats = (
            DB.session.query(
                BibAreasTypes.type_name,
                BibAreasTypes.type_desc,
                BibAreasTypes.type_code,
                MVTerritoryGeneralStats.area_code,
                MVTerritoryGeneralStats.area_name,
                MVTerritoryGeneralStats.id_area,
                MVTerritoryGeneralStats.count_dataset,
                MVTerritoryGeneralStats.count_observer,
                MVTerritoryGeneralStats.count_date,
                MVTerritoryGeneralStats.count_taxa,
                MVTerritoryGeneralStats.last_obs,
                MVTerritoryGeneralStats.count_threatened,
                MVTerritoryGeneralStats.count_occtax,
            )
            .join(
                BibAreasTypes,
                BibAreasTypes.type_code == MVTerritoryGeneralStats.type_code,
            )
            .filter(
                and_(
                    MVTerritoryGeneralStats.geom_local.ST_Intersects(
                        func.ST_Buffer(area.geom, buffer)
                    ),
                    BibAreasTypes.id_type.in_(select),
                    MVTerritoryGeneralStats.id_area != area.id_area,
                )
            )
        )
        results = q_gen_stats.all()
        data = []
        for r in results:
            data.append(r._asdict())
        DB.session.commit()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"<get_surrounding_area> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/type")
@cache.cached(timeout=CACHE_TIMEOUT)
def datas_types() -> Response:
    """"""
    try:
        query = DB.session.query(
            BibDatasTypes.type_protocol,
            BibDatasTypes.type_name,
            TReleasedDatas.data_name,
            TReleasedDatas.data_desc,
        ).join(
            BibDatasTypes,
            BibDatasTypes.id_type == TReleasedDatas.id_type,
            isouter=True,
        )
        result = query.first()
        data = result._asdict()
        DB.session.commit()
        return jsonify(data)
    except Exception as e:
        current_app.logger.error("<datas_types> ERROR:", e)
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/geom/<string:type_code>/<string:area_code>", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_geojson_area(type_code: str, area_code: str) -> Response:
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
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
            .filter(
                and_(BibAreasTypes.type_code == type_code.upper()),
                LAreas.area_code == area_code,
            )
        ).limit(1)
        result = query.one()
        feature = Feature(geometry=to_shape(result.geom))
        feature["properties"]["area_name"] = result.area_name
        feature["properties"]["area_code"] = result.area_code
        DB.session.commit()
        return feature
    except Exception as e:
        current_app.logger.error("<get_geojson_area> ERROR:", e)
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route(
    "/grid_data/<int:id_area>/<int:buffer>/<string:grid>", methods=["GET"]
)
@cache.cached(timeout=CACHE_TIMEOUT)
@cache.cached(timeout=CACHE_TIMEOUT)
def get_grid_datas(id_area: int, buffer: int, grid: str) -> Response:
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
                MVTerritoryGeneralStats.geom_local,
                func.ST_Buffer(area.geom, buffer),
            )
        )
        datas = qgrid.all()
        features = []
        for d in datas:
            features.append(d.as_geofeature("geom_4326", "id_area"))
        DB.session.commit()
        return FeatureCollection(features)
    except Exception as e:
        current_app.logger.error("<get_grid_datas> ERROR:", e)
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/territory/conf/ntile/", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_ntile() -> Response:
    """

    :param type:
    :return:
    """
    try:
        query = MVAreaNtileLimit.query.order_by(
            MVAreaNtileLimit.type
        ).order_by(MVAreaNtileLimit.ntile)
        ntiles = query.all()
        datas = []
        for r in ntiles:
            datas.append(r.as_dict())
        DB.session.commit()
        return jsonify(datas)
    except Exception as e:
        current_app.logger.error(f"<get_ntile> ERROR  {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/list_taxa/<int:id_area>", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_taxa_list(id_area: int) -> Response:
    """

    :param type:
    :return:
    """
    try:
        reproduction_id = get_nomenclature_id("STATUT_BIO", "3")
        query_territory = (
            DB.session.query(
                Taxref.cd_ref.label("id"),
                Taxref.cd_ref,
                func.split_part(Taxref.nom_vern, ",", 1).label("nom_vern"),
                Taxref.lb_nom,
                Taxref.group2_inpn,
                func.coalesce(TMaxThreatenedStatus.threatened, False).label(
                    "threatened"
                ),
                func.count(distinct(Synthese.id_synthese)).label(
                    "count_occtax"
                ),
                func.count(distinct(Synthese.observers)).label(
                    "count_observer"
                ),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label(
                    "count_dataset"
                ),
                func.max(
                    distinct(func.extract("year", Synthese.date_min))
                ).label("last_year"),
                func.array_agg(
                    aggregate_order_by(
                        distinct(func.extract("year", Synthese.date_min)),
                        func.extract("year", Synthese.date_min).desc(),
                    )
                ).label("list_years"),
                func.array_agg(
                    aggregate_order_by(
                        distinct(func.extract("month", Synthese.date_min)),
                        func.extract("month", Synthese.date_min).asc(),
                    )
                ).label("list_months"),
                func.bool_or(
                    Synthese.id_nomenclature_bio_status == reproduction_id
                ).label("reproduction"),
                func.max(distinct(func.extract("year", Synthese.date_min)))
                .filter(Synthese.id_nomenclature_bio_status == reproduction_id)
                .label("last_year_reproduction"),
                func.array_agg(distinct(TNomenclatures.mnemonique)).label(
                    "bio_status"
                ),
                case(
                    [(func.count(TaxrefProtectionEspeces.cd_nom) > 0, True)],
                    else_=False,
                ).label("protection"),
            )
            .select_from(Taxref)
            .join(Synthese, Synthese.cd_nom == Taxref.cd_nom)
            .join(
                CorAreaSynthese,
                Synthese.id_synthese == CorAreaSynthese.id_synthese,
            )
            .outerjoin(
                TNomenclatures,
                TNomenclatures.id_nomenclature
                == Synthese.id_nomenclature_bio_status,
            )
            .outerjoin(
                TMaxThreatenedStatus,
                TMaxThreatenedStatus.cd_nom == Taxref.cd_nom,
            )
            .outerjoin(
                TaxrefProtectionEspeces,
                TaxrefProtectionEspeces.cd_nom == Taxref.cd_nom,
            )
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .group_by(
                func.coalesce(TMaxThreatenedStatus.threatened, False),
                Taxref.cd_ref,
                Taxref.nom_vern,
                Taxref.lb_nom,
                Taxref.group2_inpn,
            )
            .order_by(
                func.coalesce(TMaxThreatenedStatus.threatened, False).desc(),
                func.count(distinct(Synthese.id_synthese)).desc(),
                Taxref.group2_inpn,
            )
        )
        if not is_secured_area(id_area):
            query_territory = query_territory.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )
        result = query_territory.all()
        count = len(result)
        data = []
        for r in result:
            dict = r._asdict()
            data.append(dict)
        DB.session.commit()
        return jsonify({"count": count, "data": data}), 200

    except Exception as e:
        error = "<get_taxa_list> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400
    finally:
        DB.session.close()


@api.route("/list_taxa/simp/<int:id_area>", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_taxa_simple_list(id_area: int) -> Response:
    """

    :param type:
    :return:
    """

    try:
        query_area = (
            DB.session.query(
                Taxref.cd_ref.label("id"),
                Taxref.cd_ref,
                func.split_part(Taxref.nom_vern, ",", 1).label("nom_vern"),
                Taxref.lb_nom,
                Taxref.group2_inpn,
                func.coalesce(TMaxThreatenedStatus.threatened, False).label(
                    "threatened"
                ),
                func.count(distinct(Synthese.id_synthese)).label(
                    "count_occtax"
                ),
                func.count(distinct(Synthese.observers)).label(
                    "count_observer"
                ),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label(
                    "count_dataset"
                ),
                func.max(
                    distinct(func.extract("year", Synthese.date_min))
                ).label("last_year"),
            )
            .select_from(Taxref)
            .join(Synthese, Synthese.cd_nom == Taxref.cd_nom)
            .join(
                CorAreaSynthese,
                Synthese.id_synthese == CorAreaSynthese.id_synthese,
            )
            .outerjoin(
                TMaxThreatenedStatus,
                TMaxThreatenedStatus.cd_nom == Taxref.cd_nom,
            )
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .distinct()
            .group_by(
                func.coalesce(TMaxThreatenedStatus.threatened, False),
                Taxref.cd_ref,
                Taxref.nom_vern,
                Taxref.lb_nom,
                Taxref.group1_inpn,
                Taxref.group2_inpn,
            )
            .order_by(
                func.coalesce(TMaxThreatenedStatus.threatened, False).desc(),
                func.count(distinct(Synthese.id_synthese)).desc(),
                Taxref.group1_inpn,
                Taxref.group2_inpn,
            )
        )
        if not is_secured_area(id_area):
            query_area = query_area.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )
        result = query_area.all()
        data = []
        for r in result:
            data.append(r._asdict())
        DB.session.commit()
        return jsonify({"count": len(result), "data": data}), 200

    except Exception as e:
        current_app.logger.error(f"<get_taxa_list> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/statut/taxa/<int:cd_nom>/redlist", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_redlist_taxa_status(cd_nom: int) -> Response:
    """

    :param type:
    :return:
    """
    try:
        return jsonify(get_redlist_status(cd_nom))

    except Exception as e:
        current_app.logger.error(f"<get_redlist_taxa_status> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/charts/synthesis/<string:time_interval>/<int:id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def get_data_over_year(id_area: int, time_interval: str = "year") -> Response:
    """

    :param id_area:
    :return:
    """
    try:
        query = (
            DB.session.query(
                func.extract(time_interval, Synthese.date_min).label("label"),
                func.count(distinct(Synthese.id_synthese)).label(
                    "count_occtax"
                ),
                func.count(distinct(Synthese.cd_nom)).label("count_taxa"),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label(
                    "count_dataset"
                ),
            )
            .filter(Synthese.id_synthese == CorAreaSynthese.id_synthese)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .group_by(func.extract(time_interval, Synthese.date_min))
            .order_by(func.extract(time_interval, Synthese.date_min))
        )
        if not is_secured_area(id_area):
            query = query.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )
        results = query.all()
        DB.session.commit()
        return jsonify([row._asdict() for row in results])

    except Exception as e:
        current_app.logger.error(f"<get_data_over_year> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/charts/synthesis/taxogroup/<int:id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def get_data_over_taxogroup(id_area: int) -> Response:
    """[summary]

    Args:
        id_area (int): [description]

    Returns:
        Response: [description]
    """
    try:
        query = (
            DB.session.query(
                Taxref.group2_inpn.label("label"),
                func.count(distinct(Synthese.id_synthese)).label(
                    "count_occtax"
                ),
                func.count(distinct(Synthese.cd_nom)).label("count_taxa"),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label(
                    "count_dataset"
                ),
            )
            .filter(Synthese.id_synthese == CorAreaSynthese.id_synthese)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .group_by(
                Taxref.group2_inpn,
            )
            .order_by(
                Taxref.group2_inpn,
            )
        )
        if not is_secured_area(id_area):
            query = query.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )
        results = query.all()
        DB.session.commit()
        return jsonify([row._asdict() for row in results])

    except Exception as e:
        current_app.logger.error(f"<get_data_over_taxogroup> ERROR: {e}")
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()


@api.route("/charts/synthesis/group2_inpn_species/<int:id_area>/<int:buffer>")
@api.route("/charts/synthesis/group2_inpn_species/<int:id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def get_surrounding_count_species_by_group2inpn(
    id_area: int, buffer: int = 10000
) -> Response:
    """

    :param id_area:
    :return:
    """
    try:
        query_surrounding_territory = (
            DB.session.query(
                Taxref.group2_inpn,
                funcfilter(
                    func.count(distinct(Taxref.cd_ref)),
                    TMaxThreatenedStatus.threatened.is_(True),
                ).label("threatened"),
                funcfilter(
                    func.count(distinct(Taxref.cd_ref)),
                    TMaxThreatenedStatus.threatened.isnot(True),
                ).label("not_threatened"),
            )
            .distinct()
            .filter(LAreas.id_area == id_area, LAreas.enable)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .filter(Synthese.the_geom_local.ST_DWithin(LAreas.geom, buffer))
            .outerjoin(
                TMaxThreatenedStatus,
                TMaxThreatenedStatus.cd_nom == Taxref.cd_ref,
            )
            .group_by(Taxref.group2_inpn)
            .order_by(Taxref.group2_inpn)
        )

        if not is_secured_area(id_area):
            query_surrounding_territory = query_surrounding_territory.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )

        surrounding_territory_data = query_surrounding_territory.all()

        query_territory = (
            DB.session.query(
                Taxref.group2_inpn,
                funcfilter(
                    func.count(distinct(Taxref.cd_ref)),
                    TMaxThreatenedStatus.threatened.is_(True),
                ).label("threatened"),
                funcfilter(
                    func.count(distinct(Taxref.cd_ref)),
                    TMaxThreatenedStatus.threatened.isnot(True),
                ).label("not_threatened"),
            )
            .distinct()
            .filter(LAreas.id_area == id_area, LAreas.enable)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(
                Synthese.id_nomenclature_observation_status != absent_id,
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref, Taxref.id_rang == "ES")
            .filter(CorAreaSynthese.id_synthese == Synthese.id_synthese)
            .filter(CorAreaSynthese.id_area == LAreas.id_area)
            .outerjoin(
                TMaxThreatenedStatus,
                TMaxThreatenedStatus.cd_nom == Taxref.cd_ref,
            )
            .group_by(Taxref.group2_inpn)
            .order_by(Taxref.group2_inpn)
        )
        if not is_secured_area(id_area):
            query_territory = query_territory.filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id,
                Synthese.id_nomenclature_sensitivity == sensitivity_id,
            )

        territory_data = query_territory.all()
        taxo_groups = list(
            set(g.group2_inpn for g in surrounding_territory_data)
        )
        taxo_groups.sort()

        response = {}
        response["labels"] = taxo_groups
        response["surrounding"] = {
            "not_threatened": [],
            "threatened": [],
        }
        response["territory"] = {
            "not_threatened": [],
            "threatened": [],
        }
        for t in taxo_groups:
            for r in surrounding_territory_data:
                if r.group2_inpn == t:
                    response["surrounding"]["threatened"].append(r.threatened)
                    response["surrounding"]["not_threatened"].append(
                        r.not_threatened
                    )
            for r in territory_data:
                if r.group2_inpn == t:
                    response["territory"]["threatened"].append(r.threatened)
                    response["territory"]["not_threatened"].append(
                        r.not_threatened
                    )
        DB.session.commit()
        return (
            jsonify(response),
            200,
        )
    except Exception as e:
        current_app.logger.error(
            f"<get_surrounding_count_species_by_group2inpn> ERROR: {e}"
        )
        return {"Error": str(e)}, 400
    finally:
        DB.session.close()
