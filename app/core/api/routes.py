from flask import Blueprint, current_app, jsonify, redirect, request, url_for
from flask.wrappers import Response
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from pypnnomenclature.models import TNomenclatures
from sqlalchemy import and_, distinct, or_
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.sql import case, func, funcfilter

from app.core.env import DB, cache
from app.core.utils import get_nomenclature_id, get_redlist_status
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

# logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)

genStats = {}

diffusion_level_id = get_nomenclature_id("NIV_PRECIS", "5")

# CACHE_TIMEOUT = current_app.config["CACHE_TIMEOUT"]
CACHE_TIMEOUT = 600


@api.route("/find/area")
def find_area() -> Response:
    """

    :return:
    """
    try:
        search_name = "%{}%".format(request.args.get("q"))
        search_code = request.args.get("q")
        qarea = (
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
        current_app.logger.debug(qarea)
        result = qarea.all()
        count = len(result)
        datas = []
        for r in result:
            datas.append(r._asdict())
        return {"count": count, "datas": datas}, 200

    except Exception as e:
        current_app.logger.error("<find_area> ERROR:", e)
        return {"Error": str(e)}, 400


@api.route("/area/<id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def redirect_area(id_area: int) -> Response:
    """
    redirect tu human readable territory url based on type_code and area_code from id_area, for select2 searches
    :param id_area:
    :return:
    """
    try:
        qarea = (
            DB.session.query(
                BibAreasTypes.type_code,
                LAreas.area_code,
            )
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
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
    except Exception as e:
        current_app.logger.error("<redirect_area> ERROR:", e)


# @api.route("/homestats")
# def home_stats():
#     """
#
#     :return:
#     """
#     # result = genStats
#     try:
#     taxa = aliased(
#         (
#             DB.session.query(Synthese.cd_nom)
#             .distinct()
#             .cte(name="taxa", recursive=False)
#         ),
#         name="taxa_cte",
#     )
#     # taxa = DB.session.query(Synthese.cd_nom).distinct()
#     # occtax = aliased(
#     #     (
#     #         DB.session.query(Synthese.id_synthese)
#     #         .distinct()
#     #         .cte(name="occtax", recursive=False)
#     #     ),
#     #     name="occtax_cte",
#     # )
#     observers = aliased(
#         (
#             DB.session.query(Synthese.observers)
#             .distinct()
#             .cte(name="observers", recursive=False)
#         ),
#         name="observers_cte",
#     )
#     dataset = aliased(
#         (
#             DB.session.query(Synthese.id_dataset)
#             .distinct()
#             .cte(name="dataset", recursive=False)
#         ),
#         name="dataset_cte",
#     )
#     result["count_taxa"] = DB.session.query(func.count(taxa.c.cd_nom)).one()[0]
#     current_app.logger.debug("<CountObserversQuery> {}".format(observers))
#     current_app.logger.info(
#         "<homestats query> {}".format(DB.session.query(func.count(taxa.c.cd_nom)))
#     )
#     result["count_occtax"] = DB.session.query(
#         func.count(Synthese.id_synthese)
#     ).one()[0]
#     result["count_dataset"] = DB.session.query(
#         func.count(dataset.c.id_dataset)
#     ).one()[0]
#     result["count_observers"] = DB.session.query(
#         func.count(observers.c.observers)
#     ).one()[0]

# query = DB.session.query(
#     func.count(taxa.c.cd_nom).label("count_taxa"),
#     func.count(occtax.c.id_synthese).label("count_occtax"),
#     func.count(dataset.c.id_dataset).label("count_dataset"),
#     func.count(observers.c.observers).label("count_observers"),
# )
# current_app.logger.info("<homestat query>: {}".format(query))
# result = query.one()
# return jsonify(result._asdict())
#     return jsonify(genStats)
#
# except Exception as e:
#     current_app.logger.error("<main_area_info> ERROR: {}".format(e))
#     return {"Error": str(e)}, 400


@api.route("/homestats")
@cache.cached(timeout=CACHE_TIMEOUT)
def home_stats() -> Response:
    """Home page general stats

    Returns:
        json: General statistics
    """

    try:
        query = MVGeneralStats.query
        stats = query.one()
        current_app.logger.debug(
            f"<main_area_info> TYPE RESULT {type(jsonify(stats.as_dict()))}"
        )
        return jsonify(stats.as_dict())
    except Exception as e:
        current_app.logger.error("<home_stats> ERROR:", e)
        return {"Error": str(e)}, 400


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
        current_app.logger.debug(
            f"<main_area_info> TYPE RESULT {type(jsonify(data))}"
        )
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"<main_area_info> ERROR: {e}")
        return {"Error": str(e)}, 400


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

    area = (
        DB.session.query(LAreas.id_area, LAreas.geom).filter(
            LAreas.area_code == area_code, BibAreasTypes.type_code == type_code
        )
    ).first()

    selected_type_codes = DB.session.query(LAreasTypeSelection.id_type).all()
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
    return jsonify(data)


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
        return jsonify(data)
    except Exception as e:
        current_app.logger.error("<datas_types> ERROR:", e)
        return {"Error": str(e)}, 400


@api.route("/geom/<string:type_code>/<string:area_code>", methods=["GET"])
# def get_geojson_area(type_code: str, area_code: str) -> Response:
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
        return feature
    except Exception as e:
        current_app.logger.error("<get_geojson_area> ERROR:", e)
        return {"Error": str(e)}, 400


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
        current_app.logger.debug(f"<get_grid_datas> qarea QUERY {qarea}")
        area = qarea.one()
        qgrid = MVTerritoryGeneralStats.query.filter(
            MVTerritoryGeneralStats.type_code == grid
        ).filter(
            func.ST_Intersects(
                MVTerritoryGeneralStats.geom_local,
                func.ST_Buffer(area.geom, buffer),
            )
        )
        current_app.logger.debug(f"<get_grid_datas> qgrid QUERY {qgrid}")
        datas = qgrid.all()
        features = []
        for d in datas:
            features.append(d.as_geofeature("geom_4326", "id_area"))
        return FeatureCollection(features)
    except Exception as e:
        current_app.logger.error("<get_grid_datas> ERROR:", e)
        return {"Error": str(e)}, 400


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
            current_app.logger.debug(f"<get_ntile> r {r}")
            current_app.logger.debug(f"<get_ntile> r.as_dict() {r.as_dict()}")
            datas.append(r.as_dict())
        return jsonify(datas)
    except Exception as e:
        current_app.logger.error(f"<get_ntile> ERROR  {e}")
        return {"Error": str(e)}, 400


@api.route("/list_taxa/<int:id_area>", methods=["GET"])
@cache.cached(timeout=CACHE_TIMEOUT)
def get_taxa_list(id_area: int) -> Response:
    """

    :param type:
    :return:
    """
    try:
        reproduction_id = get_nomenclature_id("STATUT_BIO", "3")

        current_app.logger.debug(f"reproduction_id {reproduction_id}")
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
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref)
            .filter(Taxref.id_rang == "ES")
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
        current_app.logger.debug(f"query_territory {query_territory}")
        result = query_territory.all()
        count = len(result)
        data = []
        for r in result:
            dict = r._asdict()
            # bio_status = []
            # for s in r.bio_status_id:
            #     bio_status.append(get_nomenclature(s))
            #     dict["bio_status"] = bio_status
            # redlist = get_redlist_status(r.cd_ref)
            # dict["redlist"] = redlist
            data.append(dict)
        #
        # redlistless_data = list(filter(redlist_list_is_null, data))
        # print("redlistless_data", len(redlistless_data))
        # redlist_data = list(filter(redlist_is_not_null, data))
        # print("redlist_data", len(redlist_data))
        # redlist_sorted_data = sorted(
        #     redlist_data,
        #     key=lambda k: (
        #         k["redlist"][0]["priority_order"],
        #         k["redlist"][0]["threatened"],
        #     ),
        # )
        # sorted_data = redlist_sorted_data + list(redlistless_data)
        return jsonify({"count": count, "data": data}), 200

    except Exception as e:
        error = "<get_taxa_list> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


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
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref)
            .filter(Taxref.id_rang == "ES")
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
        current_app.logger.debug(f"query_territory {query_area}")
        result = query_area.all()
        data = []
        for r in result:
            data.append(r._asdict())

        return jsonify({"count": len(result), "data": data}), 200

    except Exception as e:
        error = "<get_taxa_list> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


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
        error = "<get_redlist_taxa_status> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


@api.route("/charts/synthesis/<string:timeinterval>/<int:id_area>")
@cache.cached(timeout=CACHE_TIMEOUT)
def get_data_over_year(id_area: int, timeinterval: str = "year") -> Response:
    """

    :param id_area:
    :return:
    """
    try:
        query = (
            DB.session.query(
                func.extract(timeinterval, Synthese.date_min).label("label"),
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
            .filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id
            )
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(Taxref.cd_nom == Taxref.cd_ref)
            .filter(Taxref.id_rang == "ES")
            .group_by(func.extract(timeinterval, Synthese.date_min))
            .order_by(func.extract(timeinterval, Synthese.date_min))
        )
        results = query.all()
        current_app.logger.debug(dir(results))
        current_app.logger.debug(type(results))
        return jsonify([dict(row) for row in results])

    except Exception as e:
        error = f"<get_data_over_year> ERROR: {e}"
        current_app.logger.error(error)
        return {"Error": error}, 400


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
            .filter(CorAreaSynthese.id_area == id_area)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(
                Synthese.id_nomenclature_diffusion_level == diffusion_level_id
            )
            .filter(Taxref.cd_nom == Taxref.cd_ref)
            .filter(Taxref.id_rang == "ES")
            .group_by(
                Taxref.group2_inpn,
            )
            .order_by(
                Taxref.group2_inpn,
            )
        )

        results = query.all()
        current_app.logger.debug(dir(results))
        return jsonify([dict(row) for row in results])

    except Exception as e:
        error = "<get_data_over_taxogroup> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


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
    query_surrounding_territory = (
        DB.session.query(
            Taxref.group2_inpn,
            funcfilter(
                func.count(distinct(Taxref.cd_ref)),
                TMaxThreatenedStatus.threatened == True,
            ).label("threatened"),
            funcfilter(
                func.count(distinct(Taxref.cd_ref)),
                TMaxThreatenedStatus.threatened.isnot(True),
            ).label("not_threatened"),
        )
        .distinct()
        .filter(LAreas.id_area == id_area)
        .filter(Synthese.cd_nom == Taxref.cd_nom)
        .filter(Synthese.id_nomenclature_diffusion_level == diffusion_level_id)
        .filter(Taxref.cd_nom == Taxref.cd_ref)
        .filter(Taxref.id_rang == "ES")
        .filter(Synthese.the_geom_local.ST_DWithin(LAreas.geom, buffer))
        .outerjoin(
            TMaxThreatenedStatus, TMaxThreatenedStatus.cd_nom == Taxref.cd_ref
        )
        .group_by(Taxref.group2_inpn)
        .order_by(Taxref.group2_inpn)
    )
    current_app.logger.debug(
        "<get_surrounding_count_species_by_group2inpn> query_surrounding_territory: {} ".format(
            query_surrounding_territory
        )
    )
    surrounding_territory_data = query_surrounding_territory.all()

    query_territory = (
        DB.session.query(
            Taxref.group2_inpn,
            funcfilter(
                func.count(distinct(Taxref.cd_ref)),
                TMaxThreatenedStatus.threatened == True,
            ).label("threatened"),
            funcfilter(
                func.count(distinct(Taxref.cd_ref)),
                TMaxThreatenedStatus.threatened.isnot(True),
            ).label("not_threatened"),
        )
        .distinct()
        .filter(LAreas.id_area == id_area)
        .filter(Synthese.cd_nom == Taxref.cd_nom)
        .filter(Synthese.id_nomenclature_diffusion_level == diffusion_level_id)
        .filter(Taxref.cd_nom == Taxref.cd_ref)
        .filter(Taxref.id_rang == "ES")
        .filter(CorAreaSynthese.id_synthese == Synthese.id_synthese)
        .filter(CorAreaSynthese.id_area == LAreas.id_area)
        .outerjoin(
            TMaxThreatenedStatus, TMaxThreatenedStatus.cd_nom == Taxref.cd_ref
        )
        .group_by(Taxref.group2_inpn)
        .order_by(Taxref.group2_inpn)
    )

    current_app.logger.debug(
        "<get_surrounding_count_species_by_group2inpn> query_territory: {} ".format(
            query_territory
        )
    )

    territory_data = query_territory.all()

    current_app.logger.debug(surrounding_territory_data)
    current_app.logger.debug(territory_data)

    taxo_groups = list(set(g.group2_inpn for g in surrounding_territory_data))
    taxo_groups.sort()
    current_app.logger.debug(taxo_groups)
    # result["territory"] = []

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

    return (
        jsonify(response),
        200,
    )
