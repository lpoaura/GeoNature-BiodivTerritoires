# coding: utf8
from __future__ import unicode_literals, print_function, absolute_import, division

from flask import Blueprint, request, jsonify
from utils_flask_sqla.response import json_resp

from . import repository


routes = Blueprint("nomenclatures", __name__)


@routes.route("/nomenclature/<int:id_type>", methods=["GET"])
@json_resp
def get_nomenclature_by_type_and_taxonomy(id_type):
    """
     => Déprécié pour des raisons de volatilité des identifiants en BD

    .. :quickref: Nomenclatures;   

    Route : liste des termes d'une nomenclature basées sur les identifiants de nomenclature
    Possibilité de filtrer par regne et group2Inpn

    """
    regne = request.args.get("regne")
    group2inpn = request.args.get("group2_inpn")

    response = repository.get_nomenclature_list(
        **{
            "id_type": id_type,
            "regne": regne,
            "group2_inpn": group2inpn,
            "filter_params": request.args,
        }
    )
    if not response:
        return {"message": "Nomenclature not found"}, 404
    return response


@routes.route("/nomenclature/<string:code_type>", methods=["GET"])
@json_resp
def get_nomenclature_by_mnemonique_and_taxonomy(code_type):
    """
        Route : liste des termes d'une nomenclature
        basées sur le code mnemonique du type de nomenclature
        Possibilité de filtrer par regne et group2Inpn

        .. :quickref: Nomenclatures;
    """
    regne = request.args.get("regne")
    group2inpn = request.args.get("group2_inpn")

    response = repository.get_nomenclature_list(
        **{
            "code_type": code_type,
            "regne": regne,
            "group2_inpn": group2inpn,
            "filter_params": request.args,
        }
    )
    if not response:
        return {"message": "Nomenclature not found"}, 404
    return response


@routes.route("/nomenclatures", methods=["GET"])
@json_resp
def get_nomenclature_by_type_list_and_taxonomy():
    """
        Route : liste des termes d'un ensemble de nomenclatures
        Possibilité de filtrer par regne et group2Inpn

        .. :quickref: Nomenclatures;
    """
    regne = request.args.get("regne")
    group2inpn = request.args.get("group2_inpn")
    types = []
    if "id_type" in request.args:
        types = request.args.getlist("id_type")
        param = "id_type"
    elif "code_type" in request.args:
        types = request.args.getlist("code_type")
        param = "code_type"

    results = []
    for id_type in types:
        response = repository.get_nomenclature_list(
            **{
                param: id_type,
                "regne": regne,
                "group2_inpn": group2inpn,
                "filter_params": request.args,
            }
        )
        if response:
            results.append(response)

    if results:
        return results
    return {"message": "not found"}, 404


@routes.route("/nomenclatures/taxonomy", methods=["GET"])
@json_resp
def get_nomenclature_with_taxonomy_list():
    response = repository.get_nomenclature_with_taxonomy_list()

    return response
