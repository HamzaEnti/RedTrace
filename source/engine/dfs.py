"""DFS recursiu per detectar cicles al graf de topologia."""

from typing import Dict, List, Set

from source.engine.graph import TopologyGraph


class CycleDetector:
    """Detecta cicles en un graf dirigit mitjançant DFS recursiu."""

    def __init__(self, graph: TopologyGraph):
        self.graph = graph
        self._visited: Set[str] = set()
        self._on_stack: Set[str] = set()
        self._stack: List[str] = []
        self._cycles: List[List[str]] = []

    """Ajuda amb ús d'IA: inici"""
    def find_cycles(self) -> List[List[str]]:
        self._visited.clear()
        self._on_stack.clear()
        self._stack.clear()
        self._cycles.clear()
        """Ajuda amb ús d'IA: fi"""

        for nid in self.graph.node_ids:
            if nid not in self._visited:
                self._dfs(nid)

        return [list(c) for c in self._cycles]

    def _dfs(self, u: str) -> None:
        self._visited.add(u)
        self._on_stack.add(u)
        self._stack.append(u)

        for v in self.graph.neighbors(u):
            if v not in self._visited:
                self._dfs(v)
            elif v in self._on_stack:
                idx = self._stack.index(v)
                cycle = self._stack[idx:] + [v]
                if not self._is_duplicate(cycle):
                    self._cycles.append(cycle)

        self._on_stack.discard(u)
        self._stack.pop()

    def _is_duplicate(self, cycle: List[str]) -> bool:
        norm = self._normalize(cycle)
        for existing in self._cycles:
            if self._normalize(existing) == norm:
                return True
        return False
    """Ajuda amb ús d'IA: inici"""
    @staticmethod
    def _normalize(cycle: List[str]) -> tuple:
        body = cycle[:-1]
        if not body:
            return tuple(cycle)
        min_idx = body.index(min(body))
        rotated = body[min_idx:] + body[:min_idx]
        return tuple(rotated)
    """Ajuda amb ús d'IA: fi"""
