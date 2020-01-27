# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.dialects.postgresql import ARRAY
from utils_flask_sqla.serializers import serializable

from app import db, admin


@serializable
class BibDatasTypes(db.Model):
    __tablename__ = "bib_datas_types"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_protocol = Column(String)
    type_desc = Column(String)


@serializable
class TReleasedDatas(db.Model):
    __tablename__ = "t_released_datas"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_data_release = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("gn_biodivterritory.bib_datas_types.id_type"))
    data_name = Column(String)
    data_type = relationship(BibDatasTypes, lazy="select")
    data_desc = Column(Text)

    def __str__():
        return self.data_name


@serializable
class VListTaxa(db.Model):
    __tablename__ = "v_list_taxa"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id = db.Column(Integer, primary_key=True)
    id_area = db.Column(Integer, ForeignKey("ref_geo.l_areas.id_area"))
    area_code = db.Column(String)
    cd_ref = db.Column(Integer, ForeignKey("taxonomie.taxref.cd_nom"))
    nom_vern = db.Column(String)
    nom_valide = db.Column(String)
    group1_inpn = db.Column(String)
    group2_inpn = db.Column(String)
    count_occtax = db.Column(Integer)
    count_date = db.Column(Integer)
    count_observer = db.Column(Integer)
    count_dataset = db.Column(Integer)
    reproduction = db.Column(Boolean)
    statuts_bio = db.Column(ARRAY(String))
    threatened = db.Column(Boolean)
    protected = db.Column(Boolean)


admin.add_view(ModelView(BibDatasTypes, db.session))
admin.add_view(ModelView(TReleasedDatas, db.session))
