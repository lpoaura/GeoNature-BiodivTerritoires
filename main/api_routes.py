from flask import render_template, redirect, abort
from config import config
from flask import jsonify

from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/test')
def index():
    return jsonify({"test":"test de sortie json"})

