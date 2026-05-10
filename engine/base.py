from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.types import AnalysisReport, IDSResult, Node, Path, RiskLevel


class AttackPathFinder(ABC):
    @abstractmethod
    def find_path(self, graph, entry: str, target: str) -> Optional["Path"]:
        ...


class RouteStrategy(ABC):
    @abstractmethod
    def select(self, graph, entry: str, target: str) -> Optional["Path"]:
        ...


class RiskClassifier(ABC):
    @property
    @abstractmethod
    def level(self) -> "RiskLevel":
        ...

    @abstractmethod
    def get_recommendations(self) -> List[str]:
        ...

    @abstractmethod
    def get_color(self) -> str:
        ...


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, report: "AnalysisReport", output_path: str) -> None:
        ...
