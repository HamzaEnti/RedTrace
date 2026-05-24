"""Dijkstra modificat amb min-heap (heapq) per trobar la ruta d'atac mínima."""

import heapq
from typing import Dict, List, Optional, Set

from engine.base import AttackPathFinder
from engine.graph import TopologyGraph
from engine.types import Edge, Node, Path


class DijkstraFinder(AttackPathFinder):
    """Calcula el camí de menor pes acumulat entre dos nodes."""

    def __init__(self, blocked_nodes: Optional[Set[str]] = None):
        self.blocked_nodes: Set[str] = blocked_nodes or set()

    def find_path(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        if graph.get_node(entry) is None or graph.get_node(target) is None:
            return None

        distances: Dict[str, float] = {nid: float("inf") for nid in graph.node_ids}
        distances[entry] = 0.0
        previous: Dict[str, Optional[str]] = {nid: None for nid in graph.node_ids}
        visited: Set[str] = set()

        heap: List = [(0.0, entry)]

        while heap:
            current_dist, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            if u == target:
                break

            for v in graph.neighbors(u):
                if v in self.blocked_nodes or v in visited:
                    continue
                weight = graph.edge_weight(u, v)
                if weight is None:
                    continue
                new_dist = current_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    previous[v] = u
                    heapq.heappush(heap, (new_dist, v))

        if distances[target] == float("inf"):
            return None

        return self._reconstruct(graph, previous, distances, entry, target)

    @staticmethod
    def _reconstruct(
        graph: TopologyGraph,
        previous: Dict[str, Optional[str]],
        distances: Dict[str, float],
        entry: str,
        target: str,
    ) -> Path:
        node_ids: List[str] = []
        cursor: Optional[str] = target
        while cursor is not None:
            node_ids.append(cursor)
            cursor = previous[cursor]
        node_ids.reverse()

        nodes: List[Node] = [graph.get_node(nid) for nid in node_ids]  # type: ignore[misc]
        edges: List[Edge] = []
        for u, v in zip(node_ids, node_ids[1:]):
            w = graph.edge_weight(u, v) or 0.0
            edges.append(Edge(from_node=u, to_node=v, weight=w))

        return Path(nodes=nodes, edges=edges, total_weight=distances[target])
