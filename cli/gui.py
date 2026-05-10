"""Interfície gràfica de RedTrace — versió inicial.

Finestra bàsica amb camps d'entrada i botó d'execució.
"""

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine.graph import TopologyGraph
from engine.route_strategy import ShortestRoute
from scanner.parser import NetworkParser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RedTrace")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        # Topology file
        row_topo = QHBoxLayout()
        row_topo.addWidget(QLabel("Topologia:"))
        self.topo_path = QLineEdit("data/topology_mock.json")
        row_topo.addWidget(self.topo_path)
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(32)
        btn_browse.clicked.connect(self._browse)
        row_topo.addWidget(btn_browse)
        root.addLayout(row_topo)

        # Entry / Target IPs
        row_ips = QHBoxLayout()
        row_ips.addWidget(QLabel("Entry IP:"))
        self.entry_ip = QLineEdit("192.168.1.1")
        row_ips.addWidget(self.entry_ip)
        row_ips.addWidget(QLabel("Target IP:"))
        self.target_ip = QLineEdit("192.168.1.100")
        row_ips.addWidget(self.target_ip)
        root.addLayout(row_ips)

        # Run button
        self.run_btn = QPushButton("▶  Analitzar")
        self.run_btn.clicked.connect(self._run)
        root.addWidget(self.run_btn)

        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        root.addWidget(self.output)

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
            route = ShortestRoute()
            path = route.select(graph, entry, target)
            if path:
                result = f"Ruta trobada ({path.hops} salts, cost {path.total_weight:.3f}):\n"
                result += " → ".join(n.id for n in path.nodes)
            else:
                result = "No s'ha trobat cap ruta."
            self.output.setText(result)
        except Exception as ex:
            self.output.setText(f"[ERROR] {ex}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
