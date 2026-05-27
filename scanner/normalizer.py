"""Normalitza i valida l'estructura JSON rebuda de ShadowScan."""

from typing import Any, Dict


REQUIRED_TOP_LEVEL = ("nodes", "edges", "entry_point", "target")
REQUIRED_NODE_FIELDS = ("id", "type", "ports", "services", "risk")
REQUIRED_EDGE_FIELDS = ("from", "to", "weight")


class TopologyValidationError(ValueError):
    pass


def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    for key in REQUIRED_TOP_LEVEL:
        if key not in raw:
            raise TopologyValidationError(f"Falta el camp obligatori '{key}' al JSON")

    for i, node in enumerate(raw["nodes"]):
        for field in REQUIRED_NODE_FIELDS:
            if field not in node:
                raise TopologyValidationError(
                    f"Node #{i}: falta el camp '{field}'"
                )
        node["ports"] = [int(p) for p in node["ports"]]
        node["services"] = {str(k): str(v) for k, v in node["services"].items()}
        node["risk"] = float(node["risk"])

    for i, edge in enumerate(raw["edges"]):
        for field in REQUIRED_EDGE_FIELDS:
            if field not in edge:
                raise TopologyValidationError(
                    f"Aresta #{i}: falta el camp '{field}'"
                )
        edge["weight"] = float(edge["weight"])

    node_ids = {n["id"] for n in raw["nodes"]}
    if raw["entry_point"] not in node_ids:
        raise TopologyValidationError(
            f"entry_point '{raw['entry_point']}' no existeix als nodes"
        )
    if raw["target"] not in node_ids:
        raise TopologyValidationError(
            f"target '{raw['target']}' no existeix als nodes"
        )

    return raw
