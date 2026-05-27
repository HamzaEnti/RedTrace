"""Tests unitaris per al NetworkParser."""

import json
from pathlib import Path

import pytest

from scanner.normalizer import TopologyValidationError, normalize
from scanner.parser import NetworkParser

MOCK_TOPOLOGY = Path("data") / "topology_mock.json"


def test_load_mock_topology():
    parser = NetworkParser(str(MOCK_TOPOLOGY))
    nodes, edges, entry, target = parser.load()

    assert len(nodes) == 9
    assert len(edges) == 18
    assert entry == "192.168.1.1"
    assert target == "192.168.1.100"
    assert all(0.0 <= n.risk <= 1.0 for n in nodes)
    assert all(0.0 < e.weight <= 1.0 for e in edges)


def test_node_fields_typed():
    parser = NetworkParser(str(MOCK_TOPOLOGY))
    nodes, _, _, _ = parser.load()
    n = nodes[0]
    assert isinstance(n.ports, list)
    assert all(isinstance(p, int) for p in n.ports)
    assert isinstance(n.services, dict)
    assert isinstance(n.risk, float)


def test_normalize_missing_top_level_field():
    with pytest.raises(TopologyValidationError):
        normalize({"nodes": [], "edges": [], "entry_point": "a"})


def test_normalize_missing_node_field():
    with pytest.raises(TopologyValidationError):
        normalize(
            {
                "nodes": [{"id": "a", "type": "router"}],
                "edges": [],
                "entry_point": "a",
                "target": "a",
            }
        )


def test_normalize_unknown_entry():
    with pytest.raises(TopologyValidationError):
        normalize(
            {
                "nodes": [
                    {
                        "id": "a",
                        "type": "router",
                        "ports": [22],
                        "services": {"22": "ssh"},
                        "risk": 0.1,
                    }
                ],
                "edges": [],
                "entry_point": "ghost",
                "target": "a",
            }
        )


def test_metadata_passthrough(tmp_path):
    raw = json.loads(MOCK_TOPOLOGY.read_text(encoding="utf-8"))
    target = tmp_path / "topo.json"
    target.write_text(json.dumps(raw), encoding="utf-8")
    parser = NetworkParser(str(target))
    parser.load()
    assert parser.metadata.get("generated_by") == "ShadowScan"
