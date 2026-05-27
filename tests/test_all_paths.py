"""Tests per a AllPathsFinder (backtracking)."""

import pytest

from engine.all_paths import AllPathsFinder
from engine.graph import TopologyGraph
from engine.types import Edge, Node


def _g(nodes, edges):
    # Crea una llista de nodes amb valors per defecte (tipus, ports, serveis i risc)
    ns = [Node(id=n, type="x", ports=[], services={}, risk=0.1) for n in nodes]

    # Crea una llista d'arestes a partir de tuples (origen, destí, pes)
    es = [Edge(from_node=u, to_node=v, weight=w) for u, v, w in edges]

    # Construeix i retorna el graf de topologia amb els nodes i arestes creats
    return TopologyGraph().build(ns, es)


def test_single_direct_edge():
    # Graf mínim: dos nodes connectats per una única aresta directa
    g = _g(["A", "B"], [("A", "B", 0.5)])
    paths = AllPathsFinder().find_all(g, "A", "B")

    # Només hi ha d'haver un camí possible
    assert len(paths) == 1

    # El camí ha de passar exactament per A i B, en aquest ordre
    assert [n.id for n in paths[0].nodes] == ["A", "B"]


def test_multiple_paths():
    # Graf amb múltiples camins possibles entre A i D:
    # A -> B -> D, A -> C -> D, A -> B -> C -> D
    g = _g(
        ["A", "B", "C", "D"],
        [
            ("A", "B", 0.2), ("A", "C", 0.3),
            ("B", "C", 0.1), ("B", "D", 0.5),
            ("C", "D", 0.4),
        ],
    )
    paths = AllPathsFinder().find_all(g, "A", "D")

    # Converteix cada camí a una cadena de text per facilitar la comparació
    sequences = sorted([" ".join(n.id for n in p.nodes) for p in paths])

    # Verifica que s'han trobat exactament els tres camins esperats
    assert sequences == sorted(["A B D", "A B C D", "A C D"])


def test_no_path_returns_empty():
    # Graf on C és un node aïllat: no hi ha cap aresta que hi arribi des d'A
    g = _g(["A", "B", "C"], [("A", "B", 0.1)])  # C isolated

    # Si no existeix cap camí, el resultat ha de ser una llista buida
    assert AllPathsFinder().find_all(g, "A", "C") == []


def test_blocked_nodes_pruned():
    # Graf amb dos camins cap a D: un passant per B i un altre per C
    g = _g(
        ["A", "B", "C", "D"],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.1), ("C", "D", 0.1)],
    )

    # Bloqueja el node B: el backtracking no ha de explorar camins que el travessin
    paths = AllPathsFinder(blocked_nodes={"B"}).find_all(g, "A", "D")

    # Només ha de quedar el camí que passa per C
    assert len(paths) == 1
    assert [n.id for n in paths[0].nodes] == ["A", "C", "D"]
