# Import flask and template operators
from flask import Flask, render_template
from flask_assets import Bundle, Environment
from flask_admin import Admin

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
import config
from app.utils import create_schemas

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
    print("Import config error : ", e)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PYSCSS_STYLE"] = "compressed"
# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)
assets = Environment(app)
admin = Admin(app, name="GnBT", template_mode="bootstrap3")

js = Bundle(
    "leaflet.js",
    "vue.js",
    "bootstrap.js",
    "Chart.js",
    "jquery.min.js",
    "select2.js",
    "main.js",
    filters="rjsmin",
    output="bundle.js",
)
assets.register("js_all", js)

css = Bundle(
    "bootstrap.css",
    "leaflet.css",
    "Chart.css",
    "main.css",
    "custom.css",
    "select2.css",
    filters="pyscss",
    output="bundle.css",
)
assets.register("css_all", css)


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


from app.api_routes import api
from app.rendered_routes import rendered

# Create schemas
create_schemas(db)
db.create_all()


# Register blueprint(s)
app.register_blueprint(rendered)
app.register_blueprint(api, url_prefix="/api")
