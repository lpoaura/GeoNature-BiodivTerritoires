from decouple import Choices, config
from flask import current_app
from flask_admin import Admin
from flask_assets import Environment
from flask_caching import Cache
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()
admin = Admin(name="Biodiv-Territoires", template_mode="bootstrap4")
assets = Environment()
ckeditor = CKEditor()
cache = Cache(
    config={
        "CACHE_TYPE": config(
            "CACHE_TYPE",
            default="RedisCache",
            cast=Choices(["RedisCache", "null"]),
        ),
        "CACHE_DEFAULT_TIMEOUT": 7200,
    }
)


def create_schemas(db):
    """create db schemas at first launch

    :param db: db connection
    """
    schemas = ["gn_biodivterritory"]
    for schema in schemas:
        current_app.logger.info("create DB schema {}".format(schema))
        db.session.execute("CREATE SCHEMA IF NOT EXISTS {}".format(schema))
    db.session.commit()
