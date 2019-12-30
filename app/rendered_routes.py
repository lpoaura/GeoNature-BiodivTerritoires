from flask import Blueprint, abort, redirect, render_template
from sqlalchemy import and_

import config
from app import db
from app.models.ref_geo import BibAreasTypes, LAreas
from app.models.datas import BibDatasTypes, TReleasedDatas
from app.models.territory import VMTerritoryGeneralStats

rendered = Blueprint("rendered", __name__)


@rendered.context_processor
def global_variables():
    values = {}
    values["site_name"] = config.SITE_NAME
    values["site_desc"] = config.SITE_DESC
    return values


@rendered.route("/")
def index():
    return render_template("home.html", name=config.SITE_NAME)


@rendered.route("/datas")
def datas():
    qdatas = db.session.query(
        BibDatasTypes.type_desc,
        BibDatasTypes.type_name,
        BibDatasTypes.type_protocol,
        TReleasedDatas.data_desc,
        TReleasedDatas.data_name,
        TReleasedDatas.data_type,
    ).join(
        TReleasedDatas, TReleasedDatas.id_type == BibDatasTypes.id_type, isouter=True
    )
    datas = qdatas.all()
    return render_template("datas.html", datas=datas)


@rendered.route("/territory/<type_code>/<area_code>")
def territory(type_code, area_code):
    """
    
   """
    q_area_info = (
        db.session.query(
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
    # q_gen_stats = db.session.query(VMTerritoryGeneralStats).filter(
    #     VMTerritoryGeneralStats.id_area == area_info.id_area
    # )
    # gen_stats = q_gen_stats.one()
    # print(gen_stats)
    return render_template("territory.html", area_info=area_info)


@rendered.route("/proxy/<user>")
def proxy_test(user):
    return render_template("proxy.html", name=user)
