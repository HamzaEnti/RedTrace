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
        """Retorna tots els cicles del graf. TODO: implementar _dfs."""
        self._visited.clear()
        self._on_stack.clear()
        self._stack.clear()
        self._cycles.clear()
        # TODO: cridar _dfs per a cada node no visitat
        return []

    def _dfs(self, u: str) -> None:
        """TODO: implementar recorregut DFS recursiu."""
        raise NotImplementedError
