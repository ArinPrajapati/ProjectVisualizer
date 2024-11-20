import networkx as nx
import os
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
        print(temp_dir)
        # visualize_graph(G)
        return G
    except Exception as e:
        raise Exception(f"Error cloning repository: {e}")
    finally:
        shutil.rmtree(temp_dir)


def visualize_graph(G, output_path="dependency_graph.png"):
    """
    Create a more organized and readable visualization of the dependency graph.
    Uses spring_layout instead of kamada_kawai_layout to avoid scipy dependency.
    """
    plt.figure(figsize=(16, 12))  # Larger figure size for better readability

    # Use spring layout with optimized parameters for better organization
    pos = nx.spring_layout(G, k=2, iterations=50)

    # Set base node size
    base_node_size = 2000

    # Draw nodes with different colors based on type
    external_deps = [node for node in G.nodes() if not node.endswith(".js")]
    internal_deps = [node for node in G.nodes() if node.endswith(".js")]

    # Draw internal files (*.js files)
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=internal_deps,
        node_color="lightblue",
        node_size=base_node_size,
        alpha=0.7,
    )

    # Draw external dependencies (npm packages, etc.)
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=external_deps,
        node_color="lightgreen",
        node_size=base_node_size,
        alpha=0.7,
    )

    # Draw edges with different styles based on type
    edges_local = [(u, v) for (u, v) in G.edges() if G[u][v].get("type") == "local"]
    edges_external = [
        (u, v) for (u, v) in G.edges() if G[u][v].get("type") == "external"
    ]

    # Draw local dependencies
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=edges_local,
        edge_color="blue",
        alpha=0.4,
        arrows=True,
        arrowsize=20,
    )

    # Draw external dependencies
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=edges_external,
        edge_color="red",
        alpha=0.4,
        arrows=True,
        arrowsize=20,
    )

    # Add labels with better formatting
    labels = {
        node: "\n".join(node.split("/")[-2:]) if "/" in node else node
        for node in G.nodes()
    }

    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_weight="bold")

    # Add a title and legend
    plt.title("JavaScript Dependencies Graph", pad=20, size=16)

    # Add legend with fixed marker sizes
    legend_elements = [
        plt.Line2D([0], [0], color="blue", alpha=0.4, label="Local Dependencies"),
        plt.Line2D([0], [0], color="red", alpha=0.4, label="External Dependencies"),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="lightblue",
            label="Internal Files",
            markersize=10,
            linestyle="None",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="lightgreen",
            label="External Packages",
            markersize=10,
            linestyle="None",
        ),
    ]
    plt.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1))

    # Add padding around the graph
    plt.margins(0.2)

    # Ensure the layout is tight but includes the legend
    plt.tight_layout()

    # Save with high DPI for better quality
    plt.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.5)
    plt.close()

    print(f"Graph saved to {output_path}")
    return output_path
