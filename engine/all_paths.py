"""Enumeració de tots els camins simples entre dos nodes via backtracking.

És el cas d'ús que esmenta E17 de l'enunciat:
    «backtracking recursiu que trobi tots els camins possibles entre A i B
     esquivant els nodes dolents».

A diferència de Dijkstra (un sol camí òptim) o BFS (un sol camí amb menys
salts), aquest mòdul retorna **tots** els camins simples (sense repetir
nodes). Permet anàlisi forense / what-if posterior.
"""

from __future__ import annotations

from typing import List, Optional, Set

from engine.graph import TopologyGraph
from engine.types import Edge, Node, Path


class AllPathsFinder:
    """Enumera camins simples entry→target mitjançant DFS amb backtracking."""

    def __init__(
        self,
        blocked_nodes: Optional[Set[str]] = None,
        max_paths: Optional[int] = None,
        max_depth: Optional[int] = None,
    ):
        self.blocked_nodes: Set[str] = blocked_nodes or set()
        self.max_paths = max_paths
        self.max_depth = max_depth

    def find_all(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> List[Path]:
        """Retorna tots els camins simples entre entry i target."""
        if graph.get_node(entry) is None or graph.get_node(target) is None:
            return []
        if entry in self.blocked_nodes or target in self.blocked_nodes:
            return []

        results: List[Path] = []
        current_ids: List[str] = [entry]
        visited: Set[str] = {entry}

        self._backtrack(graph, entry, target, current_ids, visited, results)
        return results

    def _backtrack(
        self,
        graph: TopologyGraph,
        u: str,
        target: str,
        current_ids: List[str],
        visited: Set[str],
        results: List[Path],
    ) -> None:
        if self.max_paths is not None and len(results) >= self.max_paths:
            return
        if self.max_depth is not None and len(current_ids) > self.max_depth:
            return

        if u == target:
            results.append(self._materialize(graph, current_ids))
            return

        for v in graph.neighbors(u):
            if v in visited or v in self.blocked_nodes:
                continue
            visited.add(v)
            current_ids.append(v)

            self._backtrack(graph, v, target, current_ids, visited, results)

            # Desfà l'estat (backtracking)
            current_ids.pop()
            visited.remove(v)

    @staticmethod
    def _materialize(graph: TopologyGraph, ids: List[str]) -> Path:
        nodes: List[Node] = [graph.get_node(nid) for nid in ids]  # type: ignore[misc]
        edges: List[Edge] = []
        total = 0.0
        for u, v in zip(ids, ids[1:]):
            w = graph.edge_weight(u, v) or 0.0
            edges.append(Edge(from_node=u, to_node=v, weight=w))
            total += w
        return Path(nodes=nodes, edges=edges, total_weight=total)
