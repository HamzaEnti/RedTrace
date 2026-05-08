"""Algoritme de Dijkstra per trobar la ruta d'atac òptima."""

import heapq
from typing import Dict, List, Optional

from engine.base import AttackPathFinder
from engine.types import Edge, Node, Path


class DijkstraPathFinder(AttackPathFinder):
    """Troba la ruta de menor cost entre entry i target. WIP."""

    def __init__(self, invert_weights: bool = False):
        self.invert_weights = invert_weights

    def find_path(self, graph, entry: str, target: str) -> Optional[Path]:
        """TODO: implementar Dijkstra amb reconstrucció de camí."""
        raise NotImplementedError("Dijkstra pendent d'implementació")
