from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


@dataclass
class Node:
    id: str
    type: str
    ports: List[int]
    services: Dict[str, str]
    risk: float
    risk_level: RiskLevel = RiskLevel.LOW


@dataclass
class Edge:
    from_node: str
    to_node: str
    weight: float


@dataclass
class Path:
    nodes: List[Node]
    edges: List[Edge]
    total_weight: float

    @property
    def hops(self) -> int:
        return len(self.edges)

    @property
    def avg_risk(self) -> float:
        if not self.nodes:
            return 0.0
        return sum(n.risk for n in self.nodes) / len(self.nodes)


@dataclass
class IDSResult:
    detected: bool
    triggered_signatures: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class AnalysisReport:
    entry: str
    target: str
    path: Path
    cycles: List[List[str]]
    ids_result: IDSResult
    node_classifications: Dict[str, RiskLevel]
