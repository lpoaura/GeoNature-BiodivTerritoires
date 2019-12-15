# coding: utf-8
from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import config
from app import db


class BibDatasTypes(db.Model):
    __tablename__ = "bib_datas_types"
    __table_args__ = {"schema": "gn_biodivterritory"}
    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_protocol = Column(String)
    type_desc = Column(String)

class TReleasedDatas(db.Model):
    __tablename__ = "t_released_datas"
    __table_args__ = {"schema": "gn_biodivterritory"}
    id_data_release = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("gn_biodivterritory.bib_datas_types.id_type"))
    data_name = Column(String)
    data_type = relationship(BibDatasTypes, lazy="select")
    data_desc = Column(Text)
    
