# Import flask and template operators
from flask import Flask, render_template

import config
from app.core.env import create_schemas, DB, assets, admin, ckeditor


# Import SQLAlchemy


def create_app():
    # Define the WSGI application object
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="static",
        template_folder="templates",
    )
    app.secret_key = config.SECRET_KEY
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
    ckeditor.init_app(app)

    # pass parameters to the usershub authenfication sub-module, DONT CHANGE THIS
    app.config["DB"] = DB

    # Sample HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    with app.app_context():
        from app.core.api.routes import api
        from app.core.frontend.routes import rendered
        from pypnusershub.routes import routes as users_routes
        from pypnnomenclature.routes import routes as nom_routes

        create_schemas(DB)
        DB.create_all()

        # Register blueprint(s)
        app.register_blueprint(rendered)
        app.register_blueprint(api, url_prefix="/api")
        app.register_blueprint(users_routes, url_prefix="/auth")
        app.register_blueprint(nom_routes, url_prefix="/api/nomenclatures")

        return app
