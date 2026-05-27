"""DFS recursiu per detectar cicles al graf de topologia."""

from typing import Dict, List, Optional, Set, Tuple

from source.engine.graph import TopologyGraph


class CycleDetector:
    """Detecta cicles en un graf dirigit mitjançant DFS recursiu.

    Per garantir un temps raonable en grafs densos (on el nombre de cicles
    simples pot ser exponencial), `find_cycles` accepta un `max_cycles`
    opcional que talla la cerca quan s'arriba al límit.
    """

    def __init__(self, graph: TopologyGraph):
        self.graph = graph
        self._visited: Set[str] = set()
        self._on_stack: Set[str] = set()
        self._stack: List[str] = []
        self._cycles: List[List[str]] = []
        # Set de cicles normalitzats per a deduplicació en O(1) amortitzat
        self._seen: Set[Tuple[str, ...]] = set()
        self._max_cycles: Optional[int] = None
        self._stop = False

    """Ajuda amb ús d'IA: inici"""
    def find_cycles(self, max_cycles: Optional[int] = None) -> List[List[str]]:
        self._visited.clear()
        self._on_stack.clear()
        self._stack.clear()
        self._cycles.clear()
        self._seen.clear()
        self._max_cycles = max_cycles
        self._stop = False
        """Ajuda amb ús d'IA: fi"""

        for nid in self.graph.node_ids:
            if self._stop:
                break
            if nid not in self._visited:
                self._dfs(nid)

        return [list(c) for c in self._cycles]

    def _dfs(self, u: str) -> None:
        if self._stop:
            return
        self._visited.add(u)
        self._on_stack.add(u)
        self._stack.append(u)

        for v in self.graph.neighbors(u):
            if self._stop:
                break
            if v not in self._visited:
                self._dfs(v)
            elif v in self._on_stack:
                idx = self._stack.index(v)
                cycle = self._stack[idx:] + [v]
                norm = self._normalize(cycle)
                if norm not in self._seen:
                    self._seen.add(norm)
                    self._cycles.append(cycle)
                    if self._max_cycles is not None and len(self._cycles) >= self._max_cycles:
                        self._stop = True
                        break

        self._on_stack.discard(u)
        self._stack.pop()

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
