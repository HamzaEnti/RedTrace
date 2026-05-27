"""Normalitza i valida l'estructura JSON rebuda de ShadowScan."""

from typing import Any, Dict

# Camps obligatoris que ha de tenir el JSON d'entrada al nivell arrel
REQUIRED_TOP_LEVEL = ("nodes", "edges", "entry_point", "target")

# Camps obligatoris que ha de tenir cada node
REQUIRED_NODE_FIELDS = ("id", "type", "ports", "services", "risk")

# Camps obligatoris que ha de tenir cada aresta
REQUIRED_EDGE_FIELDS = ("from", "to", "weight")


class TopologyValidationError(ValueError):
    pass


def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:

    # Comprova que tots els camps d'alt nivell són presents al JSON
    for key in REQUIRED_TOP_LEVEL:
        if key not in raw:
            raise TopologyValidationError(f"Falta el camp obligatori '{key}' al JSON")

    for i, node in enumerate(raw["nodes"]):
        # Comprova que cada node té tots els camps obligatoris
        for field in REQUIRED_NODE_FIELDS:
            if field not in node:
                raise TopologyValidationError(
                    f"Node #{i}: falta el camp '{field}'"
                )

        # Normalitza els tipus de cada camp del node
        node["ports"] = [int(p) for p in node["ports"]]
        node["services"] = {str(k): str(v) for k, v in node["services"].items()}
        node["risk"] = float(node["risk"])

    for i, edge in enumerate(raw["edges"]):
        # Comprova que cada aresta té tots els camps obligatoris
        for field in REQUIRED_EDGE_FIELDS:
            if field not in edge:
                raise TopologyValidationError(
                    f"Aresta #{i}: falta el camp '{field}'"
                )

        # Normalitza el pes de l'aresta a float
        edge["weight"] = float(edge["weight"])

    #Assistència IA
    # Construeix el conjunt d'ids de nodes per fer les validacions finals
    node_ids = {n["id"] for n in raw["nodes"]}

    # Comprova que entry_point fa referència a un node existent
    if raw["entry_point"] not in node_ids:
        raise TopologyValidationError(
            f"entry_point '{raw['entry_point']}' no existeix als nodes"
        )

    # Comprova que target fa referència a un node existent
    if raw["target"] not in node_ids:
        raise TopologyValidationError(
            f"target '{raw['target']}' no existeix als nodes"
        )
    #Fi Assistència IA

    return raw
