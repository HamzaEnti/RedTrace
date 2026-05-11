"""Interfície gràfica de RedTrace — v3: tema fosc."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QRadioButton, QSizePolicy, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from engine.graph import TopologyGraph
from engine.route_strategy import SafestRoute, ShortestRoute
from scanner.parser import NetworkParser

COL_BG      = "#0E0E12"
COL_PANEL   = "#181821"
COL_CARD    = "#23232E"
COL_BORDER  = "#2D2D3A"
COL_ACCENT  = "#E53935"
COL_TEXT    = "#ECEFF4"
COL_TEXT_DIM = "#7A8090"

STYLESHEET = f"""
* {{ font-family: "Segoe UI", sans-serif; }}
QMainWindow, QWidget {{ background: {COL_BG}; color: {COL_TEXT}; }}
QFrame#sidebar {{ background: {COL_PANEL}; border-radius: 8px; }}
QFrame#mainPanel {{ background: {COL_PANEL}; border-radius: 8px; }}
QLineEdit {{
    background: {COL_CARD}; color: {COL_TEXT};
    border: 1px solid {COL_BORDER}; border-radius: 4px;
    padding: 4px 8px;
}}
QPushButton {{
    background: {COL_ACCENT}; color: white; border: none;
    border-radius: 4px; padding: 6px 12px; font-weight: bold;
}}
QPushButton:hover {{ background: #C62828; }}
QRadioButton {{ color: {COL_TEXT}; }}
QTabWidget::pane {{ border: 1px solid {COL_BORDER}; background: {COL_PANEL}; }}
QTabBar::tab {{
    background: {COL_CARD}; color: {COL_TEXT_DIM};
    padding: 6px 16px; border: none;
}}
QTabBar::tab:selected {{ color: {COL_TEXT}; border-bottom: 2px solid {COL_ACCENT}; }}
QTextEdit {{ background: {COL_CARD}; color: {COL_TEXT}; border: none; }}
QLabel {{ color: {COL_TEXT_DIM}; font-size: 11px; }}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedTrace")
        self.resize(1100, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Sidebar ──────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(14, 14, 14, 14)
        sb.setSpacing(10)

        lbl_brand = QLabel("REDTRACE")
        lbl_brand.setStyleSheet(f"color:{COL_ACCENT};font-size:18px;font-weight:800;")
        sb.addWidget(lbl_brand)
        sb.addWidget(QLabel("Topologia"))

        row_topo = QHBoxLayout()
        self.topo_path = QLineEdit("data/topology_mock.json")
        row_topo.addWidget(self.topo_path)
        btn_b = QPushButton("…")
        btn_b.setFixedWidth(28)
        btn_b.setStyleSheet(f"background:{COL_CARD};color:{COL_TEXT};border:1px solid {COL_BORDER};")
        btn_b.clicked.connect(self._browse)
        row_topo.addWidget(btn_b)
        sb.addLayout(row_topo)

        sb.addWidget(QLabel("Entry IP"))
        self.entry_ip = QLineEdit("192.168.1.1")
        sb.addWidget(self.entry_ip)

        sb.addWidget(QLabel("Target IP"))
        self.target_ip = QLineEdit("192.168.1.100")
        sb.addWidget(self.target_ip)

        sb.addWidget(QLabel("Estratègia"))
        self.rb_shortest = QRadioButton("Shortest")
        self.rb_safest   = QRadioButton("Safest")
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

        # ── Main: tabs ──────────────────────
        main_panel = QFrame()
        main_panel.setObjectName("mainPanel")
        mp = QVBoxLayout(main_panel)
        mp.setContentsMargins(8, 8, 8, 8)
        self.tabs = QTabWidget()
        mp.addWidget(self.tabs)
        root.addWidget(main_panel)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        self.tabs.addTab(self.output, "Resultat")

        # Graf placeholder
        self._fig = Figure(facecolor=COL_CARD)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self.tabs.addTab(self._canvas, "Graf")

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
            strategy = SafestRoute() if self.rb_safest.isChecked() else ShortestRoute()
            path = strategy.select(graph, entry, target)
            if path:
                lines = [f"Ruta trobada ({path.hops} salts, cost {path.total_weight:.3f}):"]
                lines.append(" → ".join(n.id for n in path.nodes))
                lines.append(f"Risc mitjà: {path.avg_risk:.2f}")
                self.output.setText("\n".join(lines))
            else:
                self.output.setText("No s'ha trobat cap ruta.")
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
