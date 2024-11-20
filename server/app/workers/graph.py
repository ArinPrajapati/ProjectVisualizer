import networkx as nx
import os
import json
import re
from git import Repo
import shutil
import tempfile
from urllib.parse import urlparse
import matplotlib.pyplot as plt
from pathlib import Path


def parse_dependencies(content):
    """Parse both import and require statements more accurately."""
    dependencies = []

    # Regular expressions for different import patterns
    import_patterns = [
        r'import\s+.*?from\s+["\']([^"\']+)["\']',  # import x from 'y'
        r'require\(["\']([^"\']+)["\']\)',  # require('x')
        r'import\s+["\']([^"\']+)["\']',  # import 'x'
    ]

    for pattern in import_patterns:
        matches = re.finditer(pattern, content)
        dependencies.extend(match.group(1) for match in matches)

    return dependencies


def get_file_info(file_path):
    """Get file attributes for node metadata."""
    stats = os.stat(file_path)
    return {
        "size": stats.st_size,
        "path": str(file_path),
        "last_modified": stats.st_mtime,
    }


def create_graph_from_js_files(path):
    G = nx.DiGraph()
    path = Path(path)

    try:
        for file_path in path.rglob("*.js"):
            relative_path = file_path.relative_to(path)
            file_info = get_file_info(file_path)

            # Add node with attributes
            G.add_node(str(relative_path), **file_info)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    dependencies = parse_dependencies(content)

                    for dep in dependencies:
                        # Handle different dependency types
                        if dep.endswith(".js"):
                            # Local dependency
                            G.add_edge(str(relative_path), dep, type="local")
                        else:
                            # External dependency
                            G.add_edge(str(relative_path), dep, type="external")

            except (IOError, UnicodeDecodeError) as e:
                print(f"Error reading file {file_path}: {e}")

    except Exception as e:
        print(f"Error processing directory {path}: {e}")

    return G


def validate_github_url(url):
    """Validate GitHub repository URL."""
    try:
        parsed = urlparse(url)
        return (
            parsed.netloc == "github.com"
            and len(parsed.path.strip("/").split("/")) == 2
        )
    except Exception:
        return False


def create_graph_from_github_repo(repo_url):
    if not validate_github_url(repo_url):
        raise ValueError("Invalid GitHub repository URL")

    temp_dir = tempfile.mkdtemp()
    try:
        Repo.clone_from(repo_url, temp_dir)
        G = create_graph_from_js_files(temp_dir)
        return G
    except Exception as e:
        raise Exception(f"Error cloning repository: {e}")
    finally:
        shutil.rmtree(temp_dir)


def visualize_graph(G, output_path="dependency_graph.png"):
    """Visualize the dependency graph."""
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue")

    # Draw edges with different colors based on type
    edge_colors = [
        "green" if G[u][v].get("type") == "local" else "red" for u, v in G.edges()
    ]
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors)

    # Add labels
    nx.draw_networkx_labels(G, pos)

    plt.title("JavaScript Dependencies Graph")
    plt.axis("off")
    plt.savefig(output_path)
    plt.close()

    return output_path
