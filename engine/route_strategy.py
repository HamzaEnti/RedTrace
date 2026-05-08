"""Estratègies de ruta per seleccionar el camí d'atac òptim."""

from typing import Optional

from engine.base import RouteStrategy
from engine.dijkstra import DijkstraPathFinder
from engine.types import Path


class ShortestRoute(RouteStrategy):
    """Selecciona la ruta amb menys pes acumulat (Dijkstra)."""

    def select(self, graph, entry: str, target: str) -> Optional[Path]:
        finder = DijkstraPathFinder()
        return finder.find_path(graph, entry, target)


class SafestRoute(RouteStrategy):
    """Selecciona la ruta que minimitza el risc màxim dels nodes travessats.

    Ha d'invertir els pesos (1 - weight) perquè Dijkstra trobi el camí amb 
    menor risc acumulat en lloc del menor cost.
    """
    
    """
    TODO: verificar direcció de la comparació.
    """

    def select(self, graph, entry: str, target: str) -> Optional[Path]:
        finder = DijkstraPathFinder(invert_weights=True)
        return finder.find_path(graph, entry, target)
