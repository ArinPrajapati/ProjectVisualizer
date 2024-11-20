from flask import Blueprint, jsonify, request, send_file
from app.workers.graph import create_graph_from_js_files, create_graph_from_github_repo
import networkx as nx
import os
from io import BytesIO
import matplotlib.pyplot as plt

api = Blueprint("api", __name__)


@api.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "Api is running"})


@api.route("/graph", methods=["POST"])
def graph():
    data = request.json
    path = data.get("path")
    repo_url = data.get("repo_url")

    if not path and not repo_url:
        return jsonify({"error": "No path or repo_url provided"}), 400

    try:
        if path:
            if not os.path.exists(path):
                return jsonify({"error": "Invalid or inaccessible path"}), 400
            G = create_graph_from_js_files(path)
        elif repo_url:
            G = create_graph_from_github_repo(repo_url)

        # Generate the graph visualization
        pos = nx.spring_layout(G)
        plt.figure(figsize=(10, 7))
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_size=5000,
            node_color="skyblue",
            font_size=10,
            font_weight="bold",
            arrows=True,
        )

        # Save graph image to an in-memory buffer
        output = BytesIO()
        plt.savefig(output, format="png")
        output.seek(0)
        plt.close()

        return send_file(output, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
