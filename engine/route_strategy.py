"""Estratègies de ruta per seleccionar el camí d'atac òptim."""

from typing import Optional

from engine.base import RouteStrategy
from engine.dijkstra import DijkstraPathFinder
from engine.types import Path


class ShortestRoute(RouteStrategy):
    """Selecciona la ruta amb menys pes acumulat (Dijkstra)."""

    def select(self, graph, entry: str, target: str) -> Optional[Path]:
        finder = DijkstraPathFinder(invert_weights=False)
        return finder.find_path(graph, entry, target)


class SafestRoute(RouteStrategy):
    """Selecciona la ruta que minimitza el risc màxim dels nodes travessats.

    Inverteix els pesos per buscar el camí amb menor risc acumulat.
    Correcció: invert_weights=True fa servir (1 - w) → prefereix arestes
    amb pes baix (menys exposades).
    """

    def select(self, graph, entry: str, target: str) -> Optional[Path]:
        finder = DijkstraPathFinder(invert_weights=True)
        return finder.find_path(graph, entry, target)
