"""Tests per al Dijkstra modificat (camí mínim ponderat)."""

from source.engine.dijkstra import DijkstraFinder
from source.engine.graph import TopologyGraph
from source.engine.types import Edge, Node


def _node(nid: str, risk: float = 0.5) -> Node:
    return Node(id=nid, type="server", ports=[22], services={"22": "ssh"}, risk=risk)


def _build(nodes, edges) -> TopologyGraph:
    return TopologyGraph().build(nodes, edges)


def test_simple_two_node_path():
    g = _build([_node("a"), _node("b")], [Edge("a", "b", 0.5)])
    p = DijkstraFinder().find_path(g, "a", "b")
    assert p is not None
    assert [n.id for n in p.nodes] == ["a", "b"]
    assert p.total_weight == 0.5


def test_chooses_lowest_weight_path():
    nodes = [_node(x) for x in ("a", "b", "c", "d")]
    edges = [
        Edge("a", "b", 0.9),
        Edge("a", "c", 0.1),
        Edge("b", "d", 0.1),
        Edge("c", "d", 0.1),
    ]
    g = _build(nodes, edges)
    p = DijkstraFinder().find_path(g, "a", "d")
    assert p is not None
    assert [n.id for n in p.nodes] == ["a", "c", "d"]
    assert abs(p.total_weight - 0.2) < 1e-9


def test_no_path_returns_none():
    nodes = [_node(x) for x in ("a", "b", "c")]
    edges = [Edge("a", "b", 0.5)]
    g = _build(nodes, edges)
    assert DijkstraFinder().find_path(g, "a", "c") is None


def test_unknown_endpoints_return_none():
    g = _build([_node("a"), _node("b")], [Edge("a", "b", 0.3)])
    assert DijkstraFinder().find_path(g, "ghost", "b") is None
    assert DijkstraFinder().find_path(g, "a", "ghost") is None


def test_blocked_nodes_avoided():
    nodes = [_node(x) for x in ("a", "b", "c", "d")]
    edges = [
        Edge("a", "b", 0.1),
        Edge("b", "d", 0.1),
        Edge("a", "c", 0.5),
        Edge("c", "d", 0.5),
    ]
    g = _build(nodes, edges)
    p = DijkstraFinder(blocked_nodes={"b"}).find_path(g, "a", "d")
    assert p is not None
    assert [n.id for n in p.nodes] == ["a", "c", "d"]
    assert abs(p.total_weight - 1.0) < 1e-9


def test_path_hops_and_avg_risk():
    nodes = [
        _node("a", risk=0.2),
        _node("b", risk=0.8),
        _node("c", risk=0.5),
    ]
    edges = [Edge("a", "b", 0.3), Edge("b", "c", 0.4)]
    g = _build(nodes, edges)
    p = DijkstraFinder().find_path(g, "a", "c")
    assert p.hops == 2
    assert abs(p.avg_risk - 0.5) < 1e-9
