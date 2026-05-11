"""Interfície gràfica de RedTrace — v4: visualització del graf."""

import sys
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("QtAgg")
import networkx as nx
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QRadioButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from engine.decision_tree import DecisionTreeRiskClassifier
from engine.dfs import CycleDetector
from engine.graph import TopologyGraph
from engine.ids_sim import IDSSimulator
from engine.risk import make_classifier
from engine.route_strategy import SafestRoute, ShortestRoute
from engine.types import AnalysisReport, RiskLevel
from scanner.parser import NetworkParser

COL_BG       = "#0E0E12"
COL_PANEL    = "#181821"
COL_CARD     = "#23232E"
COL_BORDER   = "#2D2D3A"
COL_ACCENT   = "#E53935"
COL_TEXT     = "#ECEFF4"
COL_TEXT_DIM = "#7A8090"
COL_LOW      = "#43A047"
COL_MEDIUM   = "#FB8C00"
COL_CRITICAL = "#E53935"

LEVEL_COLOR = {
    RiskLevel.LOW: COL_LOW,
    RiskLevel.MEDIUM: COL_MEDIUM,
    RiskLevel.CRITICAL: COL_CRITICAL,
}

STYLESHEET = f"""
* {{ font-family: "Segoe UI", sans-serif; }}
QMainWindow, QWidget {{ background: {COL_BG}; color: {COL_TEXT}; }}
QFrame#sidebar {{ background: {COL_PANEL}; border-radius: 8px; }}
QFrame#mainPanel {{ background: {COL_PANEL}; border-radius: 8px; }}
QLineEdit {{
    background: {COL_CARD}; color: {COL_TEXT};
    border: 1px solid {COL_BORDER}; border-radius: 4px; padding: 4px 8px;
}}
QPushButton {{
    background: {COL_ACCENT}; color: white; border: none;
    border-radius: 4px; padding: 6px 12px; font-weight: bold;
}}
QPushButton:hover {{ background: #C62828; }}
QRadioButton {{ color: {COL_TEXT}; }}
QTabWidget::pane {{ border: 1px solid {COL_BORDER}; background: {COL_PANEL}; }}
QTabBar::tab {{
    background: {COL_CARD}; color: {COL_TEXT_DIM}; padding: 6px 16px; border: none;
}}
QTabBar::tab:selected {{ color: {COL_TEXT}; border-bottom: 2px solid {COL_ACCENT}; }}
QTextEdit {{ background: {COL_CARD}; color: {COL_TEXT}; border: none; padding: 6px; }}
QLabel {{ color: {COL_TEXT_DIM}; font-size: 11px; }}
"""


class NetworkCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self._fig = Figure(facecolor=COL_CARD)
        super().__init__(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(COL_CARD)

    def draw_graph(self, graph: TopologyGraph,
                   attack_path: Optional[List[str]] = None,
                   classifications=None):
        self._ax.clear()
        self._ax.set_facecolor(COL_CARD)
        g = graph.raw
        if g.number_of_nodes() == 0:
            self.draw()
            return

        pos = nx.spring_layout(g, seed=42)
        node_colors = []
        for nid in g.nodes:
            node = graph.get_node(nid)
            if classifications and node:
                lvl = classifications.get(nid, RiskLevel.LOW)
                node_colors.append(LEVEL_COLOR[lvl])
            else:
                node_colors.append("#555566")

        nx.draw_networkx_nodes(g, pos, ax=self._ax,
                               node_color=node_colors, node_size=700, alpha=0.9)
        nx.draw_networkx_labels(g, pos, ax=self._ax,
                                font_color="white", font_size=7)
        nx.draw_networkx_edges(g, pos, ax=self._ax,
                               edge_color="#555", arrows=True,
                               arrowsize=15, alpha=0.6)

        if attack_path and len(attack_path) > 1:
            path_edges = list(zip(attack_path[:-1], attack_path[1:]))
            nx.draw_networkx_edges(g, pos, edgelist=path_edges, ax=self._ax,
                                   edge_color=COL_ACCENT, width=3,
                                   arrows=True, arrowsize=20)

        self._ax.axis("off")
        self._fig.tight_layout()
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedTrace")
        self.resize(1150, 740)
        self._graph: Optional[TopologyGraph] = None
        self._report: Optional[AnalysisReport] = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Sidebar ─────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(14, 14, 14, 14)
        sb.setSpacing(10)

        lbl_brand = QLabel("REDTRACE")
        lbl_brand.setStyleSheet(f"color:{COL_ACCENT};font-size:18px;font-weight:800;")
        sb.addWidget(lbl_brand)
        lbl_tag = QLabel("Lateral Movement Simulator")
        sb.addWidget(lbl_tag)

        sb.addWidget(QLabel("TOPOLOGIA"))
        row_t = QHBoxLayout()
        self.topo_path = QLineEdit("data/topology_mock.json")
        row_t.addWidget(self.topo_path)
        btn_b = QPushButton("…")
        btn_b.setFixedWidth(28)
        btn_b.setStyleSheet(f"background:{COL_CARD};color:{COL_TEXT};border:1px solid {COL_BORDER};font-weight:normal;")
        btn_b.clicked.connect(self._browse)
        row_t.addWidget(btn_b)
        sb.addLayout(row_t)

        sb.addWidget(QLabel("ENTRY IP"))
        self.entry_ip = QLineEdit("192.168.1.1")
        sb.addWidget(self.entry_ip)

        sb.addWidget(QLabel("TARGET IP"))
        self.target_ip = QLineEdit("192.168.1.100")
        sb.addWidget(self.target_ip)

        sb.addWidget(QLabel("ESTRATÈGIA"))
        self.rb_shortest = QRadioButton("Shortest path")
        self.rb_safest   = QRadioButton("Safest path")
        self.rb_shortest.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_shortest)
        grp.addButton(self.rb_safest)
        sb.addWidget(self.rb_shortest)
        sb.addWidget(self.rb_safest)

        sb.addSpacing(8)
        self.run_btn = QPushButton("▶  Analitzar")
        self.run_btn.clicked.connect(self._run)
        sb.addWidget(self.run_btn)
        sb.addStretch()
        root.addWidget(sidebar)

        # ── Main panel ──────────────────────────────────────────
        main_panel = QFrame()
        main_panel.setObjectName("mainPanel")
        mp = QVBoxLayout(main_panel)
        mp.setContentsMargins(8, 8, 8, 8)
        self.tabs = QTabWidget()
        mp.addWidget(self.tabs)
        root.addWidget(main_panel)

        # Tab Graf
        self._net_canvas = NetworkCanvas()
        self.tabs.addTab(self._net_canvas, "Graf")

        # Tab Resultat
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        self.tabs.addTab(self.output, "Resultat")

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Obre topologia", "", "JSON (*.json)")
        if path:
            self.topo_path.setText(path)

    def _run(self):
        topo = self.topo_path.text()
        entry = self.entry_ip.text().strip()
        target = self.target_ip.text().strip()
        if not Path(topo).is_file():
            self.output.setText(f"[ERROR] Fitxer no trobat: {topo}")
            return
        try:
            parser = NetworkParser(topo)
            nodes, edges, _, _ = parser.load()
            graph = TopologyGraph()
            for n in nodes:
                graph.add_node(n)
            for e in edges:
                graph.add_edge(e)
            self._graph = graph

            classifier = DecisionTreeRiskClassifier()
            classifier.annotate_nodes(nodes)
            classifications = {n.id: n.risk_level for n in nodes}

            strategy = SafestRoute() if self.rb_safest.isChecked() else ShortestRoute()
            path = strategy.select(graph, entry, target)

            ids = IDSSimulator()
            ids_result = ids.evaluate(path) if path else None

            if path:
                node_ids = [n.id for n in path.nodes]
                self._net_canvas.draw_graph(graph, node_ids, classifications)
                lines = [
                    f"Ruta trobada ({path.hops} salts, cost {path.total_weight:.3f})",
                    "─" * 40,
                    " → ".join(node_ids),
                    f"Risc mitjà: {path.avg_risk:.2f}",
                ]
                if ids_result:
                    lines += ["", f"IDS: {ids_result.message}"]
                self.output.setText("\n".join(lines))
            else:
                self._net_canvas.draw_graph(graph, classifications=classifications)
                self.output.setText("No s'ha trobat cap ruta.")
            self.tabs.setCurrentIndex(0)
        except Exception as ex:
            self.output.setText(f"[ERROR] {ex}")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
