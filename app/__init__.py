# Import flask and template operators
from flask import Flask, render_template
from flask_assets import Bundle

import config
from app.utils import create_schemas, DB, assets, admin


# Import SQLAlchemy


def create_app():
    # Define the WSGI application object
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
        template_folder="templates",
    )

    # Configurations
    try:
        app.config.from_object(config)
    except Exception as e:
        print("<create_app> Import config error : ", e)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PYSCSS_STYLE"] = "compressed"
    # Define the database object which is imported
    # by modules and controllers
    DB.init_app(app)
    assets.init_app(app)
    admin.init_app(app)

    # pass parameters to the usershub authenfication sub-module, DONT CHANGE THIS
    app.config["DB"] = DB



    # Sample HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        from app.api_routes import api
        from app.rendered_routes import rendered

        create_schemas(DB)
        DB.create_all()

        # Register blueprint(s)
        app.register_blueprint(rendered)
        app.register_blueprint(api, url_prefix="/api")

        return app



