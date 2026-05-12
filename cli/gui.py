"""Interfície gràfica de RedTrace — v6: tabs de cicles i estadístiques."""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("QtAgg")
import networkx as nx
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QFrame,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QSpacerItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from engine.decision_tree import DecisionTreeRiskClassifier
from engine.dfs import CycleDetector
from engine.graph import TopologyGraph
from engine.ids_sim import IDSSimulator
from engine.risk import make_classifier
from engine.route_strategy import SafestRoute, ShortestRoute
from engine.types import AnalysisReport, Path as RTPath, RiskLevel
from scanner.parser import NetworkParser

COL_BG       = "#0E0E12"
COL_PANEL    = "#181821"
COL_CARD     = "#23232E"
COL_CARD_HOVER = "#2A2A36"
COL_BORDER   = "#2D2D3A"
COL_ACCENT   = "#E53935"
COL_ACCENT_DARK = "#B71C1C"
COL_TEXT     = "#ECEFF4"
COL_TEXT_DIM = "#7A8090"
COL_LOW      = "#43A047"
COL_MEDIUM   = "#FB8C00"
COL_CRITICAL = "#E53935"
COL_SUCCESS  = "#43A047"

LEVEL_COLOR = {
    RiskLevel.LOW: COL_LOW,
    RiskLevel.MEDIUM: COL_MEDIUM,
    RiskLevel.CRITICAL: COL_CRITICAL,
}

STYLESHEET = f"""
* {{ font-family: "Segoe UI", "SF Pro Display", "Inter", sans-serif; }}
QMainWindow, QWidget {{ background: {COL_BG}; color: {COL_TEXT}; }}
QFrame#header {{ background: {COL_PANEL}; border-bottom: 1px solid {COL_BORDER}; }}
QFrame#footer {{ background: {COL_PANEL}; border-top: 1px solid {COL_BORDER}; }}
QFrame#sidebar {{ background: {COL_PANEL}; border-radius: 10px; }}
QFrame#mainPanel {{ background: {COL_PANEL}; border-radius: 10px; }}
QFrame#separator {{ background: {COL_BORDER}; max-height: 1px; min-height: 1px; }}
QFrame#card {{ background: {COL_CARD}; border-radius: 8px; }}
QLineEdit {{
    background: {COL_CARD}; color: {COL_TEXT};
    border: 1px solid {COL_BORDER}; border-radius: 6px; padding: 5px 10px;
}}
QLineEdit:focus {{ border: 1px solid {COL_ACCENT}; }}
QPushButton#runBtn {{
    background: {COL_ACCENT}; color: white; border: none;
    border-radius: 6px; padding: 8px; font-size: 13px; font-weight: bold;
}}
QPushButton#runBtn:hover {{ background: {COL_ACCENT_DARK}; }}
QPushButton#browseBtn {{
    background: {COL_CARD}; color: {COL_TEXT_DIM};
    border: 1px solid {COL_BORDER}; border-radius: 6px; padding: 5px 10px;
}}
QRadioButton {{ color: {COL_TEXT}; spacing: 6px; }}
QTabWidget::pane {{ border: 1px solid {COL_BORDER}; background: {COL_PANEL}; border-radius: 6px; }}
QTabBar::tab {{
    background: {COL_CARD}; color: {COL_TEXT_DIM};
    padding: 7px 18px; border: none; font-size: 12px;
}}
QTabBar::tab:selected {{ color: {COL_TEXT}; border-bottom: 2px solid {COL_ACCENT}; }}
QTextEdit {{ background: {COL_CARD}; color: {COL_TEXT}; border: none; padding: 8px; }}
QScrollArea {{ border: none; background: transparent; }}
QLabel#brand {{ color: {COL_ACCENT}; font-size: 22px; font-weight: 800; }}
QLabel#tagline {{ color: {COL_TEXT_DIM}; font-size: 12px; }}
QLabel#sectionTitle {{ color: {COL_ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }}
QLabel#fieldLabel {{ color: {COL_TEXT_DIM}; font-size: 11px; }}
QLabel#statusOk  {{ color: {COL_TEXT_DIM}; font-size: 11px; }}
QLabel#statusErr {{ color: {COL_ACCENT}; font-size: 11px; font-weight: 600; }}
QLabel#statValue {{ color: {COL_TEXT}; font-size: 22px; font-weight: 700; }}
QLabel#statLabel {{ color: {COL_TEXT_DIM}; font-size: 10px; }}
"""


class NetworkCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self._fig = Figure(facecolor=COL_CARD)
        super().__init__(self._fig)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(COL_CARD)

    def draw_graph(self, graph: TopologyGraph,
                   attack_path: Optional[List[str]] = None,
                   classifications: Optional[Dict] = None):
        self._ax.clear()
        self._ax.set_facecolor(COL_CARD)
        g = graph.raw
        if not g.number_of_nodes():
            self.draw()
            return
        pos = nx.spring_layout(g, seed=42)
        node_colors = [
            LEVEL_COLOR.get((classifications or {}).get(nid, RiskLevel.LOW), "#555566")
            for nid in g.nodes
        ]
        nx.draw_networkx_nodes(g, pos, ax=self._ax, node_color=node_colors, node_size=750)
        nx.draw_networkx_labels(g, pos, ax=self._ax, font_color="white", font_size=7)
        nx.draw_networkx_edges(g, pos, ax=self._ax, edge_color="#555", arrows=True, arrowsize=15, alpha=0.5)
        if attack_path and len(attack_path) > 1:
            nx.draw_networkx_edges(g, pos,
                edgelist=list(zip(attack_path[:-1], attack_path[1:])),
                ax=self._ax, edge_color=COL_ACCENT, width=3, arrows=True, arrowsize=20)
        self._ax.axis("off")
        self._fig.tight_layout()
        self.draw()


def _lbl(text, name=None):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    return l


def _stat_card(value, label):
    card = QFrame()
    card.setObjectName("card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 14, 16, 14)
    lv = _lbl(str(value), "statValue")
    lv.setAlignment(Qt.AlignCenter)
    ll = _lbl(label, "statLabel")
    ll.setAlignment(Qt.AlignCenter)
    lay.addWidget(lv)
    lay.addWidget(ll)
    return card, lv


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedTrace")
        self.resize(1200, 760)
        self._graph: Optional[TopologyGraph] = None

        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QVBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        hdr = QHBoxLayout(header)
        hdr.setContentsMargins(20, 0, 20, 0)
        hdr.addWidget(_lbl("REDTRACE", "brand"))
        hdr.addSpacing(12)
        hdr.addWidget(_lbl("Lateral Movement Simulator", "tagline"))
        hdr.addStretch()
        self.lbl_status = _lbl("Sense topologia carregada", "statusOk")
        hdr.addWidget(self.lbl_status)
        root.addWidget(header)

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(12, 12, 12, 12)
        body_lay.setSpacing(10)
        root.addWidget(body, stretch=1)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(16, 16, 16, 16)
        sb.setSpacing(8)
        sb.addWidget(_lbl("TOPOLOGIA", "sectionTitle"))
        row_t = QHBoxLayout()
        self.topo_path = QLineEdit("data/topology_mock.json")
        row_t.addWidget(self.topo_path)
        btn_b = QPushButton("…")
        btn_b.setObjectName("browseBtn")
        btn_b.setFixedWidth(32)
        btn_b.clicked.connect(self._browse)
        row_t.addWidget(btn_b)
        sb.addLayout(row_t)
        sb.addWidget(_lbl("ENTRY IP", "sectionTitle"))
        self.entry_ip = QLineEdit("192.168.1.1")
        sb.addWidget(self.entry_ip)
        sb.addWidget(_lbl("TARGET IP", "sectionTitle"))
        self.target_ip = QLineEdit("192.168.1.100")
        sb.addWidget(self.target_ip)
        sb.addWidget(_lbl("ESTRATÈGIA", "sectionTitle"))
        self.rb_shortest = QRadioButton("Shortest path")
        self.rb_safest   = QRadioButton("Safest path")
        self.rb_shortest.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_shortest)
        grp.addButton(self.rb_safest)
        sb.addWidget(self.rb_shortest)
        sb.addWidget(self.rb_safest)
        sb.addSpacing(12)
        self.run_btn = QPushButton("▶  Analitzar")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.clicked.connect(self._run)
        sb.addWidget(self.run_btn)
        sb.addStretch()
        body_lay.addWidget(sidebar)

        # Main tabs
        main_panel = QFrame()
        main_panel.setObjectName("mainPanel")
        mp = QVBoxLayout(main_panel)
        mp.setContentsMargins(8, 8, 8, 8)
        self.tabs = QTabWidget()
        mp.addWidget(self.tabs)
        body_lay.addWidget(main_panel, stretch=1)

        self._net_canvas = NetworkCanvas()
        self.tabs.addTab(self._net_canvas, "Graf")

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        self.tabs.addTab(self.output, "Informe")

        # Tab Cicles
        self.cycles_view = QTextEdit()
        self.cycles_view.setReadOnly(True)
        self.tabs.addTab(self.cycles_view, "Cicles")

        # Tab Estadístiques
        stats_w = QWidget()
        stats_lay = QGridLayout(stats_w)
        stats_lay.setContentsMargins(16, 16, 16, 16)
        stats_lay.setSpacing(10)
        card_nodes, self.sv_nodes   = _stat_card("—", "Nodes")
        card_edges, self.sv_edges   = _stat_card("—", "Arestes")
        card_hops,  self.sv_hops    = _stat_card("—", "Salts ruta")
        card_risk,  self.sv_risk    = _stat_card("—", "Risc mitjà")
        card_cyc,   self.sv_cycles  = _stat_card("—", "Cicles detectats")
        card_ids,   self.sv_ids     = _stat_card("—", "Firmes IDS activ.")
        for i, card in enumerate([card_nodes, card_edges, card_hops,
                                   card_risk, card_cyc, card_ids]):
            stats_lay.addWidget(card, i // 3, i % 3)
        self.tabs.addTab(stats_w, "Estadístiques")

        # Footer IDS
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(40)
        ftr = QHBoxLayout(footer)
        ftr.setContentsMargins(20, 0, 20, 0)
        lbl_ids_lbl = _lbl("IDS")
        lbl_ids_lbl.setStyleSheet(f"color:{COL_ACCENT};font-weight:700;font-size:11px;")
        ftr.addWidget(lbl_ids_lbl)
        ftr.addSpacing(8)
        self.lbl_ids = _lbl("En espera d'anàlisi…", "statusOk")
        ftr.addWidget(self.lbl_ids)
        ftr.addStretch()
        root.addWidget(footer)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Obre topologia", "", "JSON (*.json)")
        if path:
            self.topo_path.setText(path)

    def _run(self):
        topo = self.topo_path.text()
        entry = self.entry_ip.text().strip()
        target = self.target_ip.text().strip()
        if not Path(topo).is_file():
            self.lbl_status.setText(f"Error: {topo}")
            return
        try:
            parser = NetworkParser(topo)
            nodes, edges, _, _ = parser.load()
            graph = TopologyGraph.build if hasattr(TopologyGraph, "build") else TopologyGraph()
            if callable(getattr(TopologyGraph, "build", None)):
                graph = TopologyGraph().build(nodes, edges)
            else:
                graph = TopologyGraph()
                for n in nodes: graph.add_node(n)
                for e in edges: graph.add_edge(e)
            self._graph = graph
            self.lbl_status.setText(f"{graph.num_nodes()} nodes · {graph.num_edges()} arestes")

            classifier = DecisionTreeRiskClassifier()
            classifier.annotate_nodes(nodes)
            classifications = {n.id: n.risk_level for n in nodes}

            strategy = SafestRoute() if self.rb_safest.isChecked() else ShortestRoute()
            path = strategy.select(graph, entry, target)

            detector = CycleDetector(graph)
            cycles = detector.find_cycles()

            ids = IDSSimulator()
            ids_result = ids.evaluate(path) if path else None

            # Update IDS footer
            if ids_result and ids_result.detected:
                self.lbl_ids.setText(f"⚠ ALERTA — {ids_result.message}")
                self.lbl_ids.setObjectName("statusErr")
            else:
                self.lbl_ids.setText("✔ Cap firma activada")
                self.lbl_ids.setObjectName("statusOk")

            # Update cycles tab
            if cycles:
                self.cycles_view.setText("\n".join(
                    f"Cicle {i+1}: {' → '.join(c)}" for i, c in enumerate(cycles)
                ))
            else:
                self.cycles_view.setText("Cap cicle detectat.")

            # Update stats
            self.sv_nodes.setText(str(graph.num_nodes()))
            self.sv_edges.setText(str(graph.num_edges()))
            self.sv_cycles.setText(str(len(cycles)))
            self.sv_ids.setText(str(len(ids_result.triggered_signatures) if ids_result else 0))

            if path:
                node_ids = [n.id for n in path.nodes]
                self._net_canvas.draw_graph(graph, node_ids, classifications)
                recs = []
                for nid in node_ids:
                    clf = make_classifier(classifications.get(nid, RiskLevel.LOW))
                    for r in clf.get_recommendations():
                        recs.append(f"  • {r}")
                lines = [
                    f"Ruta trobada ({path.hops} salts, cost {path.total_weight:.3f})",
                    "─" * 50,
                    " → ".join(node_ids),
                    f"Risc mitjà: {path.avg_risk:.2f}",
                    "", "Recomanacions:",
                ] + recs
                self.output.setText("\n".join(lines))
                self.sv_hops.setText(str(path.hops))
                self.sv_risk.setText(f"{path.avg_risk:.2f}")
            else:
                self._net_canvas.draw_graph(graph, classifications=classifications)
                self.output.setText("No s'ha trobat cap ruta.")
                self.sv_hops.setText("—")
                self.sv_risk.setText("—")
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
