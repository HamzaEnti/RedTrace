"""Visualitzador de la topologia de xarxa amb matplotlib.

TODO: afegir coloració per nivell de risc i marcadors de ruta.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import networkx as nx

from engine.graph import TopologyGraph


class NetworkVisualizer:
    """Genera una imatge de la topologia amb la ruta destacada."""

    def __init__(self, graph: TopologyGraph):
        self.graph = graph

    def render(self, output_path: str, attack_path: Optional[List[str]] = None) -> None:
        fig, ax = plt.subplots(figsize=(12, 8))
        g = self.graph.raw
        pos = nx.spring_layout(g, seed=42)

        nx.draw_networkx(g, pos=pos, ax=ax,
                         node_color="#555", font_color="white",
                         edge_color="#888", node_size=800)

        if attack_path and len(attack_path) > 1:
            path_edges = list(zip(attack_path[:-1], attack_path[1:]))
            nx.draw_networkx_edges(g, pos=pos, edgelist=path_edges,
                                   edge_color="#E53935", width=2.5, ax=ax)

        ax.set_title("RedTrace — Topologia de xarxa")
        ax.axis("off")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
