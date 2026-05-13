"""Generadors d'informe (JSON i text) basats en cua d'esdeveniments.

L'estructura interna és una `deque` (cua FIFO) d'esdeveniments més un `dict`
de metadades — exactament l'estructura assignada al mòdul (R2 enunciat).
"""

import json
from abc import abstractmethod
from collections import deque
from pathlib import Path as _PathLib
from typing import Any, Deque, Dict, List

from engine.base import ReportGenerator
from engine.risk import make_classifier
from engine.types import AnalysisReport


class _ReportBase(ReportGenerator):
    """Arrel comuna que omple cua d'esdeveniments + dict de metadades."""

    def __init__(self):
        self._events: Deque[Dict[str, Any]] = deque()
        self._meta: Dict[str, Any] = {}

    @abstractmethod
    def generate(self, report: AnalysisReport, output_path: str) -> None: ...

    def _populate(self, report: AnalysisReport) -> None:
        self._events.clear()
        self._meta.clear()

        path = report.path
        self._meta = {
            "entry": report.entry,
            "target": report.target,
            "total_weight": round(path.total_weight, 4),
            "hops": path.hops,
            "avg_risk": round(path.avg_risk, 4),
            "ids_detected": report.ids_result.detected,
        }

        for i, node in enumerate(path.nodes):
            classifier = make_classifier(node.risk_level)
            self._events.append(
                {
                    "step": i,
                    "node_id": node.id,
                    "type": node.type,
                    "risk_score": node.risk,
                    "risk_level": node.risk_level.value,
                    "ports": list(node.ports),
                    "services": dict(node.services),
                    "recommendations": classifier.get_recommendations(),
                }
            )

        self._events.append(
            {
                "phase": "cycles_detected",
                "count": len(report.cycles),
                "cycles": [list(c) for c in report.cycles],
            }
        )

        self._events.append(
            {
                "phase": "ids_evaluation",
                "detected": report.ids_result.detected,
                "triggered_signatures": list(report.ids_result.triggered_signatures),
                "message": report.ids_result.message,
            }
        )


class JSONReport(_ReportBase):
    def generate(self, report: AnalysisReport, output_path: str) -> None:
        self._populate(report)
        payload = {
            "metadata": self._meta,
            "events": list(self._events),
            "node_classifications": {
                nid: lvl.value for nid, lvl in report.node_classifications.items()
            },
        }
        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


class TextReport(_ReportBase):
    def generate(self, report: AnalysisReport, output_path: str) -> None:
        self._populate(report)
        lines: List[str] = []
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
        for ev in self._events:
            if "step" in ev:
                lines.append(
                    f"  [{ev['step']}] {ev['node_id']} "
                    f"({ev['type']}) — risc {ev['risk_score']:.2f} "
                    f"· classificació {ev['risk_level']}"
                )
                for rec in ev["recommendations"]:
                    lines.append(f"      → {rec}")

        lines.append("")
        for ev in self._events:
            if ev.get("phase") == "cycles_detected":
                lines.append(f"-- Cicles detectats: {ev['count']} --")
                for c in ev["cycles"]:
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

        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
