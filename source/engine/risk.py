"""Subclasses polimòrfiques de RiskClassifier (LOW/MEDIUM/CRITICAL)

Cada nivell encapsula color de visualització. La classificació la fa l'arbre de
decisió a decision_tree.py; aquestes classes només encapsulen la resposta
"""

from typing import Dict, List, Type

from engine.base import RiskClassifier
from engine.types import RiskLevel


class LowRisk(RiskClassifier):
    """Classificador de risc baix"""

    @property
    def level(self) -> RiskLevel:
        return RiskLevel.LOW

    def get_recommendations(self) -> List[str]:
        """Retorna recomanacions de manteniment preventiu"""
        return [
            "Mantenir actualitzacions periòdiques del sistema operatiu",
            "Monitoritzar logs setmanalment",
            "Verificar la configuració del firewall localment",
        ]

    def get_color(self) -> str:
        """Retorna el color verd del risc baix"""
        return "#4CAF50"


class MediumRisk(RiskClassifier):
    """Classificador de risc mitjà"""

    @property
    def level(self) -> RiskLevel:
        return RiskLevel.MEDIUM

    def get_recommendations(self) -> List[str]:
        """Retorna recomanacions de restricció i segmentació de xarxa"""
        return [
            "Restringir l'accés per IP origen quan sigui possible",
            "Implementar autenticació de doble factor als serveis exposats",
            "Revisar els logs diàriament i alertar sobre patrons sospitosos",
            "Aplicar segmentació de xarxa per limitar el moviment lateral",
        ]

    def get_color(self) -> str:
        """Retorna el color taronja del risc mitjà"""
        return "#FF9800"


class CriticalRisk(RiskClassifier):
    """Classificador de risc crític"""

    @property
    def level(self) -> RiskLevel:
        return RiskLevel.CRITICAL

    def get_recommendations(self) -> List[str]:
        """Retorna recomanacions d'actuació immediata per contenir la amenaça"""
        return [
            "AÏLLAR immediatament en una VLAN segregada",
            "Auditoria completa de seguretat i revisió de privilegis",
            "Desactivar serveis insegurs (Telnet, SMBv1, FTP en clar)",
            "Desplegar EDR i monitoritzar 24/7",
            "Forçar rotació de credencials administratives",
        ]

    def get_color(self) -> str:
        """Retorna el color vermell del risc crític."""
        return "#F44336"

CLASSIFIER_BY_LEVEL: Dict[RiskLevel, Type[RiskClassifier]] = {
    RiskLevel.LOW: LowRisk,
    RiskLevel.MEDIUM: MediumRisk,
    RiskLevel.CRITICAL: CriticalRisk,
}


def make_classifier(level: RiskLevel) -> RiskClassifier:
    """Instancia i retorna el classificador corresponent al nivell de risc donat"""
    return CLASSIFIER_BY_LEVEL[level]()