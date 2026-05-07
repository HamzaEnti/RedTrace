"""DFS recursiu per detectar cicles al graf de topologia."""

from typing import List, Set

from engine.graph import TopologyGraph


class CycleDetector:
    """Detecta cicles en un graf dirigit mitjançant DFS recursiu."""

    def __init__(self, graph: TopologyGraph):
        self.graph = graph
        self._visited: Set[str] = set()
        self._on_stack: Set[str] = set()
        self._stack: List[str] = []
        self._cycles: List[List[str]] = []

    def find_cycles(self) -> List[List[str]]:
        self._visited.clear()
        self._on_stack.clear()
        self._stack.clear()
        self._cycles.clear()

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
                self._cycles.append(cycle)

        self._on_stack.discard(u)
        self._stack.pop()
