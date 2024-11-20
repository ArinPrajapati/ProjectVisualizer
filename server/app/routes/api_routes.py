from flask import Blueprint, jsonify


api = Blueprint("api", __name__)


@api.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "Api is running"})



