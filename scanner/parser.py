"""Parser del JSON de ShadowScan: produeix nodes/arestes tipificats."""

import json
from typing import Dict, List, Tuple

from engine.types import Edge, Node


class NetworkParser:
    """Llegeix i tipifica el JSON de ShadowScan."""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self._raw: Dict = {}

    def load(self) -> Tuple[List[Node], List[Edge], str, str]:
        """Llegeix el fitxer JSON i retorna nodes, arestes i punts entry/target.

        TODO: implementar parsing complet dels camps normalitzats.
        """
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)

        # WIP: retorna llistes buides fins que normalizer estigui llest
        return [], [], "", ""

    @property
    def metadata(self) -> Dict:
        return self._raw.get("metadata", {})

    @staticmethod
    def exists(path: str) -> bool:
        from pathlib import Path as _PathLib
        return _PathLib(path).is_file()
