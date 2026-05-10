"""Tests unitaris per al NetworkParser."""

import json
import tempfile
from pathlib import Path

import pytest

from scanner.parser import NetworkParser


SAMPLE = {
    "metadata": {"generated_by": "ShadowScan", "version": "1.0-mock"},
    "nodes": [
        {"id": "10.0.0.1", "type": "router", "ports": [22, 80],
         "services": {"22": "ssh", "80": "http"}, "risk": 0.3},
        {"id": "10.0.0.2", "type": "server", "ports": [443],
         "services": {"443": "https"}, "risk": 0.6},
    ],
    "edges": [{"from": "10.0.0.1", "to": "10.0.0.2", "weight": 0.5}],
    "entry_point": "10.0.0.1",
    "target": "10.0.0.2",
}


@pytest.fixture
def topo_file(tmp_path):
    p = tmp_path / "topo.json"
    p.write_text(json.dumps(SAMPLE))
    return str(p)


def test_load_nodes(topo_file):
    parser = NetworkParser(topo_file)
    nodes, edges, entry, target = parser.load()
    assert len(nodes) == 2
    assert nodes[0].id == "10.0.0.1"


def test_load_edges(topo_file):
    parser = NetworkParser(topo_file)
    nodes, edges, _, _ = parser.load()
    assert len(edges) == 1
    assert edges[0].weight == 0.5


# TODO: afegir tests de camps opcionals i JSON malformat
