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
        # Nodes que el DFS no pot travessar en cap circumstància
        self.blocked_nodes: Set[str] = blocked_nodes or set()

        # Límit opcional de camins trobats; evita explosió combinatòria en grafs densos
        self.max_paths = max_paths

        # Profunditat màxima de recursió; limita camins molt llargs
        self.max_depth = max_depth

    def find_all(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> List[Path]:
        """Retorna tots els camins simples entre entry i target."""
        # Comprova que els dos extrems existeixen al graf
        if graph.get_node(entry) is None or graph.get_node(target) is None:
            return []

        # Si l'entrada o el destí estan bloquejats, cap camí és viable
        if entry in self.blocked_nodes or target in self.blocked_nodes:
            return []

        results: List[Path] = []

        # Camí actual en construcció (llista d'ids de node)
        current_ids: List[str] = [entry]

        # Conjunt de nodes ja presents al camí actual (evita cicles)
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
        # Atura la recursió si ja hem assolit el límit de camins sol·licitat
        if self.max_paths is not None and len(results) >= self.max_paths:
            return

        # Atura la recursió si el camí actual supera la profunditat màxima
        if self.max_depth is not None and len(current_ids) > self.max_depth:
            return

        # Cas base: hem arribat al destí; materialitza i desa el camí complet
        if u == target:
            results.append(self._materialize(graph, current_ids))
            return

        for v in graph.neighbors(u):
            # Salta nodes ja visitats en aquest camí o explícitament bloquejats
            if v in visited or v in self.blocked_nodes:
                continue

            # Marca v com a visitat i l'afegeix al camí actual
            visited.add(v)
            current_ids.append(v)

            self._backtrack(graph, v, target, current_ids, visited, results)

            # Desfà l'estat (backtracking): elimina v per explorar altres branques
            current_ids.pop()
            visited.remove(v)

    #Assistència IA
    @staticmethod
    def _materialize(graph: TopologyGraph, ids: List[str]) -> Path:
        # Recupera els objectes Node complets a partir dels identificadors del camí
        nodes: List[Node] = [graph.get_node(nid) for nid in ids]  # type: ignore[misc]

        edges: List[Edge] = []
        total = 0.0

        # Construeix cada aresta del camí i acumula el pes total
        for u, v in zip(ids, ids[1:]):
            w = graph.edge_weight(u, v) or 0.0
            edges.append(Edge(from_node=u, to_node=v, weight=w))
            total += w

        return Path(nodes=nodes, edges=edges, total_weight=total)
    #Fi Assistència IA

    def find_best(
        self,
        graph: TopologyGraph,
        entry: str,
        target: str,
        key=lambda p: p.total_weight,
    ) -> Optional[Path]:
        """Retorna el camí òptim segons una funció de cost arbitrària.

        Útil per analitzar criteris no suportats per Dijkstra (p. ex.
        minimitzar risc màxim del camí, no la suma).
        """
        # Obté tots els camins possibles entre entry i target
        paths = self.find_all(graph, entry, target)

        # Si no existeix cap camí, retorna None
        if not paths:
            return None

        # Retorna el camí amb menor valor segons la funció de cost passada per paràmetre
        return min(paths, key=key)
