# coding: utf-8
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app import db


class BibDatasTypes(db.Model):
    __tablename__ = "bib_datas_types"
    __table_args__ = {"schema": "gn_biodiv_territory"}
    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_protocol = Column(String)
    type_desc = Column(String)


class TReleasedDatas(db.Model):
    __tablename__ = "t_released_datas"
    __table_args__ = {"schema": "gn_biodiv_territory"}
    id_data_release = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("gn_biodivterritory.bib_datas_types.id_type"))
    data_name = Column(String)
    data_type = relationship(BibDatasTypes, lazy="select")
    data_desc = Column(Text)
