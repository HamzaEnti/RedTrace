"""
Breadth-First Search per trobar el camí amb menys salts entrada→objectiu.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Optional, Set
from source.engine.base import AttackPathFinder
from source.engine.graph import TopologyGraph
from source.engine.types import Edge, Node, Path


class BFSFinder(AttackPathFinder):
    """Ajuda amb ús d'IA: inici"""
    """Troba el camí amb el menor nombre d'arestes (hops). (WIP)"""

    def __init__(self, blocked_nodes: Optional[Set[str]] = None):
        self.blocked_nodes: Set[str] = blocked_nodes or set()

    def find_path(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        if graph.get_node(entry) is None or graph.get_node(target) is None:
            return None
        if entry == target:
            n = graph.get_node(entry)
            return Path(nodes=[n], edges=[], total_weight=0.0)
        visited: Set[str] = {entry}
        previous: Dict[str, Optional[str]] = {entry: None}
        queue: Deque[str] = deque([entry])
        """Ajuda amb ús d'IA: fi"""

        while queue:
            u = queue.popleft()
            if u == target:
                break
            for v in graph.neighbors(u):
                if v in visited or v in self.blocked_nodes:
                    continue
                visited.add(v)
                previous[v] = u
                queue.append(v)

        if target not in previous:
            return None

        return self._reconstruct(graph, previous, entry, target)

    @staticmethod
    def _reconstruct(
        graph: TopologyGraph,
        previous: Dict[str, Optional[str]],
        entry: str,
        target: str,
    ) -> Path:
        ids: List[str] = []
        cursor: Optional[str] = target
        while cursor is not None:
            ids.append(cursor)
            cursor = previous[cursor]
        ids.reverse()
        """Ajuda amb ús d'IA: inici"""
        nodes: List[Node] = [graph.get_node(nid) for nid in ids]  # type: ignore[misc]
        edges: List[Edge] = []
        total = 0.0
        """Ajuda amb ús d'IA: fi"""
        for u, v in zip(ids, ids[1:]):
            w = graph.edge_weight(u, v) or 0.0
            edges.append(Edge(from_node=u, to_node=v, weight=w))
            total += w

        return Path(nodes=nodes, edges=edges, total_weight=total)