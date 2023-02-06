from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from sqlalchemy import and_

from app.core.env import DB
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.dynamic_content import BibDynamicPagesCategory, TDynamicPages
from app.models.ref_geo import BibAreasTypes, LAreas
from app.models.territory import MVAreaNtileLimit, MVTerritoryGeneralStats

rendered = Blueprint("rendered", __name__)


def get_legend_classes(type: str):
    try:
        query = MVAreaNtileLimit.query.filter_by(type=type).order_by(
            MVAreaNtileLimit.ntile
        )
        ntiles = query.all()
        datas = []
        for r in ntiles:
            datas.append(r.as_dict())
        return datas
    except Exception as e:
        current_app.logger.error(f"<get_legend_classes> ERROR {e}")


@rendered.context_processor
# @cache.cached(timeout=600)
def global_variables():
    values = {}
    values["debug"] = current_app.config["DEBUG"]
    values["site_name"] = current_app.config["SITE_NAME"]
    values["site_desc"] = current_app.config["SITE_DESC"]
    values["default_grid"] = current_app.config["DEFAULT_GRID"]
    values["default_buffer"] = current_app.config["DEFAULT_BUFFER"]
    values["taxa_link_url_template"] = current_app.config[
        "TAXA_LINK_URL_TEMPLATE"
    ]
    # values["base_layers"] = config.BASE_LAYERS
    values["taxhub_url"] = current_app.config["TAXHUB_URL"]
    values["special_pages"] = (
        DB.session.query(TDynamicPages.link_name, TDynamicPages.url)
        .filter(TDynamicPages.is_active.is_(True))
        .filter(TDynamicPages.navbar_link.is_(True))
        .filter(TDynamicPages.url.isnot(None))
        .order_by(TDynamicPages.navbar_link_order.asc())
        .all()
    )
    values["footer"] = (
        DB.session.query(TDynamicPages.content)
        .filter(TDynamicPages.is_active.is_(False))
        .filter(TDynamicPages.navbar_link.is_(False))
        .filter(TDynamicPages.url == "footer")
        .one()
    ).content

    categories = (
        DB.session.query(
            BibDynamicPagesCategory.category_name,
            BibDynamicPagesCategory.category_desc,
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
    DB.session.commit()
    return values


@rendered.route("/")
# @cache.cached(timeout=600)
def index() -> str:
    home_desc = (
        DB.session.query(
            TDynamicPages.title,
            TDynamicPages.short_desc,
            TDynamicPages.content,
        )
        .filter(TDynamicPages.url == "home_desc")
        .first()
    )
    financial_partners = (
        DB.session.query(
            TDynamicPages.title,
            TDynamicPages.short_desc,
            TDynamicPages.content,
        )
        .filter(TDynamicPages.url == "financial_partners")
        .first()
    )

    technical_partners = (
        DB.session.query(
            TDynamicPages.title,
            TDynamicPages.short_desc,
            TDynamicPages.content,
        )
        .filter(TDynamicPages.url == "technical_partners")
        .first()
    )
    DB.session.commit()
    return render_template(
        "home.html",
        name=current_app.config["SITE_NAME"],
        home_desc=home_desc,
        financial_partners=financial_partners,
        technical_partners=technical_partners,
    )


@rendered.route("/page/<string:url>")
def special_pages(url: str) -> str:
    """

    :return:
    """
    page = TDynamicPages.query.filter(TDynamicPages.url == url).first()
    return render_template("dynamic_page.html", page=page)


@rendered.route("/datas")
def datas() -> str:
    qdatas = DB.session.query(
        BibDatasTypes.type_desc,
        BibDatasTypes.type_name,
        BibDatasTypes.type_protocol,
        TReleasedDatas.data_desc,
        TReleasedDatas.data_name,
        TReleasedDatas.data_type,
        TReleasedDatas.data_url,
    ).join(
        BibDatasTypes,
        TReleasedDatas.id_type == BibDatasTypes.id_type,
        isouter=True,
    )
    datas = qdatas.all()
    intro = (
        DB.session.query(
            TDynamicPages.title,
            TDynamicPages.short_desc,
            TDynamicPages.content,
        )
        .filter(TDynamicPages.url == "datas-intro")
        .first()
    )
    DB.session.commit()
    return render_template("datas.html", datas=datas, intro=intro)


@rendered.route("/territory/<string:type_code>/<string:area_code>")
def territory(type_code: str, area_code: str) -> str:
    """"""
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
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
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
                TDynamicPages.title,
                TDynamicPages.short_desc,
                TDynamicPages.content,
            )
            .filter(TDynamicPages.url == "territory-intro")
            .first()
        )
        DB.session.commit()
        return render_template(
            "territory/_main.html",
            area_info=area_info,
            gen_stats=gen_stats,
            legend_dict=legend_dict,
            intro=intro,
        )

    except Exception as e:
        flash("Erreur: {}".format(e))
        current_app.logger.error(f"<territory> ERROR: {str(e)}")
        return redirect(url_for("rendered.index"))


@rendered.route("/embed/territory/<string:type_code>/<string:area_code>")
def embed_territory(type_code: str, area_code: str) -> str:
    """"""
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
            .join(
                LAreas, LAreas.id_type == BibAreasTypes.id_type, isouter=True
            )
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
                TDynamicPages.title,
                TDynamicPages.short_desc,
                TDynamicPages.content,
            )
            .filter(TDynamicPages.url == "territory-intro")
            .first()
        )
        DB.session.commit()
        return render_template(
            "territory/_embed_main.html",
            area_info=area_info,
            gen_stats=gen_stats,
            legend_dict=legend_dict,
            intro=intro,
        )

    except Exception as e:
        flash("Erreur: {}".format(e))
        current_app.logger.error(f"<territory> ERROR: {str(e)}")
        return redirect(url_for("rendered.index"))
