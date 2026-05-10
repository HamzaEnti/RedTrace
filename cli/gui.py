"""Interfície gràfica de RedTrace — v2: tabs i sidebar."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from engine.graph import TopologyGraph
from engine.route_strategy import SafestRoute, ShortestRoute
from scanner.parser import NetworkParser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedTrace")
        self.resize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Sidebar ──────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setSpacing(10)

        sb_layout.addWidget(QLabel("Topologia"))
        row_topo = QHBoxLayout()
        self.topo_path = QLineEdit("data/topology_mock.json")
        row_topo.addWidget(self.topo_path)
        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(28)
        btn_browse.clicked.connect(self._browse)
        row_topo.addWidget(btn_browse)
        sb_layout.addLayout(row_topo)

        sb_layout.addWidget(QLabel("Entry IP"))
        self.entry_ip = QLineEdit("192.168.1.1")
        sb_layout.addWidget(self.entry_ip)

        sb_layout.addWidget(QLabel("Target IP"))
        self.target_ip = QLineEdit("192.168.1.100")
        sb_layout.addWidget(self.target_ip)

        sb_layout.addWidget(QLabel("Estratègia"))
        self.rb_shortest = QRadioButton("Shortest")
        self.rb_safest = QRadioButton("Safest")
        self.rb_shortest.setChecked(True)
        grp = QButtonGroup(self)
        grp.addButton(self.rb_shortest)
        grp.addButton(self.rb_safest)
        sb_layout.addWidget(self.rb_shortest)
        sb_layout.addWidget(self.rb_safest)

        sb_layout.addSpacing(8)
        self.run_btn = QPushButton("▶  Analitzar")
        self.run_btn.clicked.connect(self._run)
        sb_layout.addWidget(self.run_btn)
        sb_layout.addStretch()

        root.addWidget(sidebar)

        # ── Main panel: tabs ──────────────────
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        self.tabs.addTab(self.output, "Resultat")

        # TODO: afegir tab de Graf
        placeholder = QLabel("Graf de xarxa — pròximament")
        placeholder.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignCenter)
        self.tabs.addTab(placeholder, "Graf")

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
