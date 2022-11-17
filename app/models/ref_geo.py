# coding: utf-8
from flask import current_app
from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from utils_flask_sqla.serializers import serializable
from utils_flask_sqla_geo.serializers import geoserializable

from app import config
from app.core.env import DB


@serializable
class BibAreasTypes(DB.Model):
    __tablename__ = "bib_areas_types"
    __table_args__ = {"schema": "ref_geo", "extend_existing": True}
    id_type = Column(Integer, primary_key=True)
    type_name = Column(String)
    type_code = Column(String)
    type_desc = Column(String)
    ref_name = Column(String)
    ref_version = Column(String)
    num_version = Column(String)


@geoserializable
class LAreas(DB.Model):
    __tablename__ = "l_areas"
    __table_args__ = {"schema": "ref_geo"}
    id_area = Column(Integer, primary_key=True)
    id_type = Column(Integer, ForeignKey("ref_geo.bib_areas_types.id_type"))
    area_name = Column(String)
    area_code = Column(String)
    geom = Column(Geometry("GEOMETRY", current_app.config["LOCAL_SRID"]))
    source = Column(String)
    area_type = relationship(
        "BibAreasTypes",
        backref=DB.backref("ref_geo.bib_areas_types", lazy=True),
    )

    def get_geofeature(self, recursif=True, columns=None):
        return self.as_geofeature("geom", "id_area", recursif, columns=columns)


@serializable
class LiMunicipalities(DB.Model):
    __tablename__ = "li_municipalities"
    __table_args__ = {"schema": "ref_geo"}
    id_municipality = Column(Integer, primary_key=True)
    id_area = Column(Integer)
    status = Column(String)
    insee_com = Column(String)
    nom_com = Column(String)
    insee_arr = Column(String)
    nom_dep = Column(String)
    insee_dep = Column(String)
    nom_reg = Column(String)
    insee_reg = Column(String)
    code_epci = Column(String)
    plani_precision = Column(Float)
    siren_code = Column(String)
    canton = Column(String)
    population = Column(Integer)
    multican = Column(String)
    cc_nom = Column(String)
    cc_siren = Column(BigInteger)
    cc_nature = Column(String)
    cc_date_creation = Column(String)
    cc_date_effet = Column(String)
    insee_commune_nouvelle = Column(String)
    meta_create_date = Column(DateTime)
    meta_update_date = Column(DateTime)


@serializable
class MVLAreasAutocomplete(DB.Model):
    __tablename__ = "mv_l_areas_autocomplete"
    __table_args__ = {"schema": "gn_biodivterritory", "extend_existing": True}
    id = Column(Integer, primary_key=True)
    type_name = Column(String)
    search_area_name = Column(String)
    type_desc = Column(String)
    type_code = Column(String)
    area_name = Column(String)
    area_code = Column(String)


@serializable
class LAreasTypeSelection(DB.Model):
    __tablename__ = "l_areas_type_selection"
    __table_args__ = ({"schema": "gn_biodivterritory"},)
    id_selection = Column(Integer, primary_key=True)
    id_type = Column(
        Integer, ForeignKey("ref_geo.bib_areas_types.id_type"), unique=True
    )
