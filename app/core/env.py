from flask_admin import Admin
from flask_assets import Environment
from flask_sqlalchemy import SQLAlchemy


DB = SQLAlchemy()
admin = Admin(name="GnBT", template_mode="bootstrap3")
assets = Environment()


def create_schemas(db):
    """create db schemas at first launch

    :param db: db connection
    """
    schemas = ["gn_biodivterritory"]
    for schema in schemas:
        print("create DB schema {}".format(schema))
        db.session.execute("CREATE SCHEMA IF NOT EXISTS {}".format(schema))
    db.session.commit()
