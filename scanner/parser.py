"""Parser del JSON de ShadowScan: produeix nodes/arestes tipificats."""

import json
from pathlib import Path as _PathLib
from typing import Dict, List, Tuple

from engine.types import Edge, Node
from scanner.normalizer import normalize


class NetworkParser:
    """Llegeix i tipifica el JSON de ShadowScan."""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self._raw: Dict = {}

    def load(self) -> Tuple[List[Node], List[Edge], str, str]:
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)
        self._raw = normalize(self._raw)

        nodes = [
            Node(
                id=n["id"],
                type=n["type"],
                ports=n["ports"],
                services=n["services"],
                risk=n["risk"],
            )
            for n in self._raw["nodes"]
        ]
        edges = [
            Edge(from_node=e["from"], to_node=e["to"], weight=e["weight"])
            for e in self._raw["edges"]
        ]
        return nodes, edges, self._raw["entry_point"], self._raw["target"]

    @property
    def metadata(self) -> Dict:
        return self._raw.get("metadata", {})

    @staticmethod
    def exists(path: str) -> bool:
        return _PathLib(path).is_file()
