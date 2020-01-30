# coding: utf-8
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
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_protocol = Column(String)
    type_desc = Column(String)


@serializable
class TReleasedDatas(DB.Model):
    __tablename__ = "t_released_datas"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_data_release = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("gn_biodivterritory.bib_datas_types.id_type"))
    data_name = Column(String)
    data_type = relationship(BibDatasTypes, lazy="select")
    data_desc = Column(Text)

    def __str__():
        return self.data_name


admin.add_view(ModelView(BibDatasTypes, DB.session))
admin.add_view(ModelView(TReleasedDatas, DB.session))
