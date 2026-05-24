"""Simulador d'IDS basat en taula hash de firmes

El diccionari signatures és la taula hash. Cada firma és una
funció que avalua una Path
"""

from typing import Callable, Dict, Tuple

from engine.types import IDSResult, Path, RiskLevel

# Llindars de detecció de les firmes
HOPS_THRESHOLD = 4
TELNET_PORT = 23
CRITICAL_CONSECUTIVE_THRESHOLD = 2
HIGH_AVG_RISK_THRESHOLD = 0.70

SignatureFn = Callable[[Path], Tuple[bool, str]]


class IDSSimulator:
    """Avalua una ruta contra un conjunt de firmes conegudes"""
    def __init__(self):
        self.signatures: Dict[str, SignatureFn] = {
            "long_path": self._sig_long_path,
            "telnet_in_path": self._sig_telnet_in_path,
            "consecutive_critical": self._sig_consecutive_critical,
            "high_avg_risk": self._sig_high_avg_risk,
        }

    def evaluate(self, path: Path) -> IDSResult:
        """Executa totes les firmes sobre la ruta i retorna el resultat agregat"""
        triggered = []
        messages = []
        for name, check in self.signatures.items():
            detected, msg = check(path)
            if detected:
                triggered.append(name)
                messages.append(msg)

        return IDSResult(
            detected=bool(triggered),
            triggered_signatures=triggered,
            message="; ".join(messages) if messages else "Cap firma activada",
        )

    @staticmethod
    def _sig_long_path(path: Path) -> Tuple[bool, str]:
        """Detecta rutes amb més salts dels permesos"""
        if path.hops > HOPS_THRESHOLD:
            return True, f"Ruta amb {path.hops} salts (> {HOPS_THRESHOLD})"
        return False, ""

    @staticmethod
    def _sig_telnet_in_path(path: Path) -> Tuple[bool, str]:
        """Detecta si algun node de la ruta té el port Telnet obert"""
        for n in path.nodes:
            if TELNET_PORT in n.ports:
                return True, f"Node {n.id} amb Telnet (port 23) a la ruta"
        return False, ""

    @staticmethod
    def _sig_consecutive_critical(path: Path) -> Tuple[bool, str]:
        """Detecta seqüències de nodes CRITICAL consecutius per sobre del llindar"""
        run = 0
        max_run = 0
        for n in path.nodes:
            if n.risk_level == RiskLevel.CRITICAL:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
        if max_run >= CRITICAL_CONSECUTIVE_THRESHOLD:
            return (
                True,
                f"{max_run} nodes CRITICAL consecutius "
                f"(>= {CRITICAL_CONSECUTIVE_THRESHOLD})",
            )
        return False, ""

    @staticmethod
    def _sig_high_avg_risk(path: Path) -> Tuple[bool, str]:
        """Detecta rutes amb un risc mitjà acumulat superior al llindar"""
        if path.avg_risk > HIGH_AVG_RISK_THRESHOLD:
            return (
                True,
                f"Risc mitjà acumulat {path.avg_risk:.2f} "
                f"(> {HIGH_AVG_RISK_THRESHOLD:.2f})",
            )
        return False, ""