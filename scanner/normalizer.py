"""Normalitzador de camps del JSON de ShadowScan.

Garanteix que els camps opcionals existeixin i que els tipus siguin correctes
abans que el parser els consumeixi.
"""

from typing import Dict


def normalize(raw: Dict) -> Dict:
    """Normalitza un diccionari ShadowScan in-place i el retorna."""
    for node in raw.get("nodes", []):
        node.setdefault("type", "unknown")
        node.setdefault("ports", [])
        node.setdefault("services", {})
        node.setdefault("risk", 0.0)
        node["risk"] = float(node["risk"])
        node["ports"] = [int(p) for p in node["ports"]]
        # Converteix claus de serveis a string per consistència
        node["services"] = {str(k): str(v) for k, v in node["services"].items()}

    for edge in raw.get("edges", []):
        edge["weight"] = float(edge.get("weight", 1.0))

    return raw
