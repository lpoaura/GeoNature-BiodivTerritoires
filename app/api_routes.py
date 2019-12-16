from flask import render_template, redirect, abort
from sqlalchemy import and_
import config
from flask import jsonify
from app.models.ref_geo import BibAreasTypes, LAreas
from app.models.datas import BibDatasTypes, TReleasedDatas
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



@api.route("/type")
def datas_types():
    """
    
    """
    qdatatype = (
        db.session.query(
            BibDatasTypes.type_protocol,
            BibDatasTypes.type_name,
            TReleasedDatas.data_name,
            TReleasedDatas.data_desc,
        )
        .join(TReleasedDatas,  BibDatasTypes.id_type == TReleasedDatas.id_type, isouter=True)
    )
    result = qdatatype.first()
    data = result._asdict()
    return jsonify(data)
