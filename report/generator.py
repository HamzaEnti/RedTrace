"""Generadors d'informe (JSON i text) basats en cua d'esdeveniments.

L'estructura interna és una 'deque' (cua FIFO) d'esdeveniments més un 'dict'
de metadades exactament l'estructura assignada al mòdul.
"""

# Importacions estàndard de Python: gestió de fitxers JSON, cues, rutes i tipus
import json
from abc import abstractmethod
from collections import deque
from pathlib import Path as _PathLib
from typing import Any, Deque, Dict, List

# Importem les dependències internes del projecte RedTrace
from engine.base import ReportGenerator
from engine.risk import make_classifier
from engine.types import AnalysisReport


# Classe base privada per als dos generadors d'informe
class _ReportBase(ReportGenerator):
    def __init__(self):
        # Inicialitzem la cua buida i el diccionari de metadades buit.
        # La deque ens permet afegir eventos tant al principi com al final
        # en O(1), tot i que aquí sempre els afegim al final (cua FIFO).
        self._events: Deque[Dict[str, Any]] = deque()
        self._meta: Dict[str, Any] = {}

    # Cada subclasse ha d'implementar com escriu l'informe a disc
    @abstractmethod
    def generate(self, report: AnalysisReport, output_path: str) -> None: ...

    def _populate(self, report: AnalysisReport) -> None:
        # Netegem les estructures per si aquest generador es reutilitza
        # en múltiples crides (no volem dades de l'execució anterior)
        self._events.clear()
        self._meta.clear()

        # Extraiem el camí calculat de l'informe per llegibilitat
        path = report.path

        # Omplim el diccionari de metadades globals de la sessió d'anàlisi
        self._meta = {
            "entry": report.entry,          # node d'inici de l'atac simulat
            "target": report.target,        # node objectiu final
            "total_weight": round(path.total_weight, 4),  # cost total de la ruta
            "hops": path.hops,              # nombre de salts (arestes) de la ruta
            "avg_risk": round(path.avg_risk, 4),  # risc mitjà dels nodes travessats
            "ids_detected": report.ids_result.detected,  # ha disparat l'IDS?
        }

        # Bloc 1: un event per cada node de la ruta d'atac.
        # Iterem pels nodes en ordre de visita (de l'entrada al target).
        for i, node in enumerate(path.nodes):
            # Obtenim el classificador de risc específic per al nivell d'aquest node.
            # make_classifier retorna LOW/MEDIUM/CRITICAL amb les recomanacions associades.
            classifier = make_classifier(node.risk_level)

            # Afegim a la cua un event que representa el pas i-èssim de la ruta
            self._events.append(
                {
                    "step": i,
                    "node_id": node.id,
                    "type": node.type,           # p. ex. "server", "workstation"
                    "risk_score": node.risk,     # valor numèric de 0.0 a 1.0
                    "risk_level": node.risk_level.value,  # etiqueta LOW/MEDIUM/CRITICAL
                    "ports": list(node.ports),   # convertim el set a llista per a JSON
                    "services": dict(node.services),  # serveis exposats al node
                    "recommendations": classifier.get_recommendations(),  # mesures de mitigació
                }
            )

        # Bloc 2: event de resum de cicles detectats al graf.
        # Els cicles els detecta DFS; aquí només els serialitzem a la cua.
        self._events.append(
            {
                "phase": "cycles_detected",
                "count": len(report.cycles),
                "cycles": [list(c) for c in report.cycles],  # conjunts → llistes (serialitzables)
            }
        )

        # Bloc 3: event amb el resultat de la simulació IDS.
        # L'IDS comprova si la seqüència de nodes/ports dispara alguna firma.
        self._events.append(
            {
                "phase": "ids_evaluation",
                "detected": report.ids_result.detected,
                "triggered_signatures": list(report.ids_result.triggered_signatures),
                "message": report.ids_result.message,  # explicació llegible de la decisió
            }
        )


# Generador d'informe en format JSON
class JSONReport(_ReportBase):
    def generate(self, report: AnalysisReport, output_path: str) -> None:
        # Primer omplim les estructures internes amb les dades de l'informe
        self._populate(report)

        # Construïm el payload final que anirà al fitxer JSON.
        # Convertim la deque a llista perquè json.dump no sap serialitzar deques.
        payload = {
            "metadata": self._meta,
            "events": list(self._events),
            # Afegim la classificació de tots els nodes del graf (no només els de la ruta)
            # per facilitar la visualització del mapa de risc complet
            "node_classifications": {
                nid: lvl.value for nid, lvl in report.node_classifications.items()
            },
        }

        # Ens assegurem que el directori de sortida existeix (el creem si cal)
        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Escrivim el JSON amb indentació de 2 espais per llegibilitat humana.
        # ensure_ascii=False permet caràcters UTF-8 (accents, etc.) sense escapar.
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


# Generador d'informe en format text pla
class TextReport(_ReportBase):
    def generate(self, report: AnalysisReport, output_path: str) -> None:
        # Omplim les estructures internes igual que al generador JSON
        self._populate(report)

        # Construïm el contingut línia a línia en una llista de strings.
        # Unir-les al final amb "\n".join() és més eficient que concatenar strings.
        lines: List[str] = []

        # Capçalera de l'informe
        lines.append("=" * 70)
        lines.append("INFORME REDTRACE — ANÀLISI DE MOVIMENT LATERAL")
        lines.append("=" * 70)
        lines.append(f"Entrada : {self._meta['entry']}")
        lines.append(f"Objectiu: {self._meta['target']}")
        lines.append(
            f"Pes total: {self._meta['total_weight']}  |  "
            f"Salts: {self._meta['hops']}  |  "
            f"Risc mitjà: {self._meta['avg_risk']}"
        )
        lines.append("")
        lines.append("-- Ruta d'atac --")

        # Secció de nodes: iterem sobre la deque buscant events de pas.
        # Només processem els events que representen un node de la ruta
        # (reconeixibles perquè tenen la clau "step" en comptes de "phase").
        for ev in self._events:
            if "step" in ev:
                # Línia principal: índex, ID del node, tipus i puntuació de risc
                lines.append(
                    f"  [{ev['step']}] {ev['node_id']} "
                    f"({ev['type']}) — risc {ev['risk_score']:.2f} "
                    f"· classificació {ev['risk_level']}"
                )
                # Afegim les recomanacions de seguretat indentades per cada node
                for rec in ev["recommendations"]:
                    lines.append(f"      → {rec}")

        lines.append("")

        # Secció de cicles i IDS: iterem buscant events de "phase".
        # Els events de fase es diferencien dels de node pel camp "phase".
        for ev in self._events:
            if ev.get("phase") == "cycles_detected":
                lines.append(f"-- Cicles detectats: {ev['count']} --")
                for c in ev["cycles"]:
                    # Mostrem cada cicle com una seqüència de nodes separats per fletxes
                    lines.append("  · " + " → ".join(c))
                lines.append("")

            elif ev.get("phase") == "ids_evaluation":
                lines.append("-- Avaluació IDS --")
                status = "DETECTAT" if ev["detected"] else "NO DETECTAT"
                lines.append(f"  Resultat: {status}")
                if ev["triggered_signatures"]:
                    lines.append("  Firmes activades:")
                    for s in ev["triggered_signatures"]:
                        lines.append(f"    · {s}")
                lines.append(f"  Missatge: {ev['message']}")

        lines.append("=" * 70)

        # Escriptura al disc
        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            # Unim totes les línies amb salts de línia i escrivim d'una sola vegada
            f.write("\n".join(lines))
