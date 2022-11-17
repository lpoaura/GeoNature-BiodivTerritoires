from flask import current_app
from geoalchemy2 import Geometry
from sqlalchemy import Column, Date, Integer, String
from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from app.core.env import DB


@serializable
class MVGeneralStats(DB.Model):
    __tablename__ = "mv_general_stats"
    __table_args__ = {
        "schema": current_app.config["APP_SCHEMA_NAME"],
        "extend_existing": True,
    }
    id = Column(Integer, primary_key=True)
    count_occtax = Column(Integer)
    count_dataset = Column(Integer)
    count_observer = Column(Integer)
    count_taxa = Column(Integer)


@serializable
@geoserializable
class MVTerritoryGeneralStats(DB.Model):
    __tablename__ = "mv_territory_general_stats"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}
    id_area = Column(Integer, primary_key=True)
    type_code = Column(String, nullable=False)
    area_code = Column(String)
    area_name = Column(String)
    count_taxa = Column(Integer)
    count_occtax = Column(Integer)
    count_threatened = Column(Integer)
    count_dataset = Column(Integer)
    count_date = Column(Integer)
    count_observer = Column(Integer)
    last_obs = Column(Date)
    geom_local = Column(Geometry("GEOMETRY", current_app.config["LOCAL_SRID"]))
    geom_4326 = Column(Geometry("GEOMETRY", 4326))

    def __repr__(self):
        return "<MVTerritoryGeneralStats: id_area={id_area}, area_name={area_name}>".format(
            id_area=self.id_area, area_name=self.area_name
        )


@serializable
class MVAreaNtileLimit(DB.Model):
    __tablename__ = "mv_area_ntile_limit"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}
    id = Column(Integer, unique=True, primary_key=True)
    type = Column(String, nullable=False)
    min = Column(Integer, nullable=False)
    max = Column(Integer, nullable=False)
    ntile = Column(Integer, nullable=False)

    def __repr__(self):
        return "<MVAreaNtileLimit: id={id}>".format(id=self.id)
