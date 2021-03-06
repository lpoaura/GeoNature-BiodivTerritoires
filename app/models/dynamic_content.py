# coding: utf-8
from datetime import datetime

from flask import current_app
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from utils_flask_sqla.serializers import serializable

from app import admin
from app.core.env import DB


@serializable
class BibDynamicPagesCategory(DB.Model):
    __tablename__ = "bib_dynamic_pages_category"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}

    id_category = Column(Integer, primary_key=True)
    category_name = Column(String)
    category_desc = Column(String)


@serializable
class TDynamicPages(DB.Model):
    __tablename__ = "t_dynamic_pages"
    __table_args__ = {"schema": current_app.config["APP_SCHEMA_NAME"]}

    id_page = Column(Integer, primary_key=True)
    id_category = Column(
        Integer,
        ForeignKey(
            "gn_biodivterritory.bib_dynamic_pages_category.id_category"
        ),
    )
    title = Column(String)
    link_name = Column(String, unique=True)
    navbar_link = Column(Boolean)
    navbar_link_order = Column(Integer)
    url = Column(String, unique=True)
    short_desc = Column(String)
    ts_create = Column(DateTime, default=datetime.now())
    ts_update = Column(DateTime, default=datetime.now())
    creator = Column(String)
    is_active = Column(Boolean)
    content = Column(Text)
    category = DB.relationship(
        "BibDynamicPagesCategory",
        backref=DB.backref("category", lazy="dynamic"),
    )


admin.add_view(
    ModelView(
        BibDynamicPagesCategory,
        DB.session,
        "Category",
        category="Dynamic content",
    )
)
admin.add_view(
    ModelView(TDynamicPages, DB.session, "Pages", category="Dynamic content"),
)
