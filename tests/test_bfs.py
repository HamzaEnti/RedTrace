"""
Tests per a BFSFinder.
"""

import pytest

from engine.bfs import BFSFinder
from engine.graph import TopologyGraph
from engine.types import Edge, Node


def _g(nodes, edges):
    ns = [Node(id=n, type="x", ports=[], services={}, risk=0.1) for n in nodes]
    es = [Edge(from_node=u, to_node=v, weight=w) for u, v, w in edges]
    return TopologyGraph().build(ns, es)


def test_bfs_returns_fewest_hops_even_if_higher_weight():
    # A -> B -> D (2 hops, pes 1.8) vs A -> C -> E -> D (3 hops, pes 0.3)
    g = _g(
        ["A", "B", "C", "D", "E"],
        [
            ("A", "B", 0.9), ("B", "D", 0.9),
            ("A", "C", 0.1), ("C", "E", 0.1), ("E", "D", 0.1),
        ],
    )
    path = BFSFinder().find_path(g, "A", "D")
    assert [n.id for n in path.nodes] == ["A", "B", "D"]


def test_bfs_no_path():
    g = _g(["A", "B"], [])
    assert BFSFinder().find_path(g, "A", "B") is None


def test_bfs_entry_equals_target():
    g = _g(["A"], [])
    path = BFSFinder().find_path(g, "A", "A")
    assert path is not None
    assert len(path.nodes) == 1
    assert path.hops == 0


def test_bfs_with_blocked():
    g = _g(
        ["A", "B", "C", "D"],
        [("A", "B", 0.1), ("B", "D", 0.1), ("A", "C", 0.1), ("C", "D", 0.1)],
    )
    path = BFSFinder(blocked_nodes={"B"}).find_path(g, "A", "D")
    assert [n.id for n in path.nodes] == ["A", "C", "D"]
