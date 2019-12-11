from flask import render_template, redirect, abort
from config import config

from flask import Blueprint

main = Blueprint('main', __name__)

@main.context_processor
def global_variables():
    values= {}
    values['site_name'] = config.SITE_NAME
    return values

@main.route('/')
def index():
   return render_template('home.html', name = config.SITE_NAME)

@main.route('/territory/<insee>')
def territory(insee):
   return render_template('territory.html', insee = insee)

@main.route('/proxy/<user>')
def proxy_test(user):
   return render_template('proxy.html', name = user)
