from flask import render_template, redirect, abort
from sqlalchemy import and_
import config
from flask import jsonify
from app.models.ref_geo import BibAreasTypes, LAreas
from app import db

from flask import Blueprint

api = Blueprint("api", __name__)


@api.route("/<type_code>/<area_code>")
def main_area_info(type_code, area_code):
    """
    
    """
    qterritory = (
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
    result = qterritory.one()
    data = result._asdict()
    return jsonify(data)
