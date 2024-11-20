from flask import Blueprint, jsonify, request, send_file
from app.workers.graph import (
    create_graph_from_js_files,
    create_graph_from_github_repo,
    visualize_graph,
)
import os
from io import BytesIO
import tempfile

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
        # Create temporary file for the graph image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            temp_path = tmp_file.name

            # Generate the graph
            if path:
                if not os.path.exists(path):
                    return jsonify({"error": "Invalid or inaccessible path"}), 400
                G = create_graph_from_js_files(path)
            elif repo_url:
                G = create_graph_from_github_repo(repo_url)

            # Generate visualization using the existing function
            visualize_graph(G, output_path=temp_path)

            # Read the generated image
            with open(temp_path, "rb") as img_file:
                output = BytesIO(img_file.read())
                output.seek(0)

            # Clean up the temporary file
            os.unlink(temp_path)

            return send_file(
                output,
                mimetype="image/png",
                as_attachment=False,
                download_name="dependency_graph.png",
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
