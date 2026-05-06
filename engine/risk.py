"""Subclasses polimòrfiques de RiskClassifier (LOW/MEDIUM/CRITICAL).

Cada nivell encapsula color de visualització. Les recomanacions
s'ampliaran en iteracions posteriors.
"""

from typing import Dict, List, Type

from engine.base import RiskClassifier
from engine.types import RiskLevel


class LowRisk(RiskClassifier):
    @property
    def level(self) -> RiskLevel:
        return RiskLevel.LOW

    def get_recommendations(self) -> List[str]:
        return ["Mantenir actualitzacions periòdiques del sistema operatiu"]

    def get_color(self) -> str:
        return"#4CAF50"


class MediumRisk(RiskClassifier):
    @property
    def level(self) -> RiskLevel:
        return RiskLevel.MEDIUM

    def get_recommendations(self) -> List[str]:
        return ["Restringir l'accés per IP origen quan sigui possible"]

    def get_color(self) -> str:
        return "#FF9800"


class CriticalRisk(RiskClassifier):
    @property
    def level(self) -> RiskLevel:
        return RiskLevel.CRITICAL

    def get_recommendations(self) -> List[str]:
        return ["AÏLLAR immediatament en una VLAN segregada"]

    def get_color(self) -> str:
        return "#F44336"

CLASSIFIER_BY_LEVEL: Dict[RiskLevel, Type[RiskClassifier]] = {
    RiskLevel.LOW: LowRisk,
    RiskLevel.MEDIUM: MediumRisk,
    RiskLevel.CRITICAL: CriticalRisk,
}


def make_classifier(level: RiskLevel) -> RiskClassifier:
    return CLASSIFIER_BY_LEVEL[level]()