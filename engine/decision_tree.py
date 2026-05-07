"""Arbre de decisió ID3 per classificar el risc dels nodes.

TODO: implementar entrenament complet des del CSV.
"""

from pathlib import Path as _PathLib
from engine.base import RiskClassifier
from engine.types import Node, RiskLevel

DEFAULT_DATASET_PATH = _PathLib("data") / "risk_dataset.csv"


class DecisionTreeRiskClassifier:
    """Embolcalla un DecisionTreeClassifier de scikit-learn. WIP."""

    def __init__(self, dataset_path: _PathLib = DEFAULT_DATASET_PATH):
        self.dataset_path = dataset_path
        self._trained: bool = False

    def ensure_trained(self) -> None:
        """TODO: carregar CSV i entrenar el model ID3."""
        raise NotImplementedError("Entrenament pendent d'implementació")

    def classify(self, node: Node) -> RiskLevel:
        """TODO: extreure features i predir."""
        raise NotImplementedError       
