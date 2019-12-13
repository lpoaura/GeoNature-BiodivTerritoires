from flask import render_template, redirect, abort
import config
from .models.ref_geo import LAreas

from flask import Blueprint

rendered = Blueprint('rendered', __name__)

@rendered.context_processor
def global_variables():
    values= {}
    values['site_name'] = config.SITE_NAME
    return values

@rendered.route('/')
def index():
   return render_template('home.html', name = config.SITE_NAME)

@rendered.route('/territory/<code>')
def territory(code):
   area = LAreas.query.filter_by(area_code=code).first()
   area_code = area.area_code
   area_name = area.area_name
   return render_template('territory.html', code=area_code, name=area_name)

@rendered.route('/proxy/<user>')
def proxy_test(user):
   return render_template('proxy.html', name = user)

