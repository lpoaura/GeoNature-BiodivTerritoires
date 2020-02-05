from flask import Blueprint, jsonify, redirect, url_for, request, current_app
from geoalchemy2.shape import to_shape
from geojson import Feature, FeatureCollection
from pypnnomenclature.models import TNomenclatures, BibNomenclaturesTypes
from sqlalchemy import and_, or_, distinct
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.sql import func, case, funcfilter

from app.core.env import DB
from app.core.utils import (
    get_nomenclature,
    get_redlist_status,
    redlist_is_not_null,
    redlist_list_is_null,
)
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.ref_geo import (
    BibAreasTypes,
    LAreas,
    MVLAreasAutocomplete,
    LAreasTypeSelection,
)
from app.models.synthese import Synthese, CorAreaSynthese
from app.models.taxonomy import (
    Taxref,
    TaxrefLR,
    TaxrefProtectionEspeces,
    TMaxThreatenedStatus,
)
from app.models.territory import MVTerritoryGeneralStats, MVAreaNtileLimit

api = Blueprint("api", __name__)


@api.route("/find/area")
def find_area():
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
            .limit(20)
        )
        print(qarea)
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
def redirect_area(id_area):
    """
    redirect tu human readable territory url based on type_code and area_code from id_area, for select2 searches
    :param id_area:
    :return:
    """
    try:
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
    except Exception as e:
        current_app.logger.error("<redirect_area> ERROR:", e)


@api.route("/homestats")
def home_stats():
    """

    :return:
    """
    try:
        query = DB.session.query(
            func.count(distinct(Synthese.id_dataset)).label("count_dataset"),
            func.count(Synthese.id_synthese).label("count_occtax"),
            func.count(distinct(Synthese.cd_nom)).label("count_taxa"),
            func.count(distinct(Synthese.observers)).label("count_observers"),
        )
        result = query.one()
        return jsonify(result._asdict())
    except Exception as e:
        current_app.logger.error("<main_area_info> ERROR:", e)
        return {"Error": str(e)}, 400


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
        current_app.logger.error("<main_area_info> ERROR:", e)
        return {"Error": str(e)}, 400


@api.route("/surrounding_areas/<string:type_code>/<string:area_code>")
@api.route("/surrounding_areas/<string:type_code>/<string:area_code>/<int:buffer>")
def get_surrounding_area(type_code, area_code, buffer=10000):
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
            BibAreasTypes, BibAreasTypes.type_code == MVTerritoryGeneralStats.type_code
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
        current_app.logger.error("<datas_types> ERROR:", e)
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
        feature = Feature(geometry=to_shape(result.geom))
        feature["properties"]["area_name"] = result.area_name
        feature["properties"]["area_code"] = result.area_code
        return feature
    except Exception as e:
        current_app.logger.error("<get_geojson_area> ERROR:", e)
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
        datas = qgrid.all()
        features = []
        for d in datas:
            features.append(d.as_geofeature("geom_4326", "id_area"))
        return FeatureCollection(features)
    except Exception as e:
        current_app.logger.error("<get_grid_datas> ERROR:", e)
        return {"Error": str(e)}, 400


@api.route("/territory/conf/ntile/", methods=["GET"])
def get_ntile():
    """

    :param type:
    :return:
    """
    try:
        query = MVAreaNtileLimit.query.order_by(MVAreaNtileLimit.type).order_by(
            MVAreaNtileLimit.ntile
        )
        ntiles = query.all()
        datas = []
        for r in ntiles:
            datas.append(r.as_dict())
        return jsonify(datas)
    except Exception as e:
        current_app.logger.error("<get_ntile> ERROR:", e)
        return {"Error": str(e)}, 400


@api.route("/list_taxa/<int:id_area>", methods=["GET"])
def get_taxa_list(id_area):
    """

    :param type:
    :return:
    """
    try:
        reproduction_id = (
            (
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
            )
            .first()
            .id_nomenclature
        )
        print("reproduction_id", reproduction_id)
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
                func.array_agg(distinct(Synthese.id_nomenclature_bio_status)).label(
                    "bio_status_id"
                ),
                case(
                    [(func.count(TaxrefProtectionEspeces.cd_nom) > 0, True)],
                    else_=False,
                ).label("protection"),
            )
            .select_from(CorAreaSynthese)
            .join(Synthese, Synthese.id_synthese == CorAreaSynthese.id_synthese)
            .join(Taxref, Synthese.cd_nom == Taxref.cd_nom)
            .join(LAreas, LAreas.id_area == CorAreaSynthese.id_area)
            .outerjoin(TaxrefLR, TaxrefLR.cd_nom == Taxref.cd_ref)
            .outerjoin(
                TaxrefProtectionEspeces, TaxrefProtectionEspeces.cd_nom == Taxref.cd_nom
            )
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
            .order_by(
                func.count(distinct(Synthese.id_synthese)).desc(),
                Taxref.group1_inpn,
                Taxref.group2_inpn,
                Taxref.nom_valide,
            )
        )
        print("query_territory", query_territory)
        result = query_territory.all()
        count = len(result)
        data = []
        for r in result:
            dict = r._asdict()
            bio_status = []
            for s in r.bio_status_id:
                bio_status.append(get_nomenclature(s))
                dict["bio_status"] = bio_status
            redlist = get_redlist_status(r.cd_ref)
            dict["redlist"] = redlist
            data.append(dict)

        redlistless_data = list(filter(redlist_list_is_null, data))
        print("redlistless_data", len(redlistless_data))
        redlist_data = list(filter(redlist_is_not_null, data))
        print("redlist_data", len(redlist_data))
        redlist_sorted_data = sorted(
            redlist_data,
            key=lambda k: (
                k["redlist"][0]["priority_order"],
                k["redlist"][0]["threatened"],
            ),
        )
        sorted_data = redlist_sorted_data + list(redlistless_data)
        return jsonify({"count": count, "data": sorted_data}), 200

    except Exception as e:
        error = "<get_taxa_list> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


@api.route("/statut/taxa/<int:cd_nom>/redlist", methods=["GET"])
def get_redlist_taxa_status(cd_nom):
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


#
# @api.route("/charts/synthesis/spatial/<int:id_area>")
# def get_territory_spatial_synthesis(id_area):
#     """
#
#     :param id_area:
#     :return:
#     """
#     pass
from sqlalchemy.orm import aliased


@api.route("/charts/synthesis/yearly/<int:id_area>")
def get_data_over_year(id_area):
    """

    :param id_area:
    :return:
    """
    try:
        query = (
            DB.session.query(
                func.extract("year", Synthese.date_min).label("year"),
                Taxref.group2_inpn,
                func.count(distinct(Synthese.id_synthese)).label("count_occtax"),
                func.count(distinct(Synthese.date_min)).label("count_date"),
                func.count(distinct(Synthese.id_dataset)).label("count_dataset"),
            )
            .filter(Synthese.id_synthese == CorAreaSynthese.id_synthese)
            .filter(Synthese.cd_nom == Taxref.cd_nom)
            .filter(CorAreaSynthese.id_area == id_area)
            .group_by(func.extract("year", Synthese.date_min), Taxref.group2_inpn,)
            .order_by(func.extract("year", Synthese.date_min), Taxref.group2_inpn,)
        )

        results = query.all()
        taxo_groups = list(set(r.group2_inpn for r in results)).sort()
        years = list(set(r.year for r in results)).sort()
        datasets = []
        for t in taxo_groups:
            label_dataset = {}
            label_dataset["label"] = t
            datasets.append(label_dataset)
        for y in years:
            for r in results:
                for d in datasets:
                    d["countocctax"] = []
                    if d["label"] == r.group2_inpn:
                        d["countocctax"].append(r.count_occtax)

        # labels = years
        # print(years, taxo_groups)
        # datasets = []
        # datasets[0].label
        # years = []
        # for r in results:
        #     if r.year in years:
        #         if r.group2_inpn in taxo_groups:
        #             data
        #     years.append(r.year)
        # print("YEARS", years)
        # years = list(set(years))
        # years.sort()
        # for year in years:
        #     print(year)
        #     dataset = {}
        #     for r in results:
        #         print(r)
        #         print(r.year == year)
        #         if r.year == year:
        #             print()
        #             dataset[r.group2_inpn] = []
        #             dataset[r.group2_inpn].append(r.count_occtax)
        #     data.append(dataset)
        #
        # print(data)
        return jsonify(datasets)

    except Exception as e:
        error = "<get_data_over_year> ERROR: {}".format(e)
        current_app.logger.error(error)
        return {"Error": error}, 400


@api.route("/charts/synthesis/group2_inpn_species/<int:id_area>/<int:buffer>")
@api.route("/charts/synthesis/group2_inpn_species/<int:id_area>")
def get_surrounding_count_species_by_group2inpn(id_area, buffer=10000):
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
                TMaxThreatenedStatus.threatened == False,
            ).label("not_threatened"),
        )
        .distinct()
        .filter(LAreas.id_area == id_area)
        .filter(Synthese.cd_nom == Taxref.cd_nom)
        .filter(Synthese.the_geom_local.ST_DWithin(LAreas.geom, buffer))
        .outerjoin(TMaxThreatenedStatus, TMaxThreatenedStatus.cd_nom == Taxref.cd_ref)
        .group_by(Taxref.group2_inpn)
        .order_by(Taxref.group2_inpn)
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
                TMaxThreatenedStatus.threatened == False,
            ).label("not_threatened"),
        )
        .distinct()
        .filter(LAreas.id_area == id_area)
        .filter(Synthese.cd_nom == Taxref.cd_nom)
        .filter(CorAreaSynthese.id_synthese == Synthese.id_synthese)
        .filter(CorAreaSynthese.id_area == LAreas.id_area)
        .outerjoin(TMaxThreatenedStatus, TMaxThreatenedStatus.cd_nom == Taxref.cd_ref)
        .group_by(Taxref.group2_inpn)
        .order_by(Taxref.group2_inpn)
    )

    territory_data = query_territory.all()

    print(surrounding_territory_data)
    print(territory_data)

    taxo_groups = list(set(g.group2_inpn for g in surrounding_territory_data))
    taxo_groups.sort()
    print(taxo_groups)
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
                response["surrounding"]["not_threatened"].append(r.not_threatened)
        for r in territory_data:
            if r.group2_inpn == t:
                response["territory"]["threatened"].append(r.threatened)
                response["territory"]["not_threatened"].append(r.not_threatened)

    return (
        jsonify(response),
        200,
    )
