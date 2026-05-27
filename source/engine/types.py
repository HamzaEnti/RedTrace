"""Estructures de dades centrals del motor d'anàlisi

Defineix els tipus immutables tipats que viatgen entre els mòduls (scanner →
engine → report): nodes, arestes, rutes i informes agregats
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class RiskLevel(Enum):
    """Nivells discrets de risc assignats als nodes per l'arbre de decisió"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


@dataclass
class Node:
    """Representa un host de la topologia amb els seus ports, serveis i risc associat"""
    id: str
    type: str
    ports: List[int]
    services: Dict[str, str]
    risk: float
    risk_level: RiskLevel = RiskLevel.LOW


@dataclass
class Edge:
    """Connexió dirigida entre dos nodes amb un pes que representa el cost d'explotació"""
    from_node: str
    to_node: str
    weight: float


@dataclass
class Path:
    """Ruta d'atac: seqüència ordenada de nodes i arestes amb el pes total acumulat"""
    nodes: List[Node]
    edges: List[Edge]
    total_weight: float

    @property
    def hops(self) -> int:
        """Nombre de salts (arestes) que componen la ruta"""
        return len(self.edges)

    @property
    def avg_risk(self) -> float:
        """Risc mitjà dels nodes que formen la ruta"""
        if not self.nodes:
            return 0.0
        return sum(n.risk for n in self.nodes) / len(self.nodes)


@dataclass
class IDSResult:
    """Resultat de l'avaluació d'una ruta contra el conjunt de firmes IDS"""
    detected: bool
    triggered_signatures: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class AnalysisReport:
    """Informe agregat d'una anàlisi: ruta, cicles detectats, alertes IDS i classificacions per node"""
    entry: str
    target: str
    path: Path
    cycles: List[List[str]]
    ids_result: IDSResult
    node_classifications: Dict[str, RiskLevel]