"""Parser del JSON de ShadowScan: produeix nodes/arestes tipificats."""

import json
from pathlib import Path as _PathLib
from typing import Dict, List, Tuple

from source.engine.types import Edge, Node
from source.scanner.normalizer import normalize


class NetworkParser:
    """Llegeix i tipifica el JSON de ShadowScan."""

    def __init__(self, json_path: str):
        # Guarda la ruta al fitxer JSON i inicialitza el diccionari de dades en brut
        self.json_path = json_path
        self._raw: Dict = {}

    def load(self) -> Tuple[List[Node], List[Edge], str, str]:
        # Obre i deserialitza el fitxer JSON amb codificació UTF-8
        with open(self.json_path, "r", encoding="utf-8") as f:
            self._raw = json.load(f)

        # Valida i normalitza l'estructura abans de tipificar
        self._raw = normalize(self._raw)

        # Construeix la llista de nodes tipificats a partir del JSON normalitzat
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

        # Construeix la llista d'arestes tipificades a partir del JSON normalitzat
        edges = [
            Edge(from_node=e["from"], to_node=e["to"], weight=e["weight"])
            for e in self._raw["edges"]
        ]

        # Retorna nodes, arestes, punt d'entrada i objectiu
        return nodes, edges, self._raw["entry_point"], self._raw["target"]

    #Assistència IA
    @property
    def metadata(self) -> Dict:
        # Retorna el bloc de metadades del JSON, o un diccionari buit si no existeix
        return self._raw.get("metadata", {})

    @staticmethod
    def exists(path: str) -> bool:
        # Comprova si el fitxer indicat existeix al sistema de fitxers
        return _PathLib(path).is_file()
    #Fi Assistència IA
