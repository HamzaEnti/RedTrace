"""Visualització matplotlib del graf amb la ruta d'atac destacada."""

from pathlib import Path as _PathLib
from typing import Set, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from engine.graph import TopologyGraph
from engine.risk import make_classifier
from engine.types import Path


class TopologyVisualizer:
    def __init__(self, graph: TopologyGraph):
        self.graph = graph

    def plot(self, path: Path, output_path: str, title: str = "RedTrace") -> None:
        g = self.graph.raw
        pos = nx.spring_layout(g, seed=42, k=1.5, iterations=80)

        node_colors = []
        for nid in g.nodes:
            node = self.graph.get_node(nid)
            color = make_classifier(node.risk_level).get_color() if node else "#888"
            node_colors.append(color)

        path_edges: Set[Tuple[str, str]] = {(e.from_node, e.to_node) for e in path.edges}
        edge_colors = []
        edge_widths = []
        for u, v in g.edges:
            if (u, v) in path_edges:
                edge_colors.append("#D32F2F")
                edge_widths.append(3.0)
            else:
                edge_colors.append("#BDBDBD")
                edge_widths.append(1.0)

        plt.figure(figsize=(13, 9))
        nx.draw_networkx_nodes(g, pos, node_color=node_colors, node_size=1100, edgecolors="black")
        nx.draw_networkx_edges(
            g, pos, edge_color=edge_colors, width=edge_widths, arrows=True, arrowsize=14
        )
        nx.draw_networkx_labels(g, pos, font_size=8, font_weight="bold")

        edge_labels = {(u, v): f"{g[u][v]['weight']:.2f}" for u, v in g.edges}
        nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=7)

        legend_handles = [
            plt.scatter([], [], c="#4CAF50", s=120, label="LOW"),
            plt.scatter([], [], c="#FF9800", s=120, label="MEDIUM"),
            plt.scatter([], [], c="#F44336", s=120, label="CRITICAL"),
            plt.plot([], [], color="#D32F2F", linewidth=3, label="Ruta d'atac")[0],
        ]
        plt.legend(handles=legend_handles, loc="upper left")
        plt.title(title)
        plt.axis("off")
        plt.tight_layout()

        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
