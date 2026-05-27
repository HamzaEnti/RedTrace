from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

""" TYPE_CHECKING és False en temps d'execució, les importacions aquí són només per anàlisi estàtic (evita imports circulars)"""
if TYPE_CHECKING:
    from source.engine.types import AnalysisReport, IDSResult, Node, Path, RiskLevel


class AttackPathFinder(ABC):
    """Class base abstracta per als algoritmes que descobreixen attack paths"""

    @abstractmethod
    def find_path(self, graph, entry: str, target: str) -> Optional["Path"]:
        """Troba un attack path desde un node d'entrada fins a un node objectiu"""
        ...


class RouteStrategy(ABC):
    """Classe base abstracta per a la selecció de ruta."""

    @abstractmethod
    def select(self, graph, entry: str, target: str) -> Optional["Path"]:
        """Selecciona una ruta òptima desde l'entrada fins a l'objectiu segons una estratègia específica"""
        ...


class RiskClassifier(ABC):
    """Classe base abstracta per a la classificació del risc dels resultats de l'anàlisi."""

    @property
    @abstractmethod
    def level(self) -> "RiskLevel":
        """Nivell de risc assignat per aquest classificador (LOW, MEDIUM, HIGH, CRITICAL)."""
        ...

    @abstractmethod
    def get_recommendations(self) -> List[str]:
        """Retorna una llista de recomanacions de mitigació basades en el nivell de risc"""
        ...

    @abstractmethod
    def get_color(self) -> str:
        """Retorna un codi de color associat al nivell de risc (informes)"""
        ...


class ReportGenerator(ABC):
    """Classe base abstracta per a la generació d'informes en diferents formats"""

    @abstractmethod
    def generate(self, report: "AnalysisReport", output_path: str) -> None:
        """Genera i escriu un informe"""
        ...