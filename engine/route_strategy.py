"""Estratègies polimòrfiques per seleccionar rutes (R3 enunciat)."""

from typing import Optional, Set

from engine.base import RouteStrategy
from engine.bfs import BFSFinder
from engine.dijkstra import DijkstraFinder
from engine.graph import TopologyGraph
from engine.types import Path


CRITICAL_RISK_THRESHOLD = 0.80


class ShortestRoute(RouteStrategy):
    """Ruta de menor pes total: Dijkstra clàssic sense restriccions."""

    def select(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        return DijkstraFinder().find_path(graph, entry, target)


class SafestRoute(RouteStrategy):
    """Evita els nodes amb risc igual o superior al llindar crític."""

    def __init__(self, threshold: float = CRITICAL_RISK_THRESHOLD):
        self.threshold = threshold

    def select(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        blocked: Set[str] = {
            n.id
            for n in graph.nodes
            if n.risk >= self.threshold and n.id not in (entry, target)
        }
        return DijkstraFinder(blocked_nodes=blocked).find_path(graph, entry, target)

class FewestHopsRoute(RouteStrategy):
    """Camí amb el menor nombre d'arestes (BFS), ignorant pesos."""

    def __init__(self, avoid_critical: bool = False,
                 threshold: float = CRITICAL_RISK_THRESHOLD):
        self.avoid_critical = avoid_critical
        self.threshold = threshold

    def select(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        blocked: Set[str] = set()
        if self.avoid_critical:
            blocked = {
                n.id
                for n in graph.nodes
                if n.risk >= self.threshold and n.id not in (entry, target)
            }
        return BFSFinder(blocked_nodes=blocked).find_path(graph, entry, target)
