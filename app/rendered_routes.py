from flask import Blueprint, abort, redirect, render_template
from sqlalchemy import and_

import config
from app import db
from app.models.ref_geo import BibAreasTypes, LAreas

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


@rendered.route("/territory/<type_code>/<area_code>")
def territory(type_code, area_code):
    """
    
   """
    qterritory = (
        db.session.query(
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
    result = qterritory.one()
    return render_template("territory.html", area_info=result)


@rendered.route("/proxy/<user>")
def proxy_test(user):
    return render_template("proxy.html", name=user)
