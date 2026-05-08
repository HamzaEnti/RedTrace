"""
Generació d'informes de RedTrace.

TODO: afegir suport per a múltiples formats (text, JSON).
"""

import json
from pathlib import Path

from engine.base import ReportGenerator
from engine.types import AnalysisReport


class TextReportGenerator(ReportGenerator):
    """Genera un informe en text pla."""

    def generate(self, report: AnalysisReport, output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "=" * 60,
            "REDTRACE — INFORME D'ANÀLISI",
            "=" * 60,
            f"Entry:  {report.entry}",
            f"Target: {report.target}",
            f"Salts:  {report.path.hops}",
            f"Cost:   {report.path.total_weight:.3f}",
            "",
            "Ruta:",
        ]
        for node in report.path.nodes:
            lines.append(f"  • {node.id} ({node.type}) — risc: {node.risk:.2f}")
        lines += ["", "IDS: " + report.ids_result.message]

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
