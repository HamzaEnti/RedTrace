"""Dijkstra modificat amb min-heap (heapq) per trobar la ruta d'atac mínima.

Implementació iterativa amb lazy deletion: un node es marca visitat només
quan surt del heap (no quan s'hi afegeix). Això evita gestionar
decrease-key i és l'aproximació recomanada en Python.

"""

import heapq
from typing import Dict, List, Optional, Set

from engine.base import AttackPathFinder
from engine.graph import TopologyGraph
from engine.types import Edge, Node, Path


class DijkstraFinder(AttackPathFinder):
    """Calcula el camí de menor pes acumulat entre dos nodes."""

    def __init__(self, blocked_nodes: Optional[Set[str]] = None):
        # Conjunt de nodes que l'algorisme ha d'ignorar durant la cerca
        self.blocked_nodes: Set[str] = blocked_nodes or set()

    def find_path(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        # Si qualsevol dels dos nodes no existeix al graf, no hi ha camí possible
        if graph.get_node(entry) is None or graph.get_node(target) is None:
            return None
        
        # Inicialitza totes les distàncies a infinit; l'entrada té cost zero
        distances: Dict[str, float] = {nid: float("inf") for nid in graph.node_ids}
        distances[entry] = 0.0
       

        # Taula de predecessors per poder reconstruir el camí al final
        previous: Dict[str, Optional[str]] = {nid: None for nid in graph.node_ids}

        # Conjunt de nodes ja processats definitivament (lazy deletion)
        visited: Set[str] = set()

        # Min-heap: tuples (distància acumulada, id del node)
        heap: List = [(0.0, entry)]

        while heap:
            # Extreu el node amb menor distància acumulada coneguda
            current_dist, u = heapq.heappop(heap)

            # Lazy deletion: si ja estava visitat, descarta aquesta entrada obsoleta
            if u in visited:
                continue
            visited.add(u)

            # Aturada anticipada: hem arribat al destí, no cal continuar
            if u == target:
                break

            for v in graph.neighbors(u):
                # Salta veïns bloquejats o ja processats definitivament
                if v in self.blocked_nodes or v in visited:
                    continue

                weight = graph.edge_weight(u, v)
                if weight is None:
                    continue

                # Relaxació de l'aresta (u → v)
                new_dist = current_dist + weight
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    previous[v] = u
                    # Afegeix v al heap amb la nova distància millorada
                    heapq.heappush(heap, (new_dist, v))

        # Si la distància al destí continua sent infinit, no existeix cap camí
        if distances[target] == float("inf"):
            return None

        return self._reconstruct(graph, previous, distances, entry, target)
#Començament d'assistencia amb IA
    @staticmethod
    def _reconstruct(
        graph: TopologyGraph,
        previous: Dict[str, Optional[str]],
        distances: Dict[str, float],
        entry: str,
        target: str,
    ) -> Path:
        # Segueix la cadena de predecessors des del destí fins a l'entrada
        node_ids: List[str] = []
        cursor: Optional[str] = target
        while cursor is not None:
            node_ids.append(cursor)
            cursor = previous[cursor]

        # Inverteix la llista per obtenir l'ordre entry → target
        node_ids.reverse()

        # Recupera els objectes Node complets a partir dels seus identificadors
        nodes: List[Node] = [graph.get_node(nid) for nid in node_ids]  # type: ignore[misc]

        # Construeix les arestes del camí i acumula el pes total
        edges: List[Edge] = []
        for u, v in zip(node_ids, node_ids[1:]):
            w = graph.edge_weight(u, v) or 0.0
            edges.append(Edge(from_node=u, to_node=v, weight=w))

        return Path(nodes=nodes, edges=edges, total_weight=distances[target])
#Fi assistencia de IA
