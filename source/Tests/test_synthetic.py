"""Tests per al generador de topologies sintètiques."""

import pytest

from source.scanner.normalizer import normalize
from source.scanner.synthetic import generate_topology


def test_basic_sizes():
    # Genera una topologia amb 20 nodes i una llavor fixa per garantir reproductibilitat
    topo = generate_topology(n_nodes=20, seed=1)

    # Comprova que el nombre de nodes generat és exactament el sol·licitat
    assert len(topo["nodes"]) == 20

    # El punt d'entrada ha de ser el primer node de la llista
    assert topo["entry_point"] == topo["nodes"][0]["id"]

    # L'objectiu ha de ser l'últim node de la llista
    assert topo["target"] == topo["nodes"][-1]["id"]


def test_reproducible_with_seed():
    # Genera dues topologies amb els mateixos paràmetres i la mateixa llavor
    a = generate_topology(n_nodes=15, edge_density=0.2, seed=42)
    b = generate_topology(n_nodes=15, edge_density=0.2, seed=42)

    # Les dues topologies han de ser idèntiques: la llavor garanteix determinisme
    assert a == b


def test_density_zero_gives_minimum_hamiltonian_chain():
    # Amb densitat zero no s'afegeixen arestes extra, només la cadena hamiltoniana mínima
    topo = generate_topology(n_nodes=10, edge_density=0.0, seed=7)

    # Cadena mínima entry -> ... -> target: exactament n-1 arestes
    assert len(topo["edges"]) == 9


def test_passes_normalizer():
    # Genera una topologia prou gran i la passa pel normalitzador
    topo = generate_topology(n_nodes=30, seed=11)
    normalized = normalize(topo)

    # Després de normalitzar, el punt d'entrada ha de seguir sent un node vàlid
    assert normalized["entry_point"] in {n["id"] for n in normalized["nodes"]}
