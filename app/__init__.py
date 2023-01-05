# Import flask and template operators
import logging

from decouple import config
from flask import Flask, render_template

from app.core.env import DB, admin, assets, cache, ckeditor, create_schemas

logger = logging.getLogger(__name__)

# Import SQLAlchemy


def create_app():
    # Define the WSGI application object
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
        template_folder="templates",
    )
    # Add Colored logs
    if app.debug:
        import coloredlogs
        import flask_monitoringdashboard as dashboard

        coloredlogs.install(level="DEBUG")
        dashboard.bind(app)

    app.app_context().push()
    app.secret_key = config("SECRET_KEY")

    # Load config
    try:
        # debug
        app.config["DEBUG"] = config("DEBUG", default=False, cast=bool)

        # Global app tech info
        app.config["APP_SCHEMA_NAME"] = config(
            "APP_SCHEMA_NAME", default="gn_biodivterritory"
        )
        app.config["LOCAL_SRID"] = config("LOCAL_SRID", default=4326)
        app.config["SQLALCHEMY_DATABASE_URI"] = config(
            "SQLALCHEMY_DATABASE_URI"
        )
        app.config["DEFAULT_GRID"] = config("DEFAULT_GRID", default="M1")
        app.config["DEFAULT_BUFFER"] = config("DEFAULT_BUFFER", default=2000)
        app.config["TAXHUB_URL"] = config(
            "TAXHUB_URL", default="http://demo.geonature.fr/taxhub/"
        )
        app.config["TAXA_LINK_URL_TEMPLATE"] = config(
            "TAXA_LINK_URL_TEMPLATE", default="https://inpn.mnhn.fr/espece/cd_nom/[CDNOM]"
        )

        # Global app info
        app.config["SITE_NAME"] = config(
            "SITE_NAME", default="Biodiv'Territoires"
        )
        app.config["SITE_DESC"] = config(
            "SITE_DESC",
            default="Une plateforme de porté à connaissance de la <b>biodiversité</b> des territoires",
        )

        # Cache
        app.config["CACHE_TIMEOUT"] = config("CACHE_TIMEOUT", default=86400)
        app.config["CACHE_REDIS_HOST"] = config(
            "CACHE_REDIS_HOST", default="redis"
        )
        app.config["CACHE_REDIS_PORT"] = config(
            "CACHE_REDIS_PORT", default=6379
        )

    except Exception as e:
        app.logger.critical("<create_app> Import config error : ", e)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PYSCSS_STYLE"] = "compressed"
    app.config["SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS"] = True
    # Define the database object which is imported
    # by modules and controllers
    DB.init_app(app)
    assets.init_app(app)
    admin.init_app(app)
    ckeditor.init_app(app)
    cache.init_app(app)

    # pass parameters to the usershub authenfication sub-module, DONT CHANGE THIS
    app.config["DB"] = DB

    # Sample HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        # from pypnusershub.routes import routes as users_routes
        from pypnnomenclature.routes import routes as nom_routes

        from app.core.api.routes import api
        from app.core.frontend.routes import rendered
        from app.core.utils import (
            create_special_pages,
            create_tables,
            init_custom_files,
        )

        create_schemas(DB)

        create_tables(DB)

        create_special_pages()
        init_custom_files()
        # Register blueprint(s)
        app.register_blueprint(rendered)
        app.register_blueprint(api, url_prefix="/api")
        app.register_blueprint(nom_routes, url_prefix="/api/nomenclatures")
        return app
