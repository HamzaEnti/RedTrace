"""
Tests addicionals per a les estratègies de ruta (Shortest, Safest, FewestHops)
"""

import pytest

from engine.graph import TopologyGraph
from engine.route_strategy import FewestHopsRoute, SafestRoute, ShortestRoute
from engine.types import Edge, Node, RiskLevel


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
