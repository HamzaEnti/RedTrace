"""
Tests addicionals per a les estratègies de ruta (Shortest, Safest, FewestHops)
"""

import pytest

from source.engine.graph import TopologyGraph
from source.engine.route_strategy import FewestHopsRoute, SafestRoute, ShortestRoute
from source.engine.types import Edge, Node, RiskLevel

"""Ajuda amb ús d'IA: inici"""
def _node(nid: str, risk: float = 0.1) -> Node:
    n = Node(id=nid, type="x", ports=[], services={}, risk=risk)
    if risk >= 0.80:
        n.risk_level = RiskLevel.CRITICAL
    elif risk >= 0.40:
        n.risk_level = RiskLevel.MEDIUM
    else:
        n.risk_level = RiskLevel.LOW
    return n


def _g(nodes, edges):
    return TopologyGraph().build(nodes, [Edge(*e) for e in edges])
"""Ajuda amb ús d'IA: fi"""
"""Ajuda amb ús d'IA: Com en el test_bfs.py, m'he ajudat per guiarme durant la creació de la base e idea de les seguents funcions."""
def test_shortest_picks_lowest_weight_sum():
    g = _g(
        [_node("A"), _node("B"), _node("C"), _node("D")],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.9), ("C", "D", 0.9)],
    )
    p = ShortestRoute().select(g, "A", "D")
    assert [n.id for n in p.nodes] == ["A", "B", "D"]


def test_safest_avoids_critical_node():
    g = _g(
        [_node("A"), _node("B", 0.95), _node("C"), _node("D")],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.4), ("C", "D", 0.4)],
    )
    p = SafestRoute().select(g, "A", "D")
    assert "B" not in [n.id for n in p.nodes]


def test_fewest_hops_prefers_short_path_over_lighter():
    g = _g(
        [_node("A"), _node("B"), _node("C"), _node("D"), _node("E")],
        [
            ("A", "B", 0.9), ("B", "D", 0.9),
            ("A", "C", 0.1), ("C", "E", 0.1), ("E", "D", 0.1),
        ],
    )
    p = FewestHopsRoute().select(g, "A", "D")
    assert [n.id for n in p.nodes] == ["A", "B", "D"]

def test_safest_respects_custom_threshold():
    g = _g(
        [_node("A"), _node("B", 0.5), _node("C"), _node("D")],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.9), ("C", "D", 0.9)],
    )
    # Threshold 0.4 -> B (0.5) queda bloquejat
    p = SafestRoute(threshold=0.4).select(g, "A", "D")
    assert "B" not in [n.id for n in p.nodes]


def test_fewest_hops_with_avoid_critical():
    g = _g(
        [_node("A"), _node("B", 0.95), _node("C"), _node("D")],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.1), ("C", "D", 0.1)],
    )
    p = FewestHopsRoute(avoid_critical=True).select(g, "A", "D")
    assert "B" not in [n.id for n in p.nodes]


def test_no_path_returns_none():
    g = _g([_node("A"), _node("B")], [])
    assert ShortestRoute().select(g, "A", "B") is None
    assert SafestRoute().select(g, "A", "B") is None
    assert FewestHopsRoute().select(g, "A", "B") is None