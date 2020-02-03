from flask import Blueprint, redirect, render_template, url_for, flash
from sqlalchemy import and_

import config
from app.core.env import DB
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.dynamic_content import TDynamicPages, BibDynamicPagesCategory
from app.models.ref_geo import BibAreasTypes, LAreas
from app.models.territory import MVTerritoryGeneralStats, MVAreaNtileLimit

rendered = Blueprint("rendered", __name__)


def get_legend_classes(type):
    query = MVAreaNtileLimit.query.filter_by(type=type).order_by(MVAreaNtileLimit.ntile)
    ntiles = query.all()
    datas = []
    for r in ntiles:
        datas.append(r.as_dict())
    return datas


@rendered.context_processor
def global_variables():
    values = {}
    values["site_name"] = config.SITE_NAME
    values["site_desc"] = config.SITE_DESC
    values["default_grid"] = config.DEFAULT_GRID
    values["default_buffer"] = config.DEFAULT_BUFFER
    values["special_pages"] = (
        DB.session.query(TDynamicPages.link_name, TDynamicPages.url)
        .filter(TDynamicPages.is_active == True)
        .filter(TDynamicPages.url != None)
        .all()
    )
    values["dynamic_pages"] = (
        DB.session.query(TDynamicPages.link_name, TDynamicPages.id_page)
        .filter(TDynamicPages.is_active == True)
        .join(
            BibDynamicPagesCategory,
            BibDynamicPagesCategory.id_category == TDynamicPages.id_category,
        )
        .all()
    )
    return values


@rendered.route("/")
def index():
    return render_template("home.html", name=config.SITE_NAME)


@rendered.route("/<string:url>")
def special_pages(url):
    """

    :return:
    """
    page = TDynamicPages.query.filter(TDynamicPages.url == url).one()
    return render_template("dynamic_page.html", page=page)


@rendered.route("/datas")
def datas():
    qdatas = DB.session.query(
        BibDatasTypes.type_desc,
        BibDatasTypes.type_name,
        BibDatasTypes.type_protocol,
        TReleasedDatas.data_desc,
        TReleasedDatas.data_name,
        TReleasedDatas.data_type,
        TReleasedDatas.data_url,
    ).join(
        TReleasedDatas, TReleasedDatas.id_type == BibDatasTypes.id_type, isouter=True
    )
    datas = qdatas.all()
    return render_template("datas.html", datas=datas)


@rendered.route("/territory/<type_code>/<area_code>")
def territory(type_code, area_code):
    """
    """
    try:
        q_area_info = (
            DB.session.query(
                BibAreasTypes.type_code,
                BibAreasTypes.type_name,
                BibAreasTypes.type_desc,
                LAreas.id_area,
                LAreas.area_name,
                LAreas.area_code,
            )
            .join(LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True)
            .filter(
                and_(BibAreasTypes.type_code == type_code.upper()),
                LAreas.area_code == area_code,
            )
        )
        area_info = q_area_info.one()

        # Retrieve general stats
        q_gen_stats = DB.session.query(MVTerritoryGeneralStats).filter(
            MVTerritoryGeneralStats.id_area == area_info.id_area
        )
        gen_stats = q_gen_stats.one()

        # generate Legend Dict
        legend_dict = {}
        for type in DB.session.query(MVAreaNtileLimit.type).distinct():
            legend_dict[type[0]] = get_legend_classes(type)
        print("legend_dict", legend_dict)
        print(gen_stats)
        return render_template(
            "territory/_main.html",
            area_info=area_info,
            gen_stats=gen_stats,
            legend_dict=legend_dict,
        )
    except Exception as e:
        flash("Aucune donnée pour ce territoire")
        print("<territory> ERROR: ", e)
        return redirect(url_for("rendered.index"))
