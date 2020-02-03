# coding: utf-8
from flask import current_app
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from utils_flask_sqla.serializers import serializable

from app import admin
from app.core.env import DB


@serializable
class BibDatasTypes(DB.Model):
    __tablename__ = "bib_datas_types"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}

    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_protocol = Column(String)
    type_desc = Column(String)


@serializable
class TReleasedDatas(DB.Model):
    __tablename__ = "t_released_datas"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}

    id_data_release = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("gn_biodivterritory.bib_datas_types.id_type"))
    data_name = Column(String)
    data_desc = Column(Text)
    data_url = Column(String)
    data_type = relationship(BibDatasTypes, lazy="select")

    def __repr__(self):
        return self.data_name


admin.add_view(
    ModelView(BibDatasTypes, DB.session, category="Données", name="Types de données")
)
admin.add_view(
    ModelView(TReleasedDatas, DB.session, category="Données", name="Données")
)
