"""Generador de topologies sintètiques per a tests i benchmarks.

Produeix un diccionari amb el mateix esquema que un JSON de ShadowScan
(`nodes`, `edges`, `entry_point`, `target`, `metadata`) per poder reutilitzar
`scanner.parser.NetworkParser` i `scanner.normalizer.normalize`.

Complexitat
-----------
Generar un graf de n nodes amb densitat d ∈ [0, 1]:
    O(n^2) en l'enumeració d'arestes candidates (parells dirigits).
    O(n) per crear els nodes.
Total: O(n^2).
"""

from __future__ import annotations

import random
from typing import Dict, List


_NODE_TYPES = ("router", "server", "workstation", "fileserver", "database")
_PORTS_BY_TYPE = {
    "router": [22, 53, 80, 443],
    "server": [22, 80, 443, 3306],
    "workstation": [445, 139, 3389],
    "fileserver": [445, 139, 21, 2049],
    "database": [22, 3306, 5432],
}
_SERVICES = {
    22: "ssh", 23: "telnet", 21: "ftp", 53: "dns", 80: "http", 139: "netbios",
    443: "https", 445: "smb", 2049: "nfs", 3306: "mysql", 3389: "rdp",
    5432: "postgresql", 161: "snmp",
}


def generate_topology(
    n_nodes: int,
    edge_density: float = 0.25,
    critical_ratio: float = 0.2,
    seed: int | None = None,
) -> Dict:
    """Genera una topologia sintètica amb n_nodes hosts.

    Parameters
    ----------
    n_nodes : int
        Nombre de nodes (mínim 2).
    edge_density : float
        Probabilitat d'existència d'una aresta dirigida entre dos nodes
        diferents (0.0 = mínim connex, 1.0 = graf complet).
    critical_ratio : float
        Fracció aproximada de nodes amb risc >= 0.80.
    seed : int | None
        Llavor per a reproducibilitat.

    Returns
    -------
    dict compatible amb scanner.parser.NetworkParser.
    """
    if n_nodes < 2:
        raise ValueError("n_nodes ha de ser >= 2")
    if not 0.0 <= edge_density <= 1.0:
        raise ValueError("edge_density fora de [0, 1]")
    if not 0.0 <= critical_ratio <= 1.0:
        raise ValueError("critical_ratio fora de [0, 1]")

    rng = random.Random(seed)

    nodes: List[Dict] = []
    for i in range(n_nodes):
        ntype = rng.choice(_NODE_TYPES)
        ports = list(_PORTS_BY_TYPE[ntype])
        # Inyecta ports d'alt risc segons critical_ratio
        if rng.random() < critical_ratio:
            ports.append(rng.choice([23, 21, 3389]))
            risk = round(rng.uniform(0.80, 0.98), 2)
        elif rng.random() < 0.4:
            risk = round(rng.uniform(0.40, 0.70), 2)
        else:
            risk = round(rng.uniform(0.10, 0.35), 2)

        nodes.append({
            "id": f"10.0.{i // 256}.{i % 256}",
            "type": ntype,
            "ports": ports,
            "services": {str(p): _SERVICES.get(p, "unknown") for p in ports},
            "risk": risk,
        })

    # Garanteix un camí Hamiltonià mínim entry -> ... -> target
    edges: List[Dict] = []
    for i in range(n_nodes - 1):
        edges.append({
            "from": nodes[i]["id"],
            "to": nodes[i + 1]["id"],
            "weight": round(rng.uniform(0.20, 0.90), 2),
        })

    # Arestes addicionals segons densitat
    existing = {(e["from"], e["to"]) for e in edges}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i == j:
                continue
            pair = (nodes[i]["id"], nodes[j]["id"])
            if pair in existing:
                continue
            if rng.random() < edge_density:
                edges.append({
                    "from": pair[0],
                    "to": pair[1],
                    "weight": round(rng.uniform(0.15, 0.95), 2),
                })
                existing.add(pair)

    return {
        "metadata": {
            "generated_by": "ShadowScan",
            "synthetic": True,
            "version": "1.0-synth",
            "hosts_active": n_nodes,
        },
        "nodes": nodes,
        "edges": edges,
        "entry_point": nodes[0]["id"],
        "target": nodes[-1]["id"],
    }


def save_topology(topo: Dict, path: str) -> None:
    """Escriu el diccionari de topologia a disc com a JSON."""
    import json
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topo, f, indent=2)
