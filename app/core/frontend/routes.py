from flask import Blueprint, redirect, render_template, url_for, flash
from sqlalchemy import and_, not_
from sqlalchemy.sql import func, case

import config
from app.core.env import DB
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.dynamic_content import TDynamicPages, BibDynamicPagesCategory
from app.models.ref_geo import BibAreasTypes, LAreas, LAreasTypeSelection
from app.models.territory import MVTerritoryGeneralStats, MVAreaNtileLimit
import re

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
        .filter(TDynamicPages.navbar_link == True)
        .filter(TDynamicPages.url != None)
        .order_by(TDynamicPages.navbar_link_order.asc())
        .all()
    )

    categories = (
        DB.session.query(
            BibDynamicPagesCategory.category_name, BibDynamicPagesCategory.category_desc
        )
        .join(
            TDynamicPages,
            TDynamicPages.id_category == BibDynamicPagesCategory.id_category,
        )
        .all()
    )

    dynamic_pages = []
    for c in categories:
        c_content = c._asdict()
        c_content["pages"] = []
        pages = (
            DB.session.query(
                TDynamicPages.link_name,
                TDynamicPages.id_category,
                TDynamicPages.link_name,
            )
            .filter(TDynamicPages.id_category == c.id_category)
            .all()
        )
        for p in pages:
            c_content["pages"].append(p._asdict())

    values["dynamic_pages"] = dynamic_pages
    return values


@rendered.route("/")
def index():
    bonus_block = (
        DB.session.query(
            TDynamicPages.title, TDynamicPages.short_desc, TDynamicPages.content
        )
        .filter(TDynamicPages.url == "home-bonus")
        .first()
    )

    print("bonus", bonus_block)
    # re_grid_codes = r"M(\d+)"

    return render_template("home.html", name=config.SITE_NAME, bonus_block=bonus_block)


@rendered.route("/<string:url>")
def special_pages(url):
    """

    :return:
    """
    page = TDynamicPages.query.filter(TDynamicPages.url == url).first()
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
    ).join(BibDatasTypes, TReleasedDatas.id_type == BibDatasTypes.id_type, isouter=True)
    datas = qdatas.all()
    intro = (
        DB.session.query(
            TDynamicPages.title, TDynamicPages.short_desc, TDynamicPages.content
        )
        .filter(TDynamicPages.url == "datas-intro")
        .first()
    )
    return render_template("datas.html", datas=datas, intro=intro)


@rendered.route("/territory/<string:type_code>/<string:area_code>")
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

        intro = (
            DB.session.query(
                TDynamicPages.title, TDynamicPages.short_desc, TDynamicPages.content
            )
            .filter(TDynamicPages.url == "territory-intro")
            .first()
        )

        return render_template(
            "territory/_main.html",
            area_info=area_info,
            gen_stats=gen_stats,
            legend_dict=legend_dict,
            intro=intro,
        )

    except Exception as e:
        flash("Erreur: {}".format(e))
        print("<territory> ERROR: ", e)
        return redirect(url_for("rendered.index"))
