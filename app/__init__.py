# Import flask and template operators
from flask import Flask, render_template
from flask_assets import Environment, Bundle

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

# Define the WSGI application object
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder="static",
    template_folder="templates",
)

# Configurations
app.config.from_object("config")
app.config["PYSCSS_STYLE"] = "compressed"
# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)
assets = Environment(app)

js = Bundle(
    "vue.js",
    "bootstrap.js",
    "leaflet.js",
    "Chart.js",
    filters="rjsmin",
    output="bundle.js",
)
assets.register("js_all", js)

css = Bundle(
    "bootstrap.css", "leaflet.css", "Chart.css", filters="pyscss", output="bundle.css"
)
assets.register("css_all", css)

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# Import a module / component using its blueprint handler variable (mod_auth)
from app.rendered_routes import rendered
from app.api_routes import api

# Register blueprint(s)
app.register_blueprint(rendered)
app.register_blueprint(api, url_prefix="/api")

