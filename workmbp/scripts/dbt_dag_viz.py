#!/usr/bin/env python3
"""
Script to visualize dbt DAG from manifest.json using graph-easy

Usage: dbt_dag_viz.py [manifest.json path] [options]

Options:
  -m, --models PATTERN     Only show models matching pattern (regex)
  -t, --type TYPE          Filter by resource type (model, seed, snapshot, source)
  -f, --format FORMAT      Output format: ascii, boxart, dot, svg, html (default: boxart)
  -h, --help               Show this help
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize dbt DAG from manifest.json using graph-easy"
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default="target/manifest.json",
        help="Path to manifest.json (default: target/manifest.json)",
    )
    parser.add_argument(
        "-m",
        "--models",
        help="Only show models matching pattern (regex)",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["model", "seed", "snapshot", "source"],
        help="Filter by resource type",
    )
    parser.add_argument(
        "-f",
        "--format",
        default="boxart",
        choices=["ascii", "boxart", "dot", "svg", "html"],
        help="Output format (default: boxart)",
    )
    return parser.parse_args()


def check_dependencies():
    """Check if graph-easy is installed"""
    try:
        subprocess.run(
            ["graph-easy", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: graph-easy is required but not installed", file=sys.stderr)
        sys.exit(1)


def load_manifest(path):
    """Load and parse manifest.json"""
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(f"Error: manifest.json not found at {path}", file=sys.stderr)
        print("Run 'dbt compile' or 'dbt run' to generate it.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        return json.load(f)


def extract_graph_edges(manifest, model_pattern=None, resource_type=None):
    """
    Extract graph edges from manifest.json

    Returns a set of edges in graph-easy format: "[source] -> [target]"
    """
    edges = set()
    nodes_in_graph = set()

    # Compile regex pattern if provided
    pattern = re.compile(model_pattern) if model_pattern else None

    # Supported resource types
    supported_types = {"model", "seed", "snapshot", "source"}

    for unique_id, node in manifest.get("nodes", {}).items():
        # Filter by resource type
        if node.get("resource_type") not in supported_types:
            continue

        if resource_type and node.get("resource_type") != resource_type:
            continue

        # Get node name
        node_name = node.get("name", "")

        # Filter by pattern
        if pattern and not pattern.search(node_name):
            continue

        nodes_in_graph.add(node_name)

        # Extract dependencies
        depends_on = node.get("depends_on", {})
        dep_nodes = depends_on.get("nodes", [])

        if dep_nodes:
            for dep_id in dep_nodes:
                # Get dependency name from unique_id
                # Format: "model.project.name" -> "name"
                dep_name = dep_id.split(".")[-1]

                # Check if dependency should be included
                if pattern:
                    # Only include if both nodes match pattern
                    if not pattern.search(dep_name):
                        continue

                edges.add(f"[{dep_name}] -> [{node_name}]")
                nodes_in_graph.add(dep_name)
        else:
            # Node with no dependencies - still add it to show it exists
            edges.add(f"[{node_name}]")

    return sorted(edges)


def visualize_graph(edges, output_format):
    """
    Pipe edges to graph-easy for visualization
    """
    if not edges:
        print("No nodes found matching the criteria", file=sys.stderr)
        return

    # Join edges with newlines
    graph_input = "\n".join(edges)

    # Call graph-easy
    try:
        result = subprocess.run(
            ["graph-easy", f"--as={output_format}"],
            input=graph_input,
            text=True,
            capture_output=True,
            check=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running graph-easy: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_args()

    check_dependencies()

    manifest = load_manifest(args.manifest)

    edges = extract_graph_edges(
        manifest,
        model_pattern=args.models,
        resource_type=args.type,
    )

    visualize_graph(edges, args.format)


if __name__ == "__main__":
    main()
