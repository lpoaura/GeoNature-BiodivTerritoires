# coding: utf-8
from datetime import datetime

from flask_admin.contrib.sqla import ModelView
from flask_ckeditor import CKEditorField
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean
from utils_flask_sqla.serializers import serializable

from app import admin
from app.core.env import DB


@serializable
class BibDynamicPagesCategory(DB.Model):
    __tablename__ = "bib_dynamic_pages_category"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_category = Column(Integer, primary_key=True)
    category_name = Column(String)
    category_desc = Column(String)


@serializable
class TDynamicPages(DB.Model):
    __tablename__ = "t_dynamic_pages"
    __table_args__ = {"schema": "gn_biodivterritory"}

    id_page = Column(Integer, primary_key=True)
    id_category = Column(
        Integer, ForeignKey("gn_biodivterritory.bib_dynamic_pages_category.id_category")
    )
    title = Column(String)
    link_name = Column(String, unique=True)
    url = Column(String, unique=True)
    short_desc = Column(String)
    ts_create = Column(DateTime, default=datetime.now())
    ts_update = Column(DateTime, default=datetime.now())
    creator = Column(String)
    is_active = Column(Boolean)
    content = Column(Text)
    category = DB.relationship(
        "BibDynamicPagesCategory", backref=DB.backref("category", lazy="dynamic")
    )


class TDynamicPagesModelView(ModelView):
    form_overrides = {"content": CKEditorField}

    create_template = "admin/ckeditor.html"
    edit_template = "admin/ckeditor.html"


admin.add_view(
    ModelView(BibDynamicPagesCategory, DB.session, category="Contenu dynamique")
)
admin.add_view(
    TDynamicPagesModelView(TDynamicPages, DB.session, category="Contenu dynamique")
)
