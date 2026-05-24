"""Interfície gràfica de RedTrace amb Qt6 (PySide6).

Tema fosc amb accent vermell, tabs per a graf/informe/cicles/estadístiques i
graf de xarxa interactiu via matplotlib (backend QtAgg).
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path as _PathLib
from typing import List, Optional

import matplotlib

matplotlib.use("QtAgg")
import networkx as nx
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import (
    Qt,
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QVariantAnimation,
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from engine.decision_tree import DecisionTreeRiskClassifier
from engine.dfs import CycleDetector
from engine.graph import TopologyGraph
from engine.ids_sim import IDSSimulator
from engine.risk import make_classifier
from engine.route_strategy import FewestHopsRoute, SafestRoute, ShortestRoute
from engine.types import AnalysisReport, Edge as RTEdge, Node as RTNode, Path as RTPath, RiskLevel
from scanner.parser import NetworkParser
from scanner.synthetic import generate_topology, save_topology


COL_BG = "#0E0E12"
COL_PANEL = "#181821"
COL_CARD = "#23232E"
COL_CARD_HOVER = "#2A2A36"
COL_BORDER = "#2D2D3A"
COL_ACCENT = "#E53935"
COL_ACCENT_DARK = "#B71C1C"
COL_TEXT = "#ECEFF4"
COL_TEXT_DIM = "#7A8090"
COL_LOW = "#43A047"
COL_MEDIUM = "#FB8C00"
COL_CRITICAL = "#E53935"
COL_SUCCESS = "#43A047"

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
QFrame#vsep {{ background: {COL_BORDER}; max-width: 1px; min-width: 1px; }}
QFrame#rowSep {{ background: {COL_BORDER}; max-height: 1px; min-height: 1px; }}
QFrame#accentBar {{ border-radius: 2px; }}

QLabel#brand {{ color: {COL_ACCENT}; font-size: 24px; font-weight: 800; letter-spacing: 0.5px; }}
QLabel#tagline {{ color: {COL_TEXT_DIM}; font-size: 12px; }}
QLabel#sectionTitle {{ color: {COL_ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }}
QLabel#fieldLabel {{ color: {COL_TEXT_DIM}; font-size: 11px; font-weight: 500; }}
QLabel#statusOk {{ color: {COL_TEXT_DIM}; font-size: 11px; }}
QLabel#statusErr {{ color: {COL_ACCENT}; font-size: 11px; font-weight: 600; }}
QLabel#bannerText {{ font-size: 13px; font-weight: 700; }}
QLabel#statText {{ color: {COL_TEXT_DIM}; font-size: 11px; font-family: "Consolas", monospace; }}
QLabel#cardLabel {{ color: {COL_TEXT_DIM}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#cardValue {{ color: {COL_TEXT}; font-size: 26px; font-weight: 700; }}

QLineEdit, QComboBox {{
    background: {COL_CARD};
    color: {COL_TEXT};
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    font-family: "Consolas", "Menlo", monospace;
    font-size: 12px;
    selection-background-color: {COL_ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {COL_ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid {COL_TEXT_DIM}; margin-right: 8px; }}
QComboBox QAbstractItemView {{
    background: {COL_CARD};
    color: {COL_TEXT};
    selection-background-color: {COL_ACCENT};
    selection-color: white;
    border: 1px solid {COL_BORDER};
    outline: 0;
    padding: 4px;
}}

QPushButton {{
    background: {COL_CARD};
    color: {COL_TEXT};
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton:hover {{ background: {COL_CARD_HOVER}; border-color: {COL_TEXT_DIM}; }}
QPushButton:pressed {{ background: {COL_PANEL}; }}
QPushButton#runBtn {{
    background: {COL_ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 16px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QPushButton#runBtn:hover {{ background: {COL_ACCENT_DARK}; }}
QPushButton#runBtn:disabled {{ background: #4A1A1A; color: #888; }}

QRadioButton {{ color: {COL_TEXT}; font-size: 12px; padding: 6px 0; spacing: 8px; }}
QRadioButton::indicator {{ width: 14px; height: 14px; }}
QRadioButton::indicator:unchecked {{ border: 1.5px solid {COL_TEXT_DIM}; border-radius: 8px; background: transparent; }}
QRadioButton::indicator:checked {{ border: 4px solid {COL_ACCENT}; border-radius: 8px; background: white; }}

QTabWidget::pane {{ background: {COL_PANEL}; border: none; top: -1px; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{
    background: {COL_CARD};
    color: {COL_TEXT_DIM};
    padding: 10px 24px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 3px;
    font-size: 12px;
    font-weight: 600;
}}
QTabBar::tab:selected {{ background: {COL_ACCENT}; color: white; }}
QTabBar::tab:hover:!selected {{ background: {COL_CARD_HOVER}; color: {COL_TEXT}; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: {COL_PANEL}; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {COL_BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {COL_TEXT_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QScrollBar:horizontal {{ background: {COL_PANEL}; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {COL_BORDER}; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {COL_TEXT_DIM}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""


def _hsep() -> QFrame:
    f = QFrame()
    f.setObjectName("separator")
    f.setFixedHeight(1)
    return f


def _row_sep() -> QFrame:
    f = QFrame()
    f.setObjectName("rowSep")
    f.setFixedHeight(1)
    return f


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("sectionTitle")
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    return lbl


def _level_text(level: RiskLevel) -> QLabel:
    lbl = QLabel(level.value)
    lbl.setStyleSheet(
        f"color: {LEVEL_COLOR[level]}; font-size: 11px; "
        f"font-weight: 800; letter-spacing: 1.2px;"
    )
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


def _fade_in(widget: QWidget, duration: int = 320) -> QPropertyAnimation:
    eff = QGraphicsOpacityEffect(widget)
    eff.setOpacity(0.0)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    widget.setProperty("_fadeAnim", anim)
    return anim


def _animate_int(label: QLabel, target: int, duration: int = 700) -> QVariantAnimation:
    anim = QVariantAnimation(label)
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(int(target))
    anim.setEasingCurve(QEasingCurve.OutQuart)
    anim.valueChanged.connect(lambda v: label.setText(str(int(v))))
    anim.start()
    label.setProperty("_intAnim", anim)
    return anim


def _animate_float(
    label: QLabel, target: float, duration: int = 700, fmt: str = "{:.2f}"
) -> QVariantAnimation:
    anim = QVariantAnimation(label)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(float(target))
    anim.setEasingCurve(QEasingCurve.OutQuart)
    anim.valueChanged.connect(lambda v: label.setText(fmt.format(float(v))))
    anim.start()
    label.setProperty("_floatAnim", anim)
    return anim


class AnimatedBar(QFrame):
    """Barra horitzontal amb fons fix i emplenat animat."""

    def __init__(self, color: str, height: int = 18) -> None:
        super().__init__()
        self.setFixedHeight(height)
        self.setStyleSheet(f"background: {COL_PANEL}; border-radius: 4px;")
        self._ratio = 0.0
        self._fill = QFrame(self)
        self._fill.setStyleSheet(f"background: {color}; border-radius: 4px;")
        self._fill.setGeometry(0, 0, 0, height)
        self._anim: QVariantAnimation | None = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        w = max(0, int(self.width() * self._ratio))
        self._fill.setGeometry(0, 0, w, self.height())

    def setRatio(self, ratio: float) -> None:
        self._ratio = max(0.0, min(1.0, float(ratio)))
        self._refresh()

    def animateTo(self, target: float, duration: int = 700) -> None:
        anim = QVariantAnimation(self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(max(0.0, min(1.0, float(target))))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(self.setRatio)
        anim.start()
        self._anim = anim


class RedTraceWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RedTrace · Lateral Movement Simulator [BETA]")
        self.resize(1340, 880)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        self.classifier = DecisionTreeRiskClassifier()
        self.graph: Optional[TopologyGraph] = None
        self.nodes: List = []
        self.node_ids: List[str] = []
        self.last_report: Optional[AnalysisReport] = None

        self._build_ui()

        default_topo = _PathLib("data") / "topology_mock.json"
        if default_topo.is_file():
            self.path_input.setText(str(default_topo))
            self._load_topology()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(10)

        body_layout.addWidget(self._build_sidebar())
        body_layout.addWidget(self._build_main(), 1)

        root.addWidget(body, 1)
        root.addWidget(self._build_footer())

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(72)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)

        brand_box = QHBoxLayout()
        brand_box.setSpacing(14)
        brand = QLabel("RedTrace")
        brand.setObjectName("brand")
        brand_box.addWidget(brand)
        sep = QFrame()
        sep.setObjectName("vsep")
        sep.setFixedHeight(28)
        brand_box.addWidget(sep)
        tagline = QLabel("Lateral Movement Simulator")
        tagline.setObjectName("tagline")
        brand_box.addWidget(tagline)

        layout.addLayout(brand_box)
        layout.addStretch()

        course = QLabel("ADAA · ENTI-UB · 2025-26")
        course.setObjectName("tagline")
        layout.addWidget(course)
        return header

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(56)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 0, 24, 0)

        self.banner_label = QLabel("IDS · esperant anàlisi")
        self.banner_label.setObjectName("bannerText")
        self.banner_label.setStyleSheet(f"color: {COL_TEXT_DIM};")
        layout.addWidget(self.banner_label)
        layout.addStretch()

        self.banner_stats = QLabel("")
        self.banner_stats.setObjectName("statText")
        layout.addWidget(self.banner_stats)
        return footer

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(20, 22, 20, 20)
        v.setSpacing(8)

        v.addWidget(_section_title("TOPOLOGIA"))
        v.addWidget(_hsep())
        v.addSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Ruta al JSON de ShadowScan…")
        v.addWidget(self.path_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        browse_btn = QPushButton("Examinar")
        browse_btn.clicked.connect(self._on_browse)
        load_btn = QPushButton("Carregar")
        load_btn.setStyleSheet(
            f"background: {COL_ACCENT_DARK}; color: white; border: none;"
        )
        load_btn.clicked.connect(self._load_topology)
        btn_row.addWidget(browse_btn)
        btn_row.addWidget(load_btn, 1)
        v.addLayout(btn_row)

        v.addSpacing(6)
        synth_btn = QPushButton("Generar topologia sintètica…")
        synth_btn.clicked.connect(self._on_generate_synthetic)
        v.addWidget(synth_btn)

        v.addSpacing(22)
        v.addWidget(_section_title("ANÀLISI"))
        v.addWidget(_hsep())
        v.addSpacing(8)

        v.addWidget(_field_label("Punt d'entrada"))
        self.entry_combo = QComboBox()
        self.entry_combo.setEditable(False)
        v.addWidget(self.entry_combo)

        v.addSpacing(8)
        v.addWidget(_field_label("Objectiu"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(False)
        v.addWidget(self.target_combo)

        v.addSpacing(12)
        v.addWidget(_field_label("Estratègia de ruta"))
        self.strat_group = QButtonGroup(self)
        self.radio_short = QRadioButton("Camí més curt (Dijkstra)")
        self.radio_safe = QRadioButton("Camí més segur (evita CRITICAL)")
        self.radio_bfs = QRadioButton("Menys salts (BFS)")
        self.radio_short.setChecked(True)
        self.strat_group.addButton(self.radio_short)
        self.strat_group.addButton(self.radio_safe)
        self.strat_group.addButton(self.radio_bfs)
        v.addWidget(self.radio_short)
        v.addWidget(self.radio_safe)
        v.addWidget(self.radio_bfs)

        v.addSpacing(20)
        self.run_btn = QPushButton("EXECUTAR ANÀLISI")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.clicked.connect(self._on_run)
        v.addWidget(self.run_btn)

        v.addSpacing(16)
        v.addWidget(_hsep())
        v.addSpacing(8)
        self.status_label = QLabel("Carrega una topologia per començar.")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        v.addWidget(self.status_label)

        v.addStretch()
        return sidebar

    def _build_main(self) -> QFrame:
        main = QFrame()
        main.setObjectName("mainPanel")
        v = QVBoxLayout(main)
        v.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_graph_tab(), "Graf")
        self.tabs.addTab(self._build_report_tab(), "Informe")
        self.tabs.addTab(self._build_cycles_tab(), "Cicles")
        self.tabs.addTab(self._build_stats_tab(), "Estadístiques")
        v.addWidget(self.tabs)
        return main

    def _build_graph_tab(self) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(8, 12, 8, 8)

        self.fig = Figure(figsize=(10, 7), facecolor=COL_PANEL, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()
        self._draw_empty()

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setStyleSheet(f"background: {COL_PANEL};")
        layout.addWidget(self.canvas)
        return wrap

    def _build_report_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.report_holder = QWidget()
        self.report_layout = QVBoxLayout(self.report_holder)
        self.report_layout.setContentsMargins(12, 12, 12, 12)
        self.report_layout.setSpacing(10)
        self._report_placeholder()
        scroll.setWidget(self.report_holder)
        return scroll

    def _build_cycles_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.cycles_holder = QWidget()
        self.cycles_layout = QVBoxLayout(self.cycles_holder)
        self.cycles_layout.setContentsMargins(12, 12, 12, 12)
        self.cycles_layout.setSpacing(10)
        self._cycles_placeholder()
        scroll.setWidget(self.cycles_holder)
        return scroll

    def _build_stats_tab(self) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        self.stats_grid_holder = QWidget()
        self.stats_grid = QGridLayout(self.stats_grid_holder)
        self.stats_grid.setHorizontalSpacing(12)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stats_grid_holder)

        self.dist_holder = QFrame()
        self.dist_holder.setObjectName("card")
        self.dist_layout = QVBoxLayout(self.dist_holder)
        self.dist_layout.setContentsMargins(18, 16, 18, 18)
        self.dist_layout.setSpacing(8)
        layout.addWidget(self.dist_holder)

        layout.addStretch()
        self._stats_placeholder()
        return wrap

    def _report_placeholder(self) -> None:
        self._clear_layout(self.report_layout)
        lbl = QLabel("Cap anàlisi executada encara.\n\nCarrega una topologia i prem «Executar anàlisi».")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px; padding: 60px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.report_layout.addWidget(lbl)
        self.report_layout.addStretch()

    def _cycles_placeholder(self) -> None:
        self._clear_layout(self.cycles_layout)
        lbl = QLabel("Cap cicle analitzat encara.")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px; padding: 60px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.cycles_layout.addWidget(lbl)
        self.cycles_layout.addStretch()

    def _stats_placeholder(self) -> None:
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.dist_layout)
        lbl = QLabel("Executa una anàlisi per veure estadístiques.")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.dist_layout.addWidget(lbl)

    def _clear_layout(self, layout) -> None:
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                child = item.layout()
                if child is not None:
                    self._clear_layout(child)

    def _draw_empty(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()
        self.ax.text(
            0.5, 0.5,
            "Carrega una topologia\nper visualitzar la xarxa",
            ha="center", va="center",
            color=COL_TEXT_DIM, fontsize=14,
            transform=self.ax.transAxes,
        )
        if hasattr(self, "canvas"):
            self.canvas.draw_idle()

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona topologia ShadowScan",
            "", "JSON (*.json);;Tots els fitxers (*.*)",
        )
        if path:
            self.path_input.setText(path)
            self._load_topology()

    def _load_topology(self) -> None:
        topo_path = self.path_input.text().strip()
        if not topo_path or not _PathLib(topo_path).is_file():
            self._set_status("Fitxer no trobat", error=True)
            return
        try:
            parser = NetworkParser(topo_path)
            nodes, edges, default_entry, default_target = parser.load()
            self.nodes = nodes
            self.node_ids = [n.id for n in nodes]
            self.graph = TopologyGraph().build(nodes, edges)
            self.classifier.annotate_nodes(nodes)

            self.entry_combo.clear()
            self.entry_combo.addItems(self.node_ids)
            self.entry_combo.setCurrentText(default_entry)

            self.target_combo.clear()
            self.target_combo.addItems(self.node_ids)
            self.target_combo.setCurrentText(default_target)

            self._draw_graph(set())
            self._set_status(
                f"Topologia carregada · {len(nodes)} nodes · {len(edges)} arestes"
            )
        except Exception as exc:
            self._set_status(f"Error en carregar: {exc}", error=True)
            traceback.print_exc()

    def _on_run(self) -> None:
        if self.graph is None or not self.nodes:
            self._set_status("Carrega una topologia primer", error=True)
            return
        entry = self.entry_combo.currentText()
        target = self.target_combo.currentText()
        if entry == target:
            self._set_status("Entrada i objectiu han de ser diferents", error=True)
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("EXECUTANT...")
        QApplication.processEvents()

        try:
            if self.radio_short.isChecked():
                strategy = ShortestRoute()
            elif self.radio_safe.isChecked():
                strategy = SafestRoute()
            else:
                strategy = FewestHopsRoute()
            path = strategy.select(self.graph, entry, target)
            if path is None:
                self._set_status(f"Sense ruta entre {entry} i {target}", error=True)
                return
            cycles = CycleDetector(self.graph).find_cycles()
            ids_result = IDSSimulator().evaluate(path)

            report = AnalysisReport(
                entry=entry, target=target, path=path,
                cycles=cycles, ids_result=ids_result,
                node_classifications={n.id: n.risk_level for n in self.nodes},
            )
            self.last_report = report

            highlighted = {(e.from_node, e.to_node) for e in path.edges}
            self._draw_graph(highlighted)
            self._render_report(report)
            self._render_cycles(cycles)
            self._render_stats(report)
            self._update_banner(report)
            self._set_status(
                f"OK · {path.hops} salts · pes {path.total_weight:.2f}"
            )
            self.tabs.setCurrentIndex(0)
        except Exception as exc:
            self._set_status(f"Error: {exc}", error=True)
            traceback.print_exc()
        finally:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("EXECUTAR ANÀLISI")

    def _draw_graph(self, highlighted_edges) -> None:
        if self.graph is None:
            self._draw_empty()
            return
        g = self.graph.raw
        self.ax.clear()
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()

        pos = nx.spring_layout(g, seed=42, k=1.7, iterations=100)

        node_colors = []
        for nid in g.nodes:
            n = self.graph.get_node(nid)
            color = LEVEL_COLOR.get(n.risk_level, COL_TEXT_DIM) if n else COL_TEXT_DIM
            node_colors.append(color)

        edge_colors = []
        edge_widths = []
        for u, v in g.edges:
            if (u, v) in highlighted_edges:
                edge_colors.append(COL_ACCENT)
                edge_widths.append(3.5)
            else:
                edge_colors.append("#3A3A48")
                edge_widths.append(1.0)

        nx.draw_networkx_nodes(
            g, pos, node_color=node_colors, node_size=950,
            edgecolors=COL_TEXT, linewidths=1.4, ax=self.ax,
        )
        nx.draw_networkx_edges(
            g, pos, edge_color=edge_colors, width=edge_widths,
            arrows=True, arrowsize=14, ax=self.ax,
            connectionstyle="arc3,rad=0.06",
        )
        nx.draw_networkx_labels(
            g, pos, font_size=8, font_weight="bold",
            font_color=COL_TEXT, ax=self.ax,
        )

        edge_labels = {(u, v): f"{g[u][v]['weight']:.2f}" for u, v in g.edges}
        nx.draw_networkx_edge_labels(
            g, pos, edge_labels=edge_labels, font_size=7,
            font_color=COL_TEXT_DIM, bbox=dict(facecolor=COL_PANEL, edgecolor="none", pad=1),
            ax=self.ax,
        )

        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _render_report(self, report: AnalysisReport) -> None:
        self._clear_layout(self.report_layout)

        # Path header (no card)
        head_box = QVBoxLayout()
        head_box.setSpacing(2)
        title = QLabel(f"{report.entry}     {report.target}")
        title.setStyleSheet(
            f"color: {COL_TEXT}; font-family: Consolas, monospace; "
            f"font-size: 17px; font-weight: 700; letter-spacing: 0.5px;"
        )
        head_box.addWidget(title)
        sub = QLabel(
            f"Estratègia: {self._current_strategy_label()}   ·   "
            f"{len(report.path.nodes)} nodes   ·   {report.path.hops} salts   ·   "
            f"pes {report.path.total_weight:.2f}   ·   risc mitjà {report.path.avg_risk:.2f}"
        )
        sub.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 11px;")
        head_box.addWidget(sub)
        head_wrap = QWidget()
        head_wrap.setLayout(head_box)
        self.report_layout.addWidget(head_wrap)

        self.report_layout.addSpacing(6)
        self.report_layout.addWidget(_row_sep())
        self.report_layout.addSpacing(6)

        # Per-node rows (no card)
        for i, node in enumerate(report.path.nodes):
            row_wrap = QWidget()
            cl = QVBoxLayout(row_wrap)
            cl.setContentsMargins(0, 6, 0, 6)
            cl.setSpacing(6)

            top = QHBoxLayout()
            top.setSpacing(12)

            step = QLabel(f"{i:02d}")
            step.setStyleSheet(
                f"color: {COL_ACCENT}; font-family: Consolas, monospace; "
                f"font-size: 14px; font-weight: 800; min-width: 28px;"
            )
            top.addWidget(step)

            id_label = QLabel(node.id)
            id_label.setStyleSheet(
                f"color: {COL_TEXT}; font-family: Consolas, monospace; "
                f"font-size: 13px; font-weight: 700;"
            )
            top.addWidget(id_label)

            type_label = QLabel(node.type)
            type_label.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 11px;")
            top.addWidget(type_label)

            top.addStretch()

            risk_label = QLabel(f"risc {node.risk:.2f}")
            risk_label.setStyleSheet(
                f"color: {COL_TEXT_DIM}; font-family: Consolas, monospace; font-size: 11px;"
            )
            top.addWidget(risk_label)

            top.addWidget(_level_text(node.risk_level))
            cl.addLayout(top)

            classifier = make_classifier(node.risk_level)
            for rec in classifier.get_recommendations():
                rl = QLabel(f"      {rec}")
                rl.setStyleSheet(f"color: {COL_TEXT}; font-size: 11px;")
                rl.setWordWrap(True)
                cl.addWidget(rl)

            self.report_layout.addWidget(row_wrap)
            if i < len(report.path.nodes) - 1:
                self.report_layout.addWidget(_row_sep())

        self.report_layout.addSpacing(14)

        # IDS verdict (left accent bar + bold colored text, no filled card)
        ids_color = COL_CRITICAL if report.ids_result.detected else COL_SUCCESS
        ids_wrap = QWidget()
        ids_layout = QHBoxLayout(ids_wrap)
        ids_layout.setContentsMargins(0, 0, 0, 0)
        ids_layout.setSpacing(14)

        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"background: {ids_color}; border-radius: 2px;")
        ids_layout.addWidget(accent_bar)

        ids_text_box = QVBoxLayout()
        ids_text_box.setSpacing(4)
        title_text = (
            "IDS HA DETECTAT LA RUTA"
            if report.ids_result.detected
            else "IDS NO HA DETECTAT LA RUTA"
        )
        title = QLabel(title_text)
        title.setStyleSheet(
            f"color: {ids_color}; font-size: 14px; font-weight: 800; letter-spacing: 1px;"
        )
        ids_text_box.addWidget(title)
        if report.ids_result.triggered_signatures:
            sigs = QLabel(
                "Firmes activades: "
                + ", ".join(report.ids_result.triggered_signatures)
            )
            sigs.setStyleSheet(f"color: {COL_TEXT}; font-size: 11px;")
            ids_text_box.addWidget(sigs)
        msg = QLabel(report.ids_result.message)
        msg.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 11px;")
        msg.setWordWrap(True)
        ids_text_box.addWidget(msg)
        ids_layout.addLayout(ids_text_box, 1)

        self.report_layout.addWidget(ids_wrap)
        self.report_layout.addStretch()

        _fade_in(self.report_holder)

    def _render_cycles(self, cycles) -> None:
        self._clear_layout(self.cycles_layout)
        if not cycles:
            lbl = QLabel("Cap cicle detectat al graf")
            lbl.setStyleSheet(
                f"color: {COL_SUCCESS}; font-size: 14px; "
                f"padding: 60px; font-weight: 700; letter-spacing: 1px;"
            )
            lbl.setAlignment(Qt.AlignCenter)
            self.cycles_layout.addWidget(lbl)
            self.cycles_layout.addStretch()
            _fade_in(self.cycles_holder)
            return

        for i, cycle in enumerate(cycles, 1):
            row_wrap = QWidget()
            cl = QVBoxLayout(row_wrap)
            cl.setContentsMargins(0, 6, 0, 6)
            cl.setSpacing(4)
            title = QLabel(f"CICLE #{i:02d}")
            title.setStyleSheet(
                f"color: {COL_ACCENT}; font-size: 11px; "
                f"font-weight: 800; letter-spacing: 1.5px;"
            )
            cl.addWidget(title)
            body = QLabel("        ".join(cycle))
            body.setStyleSheet(
                f"color: {COL_TEXT}; font-family: Consolas, monospace; font-size: 13px;"
            )
            body.setWordWrap(True)
            cl.addWidget(body)
            self.cycles_layout.addWidget(row_wrap)
            if i < len(cycles):
                self.cycles_layout.addWidget(_row_sep())
        self.cycles_layout.addStretch()
        _fade_in(self.cycles_holder)

    def _render_stats(self, report: AnalysisReport) -> None:
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.dist_layout)

        avg_color = (
            COL_CRITICAL if report.path.avg_risk > 0.7
            else COL_MEDIUM if report.path.avg_risk > 0.4
            else COL_SUCCESS
        )
        ids_color = COL_CRITICAL if report.ids_result.detected else COL_SUCCESS
        ids_text = "DETECTAT" if report.ids_result.detected else "NEGATIU"

        # Animated numeric tiles (no card backgrounds)
        cards = [
            ("SALTS", report.path.hops, "int", COL_TEXT),
            ("PES TOTAL", report.path.total_weight, "float", COL_TEXT),
            ("RISC MITJÀ", report.path.avg_risk, "float", avg_color),
            ("IDS", ids_text, "static", ids_color),
        ]
        for c, (label, value, kind, color) in enumerate(cards):
            tile = QWidget()
            cl = QVBoxLayout(tile)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(8)
            l1 = QLabel(label)
            l1.setObjectName("cardLabel")
            l2 = QLabel("0" if kind != "static" else "")
            l2.setStyleSheet(
                f"color: {color}; font-size: 32px; font-weight: 800; letter-spacing: 1px;"
            )
            cl.addWidget(l1)
            cl.addWidget(l2)
            self.stats_grid.addWidget(tile, 0, c)
            self.stats_grid.setColumnStretch(c, 1)

            if kind == "int":
                _animate_int(l2, int(value), duration=750)
            elif kind == "float":
                _animate_float(l2, float(value), duration=750)
            else:
                l2.setText(str(value))
                _fade_in(l2, duration=400)

        # Risk distribution (no card, animated bars)
        title = QLabel("DISTRIBUCIÓ DE RISC AL GRAF")
        title.setObjectName("cardLabel")
        self.dist_layout.addWidget(title)
        self.dist_layout.addSpacing(8)

        dist = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 0, RiskLevel.CRITICAL: 0}
        for lvl in report.node_classifications.values():
            dist[lvl] = dist.get(lvl, 0) + 1
        total = sum(dist.values()) or 1

        bars: list[AnimatedBar] = []
        for level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.CRITICAL):
            row = QHBoxLayout()
            row.setSpacing(12)
            tag = QLabel(level.value)
            tag.setFixedWidth(90)
            tag.setStyleSheet(
                f"color: {LEVEL_COLOR[level]}; font-size: 11px; "
                f"font-weight: 800; letter-spacing: 1.2px;"
            )
            row.addWidget(tag)

            bar = AnimatedBar(LEVEL_COLOR[level], height=18)
            bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            bar.setProperty("_targetRatio", dist[level] / total)
            row.addWidget(bar, 1)
            bars.append(bar)

            count = QLabel("0")
            count.setFixedWidth(36)
            count.setStyleSheet(
                f"color: {COL_TEXT}; font-family: Consolas, monospace; "
                f"font-size: 13px; font-weight: 700;"
            )
            row.addWidget(count)
            _animate_int(count, dist[level], duration=750)

            self.dist_layout.addLayout(row)
            self.dist_layout.addSpacing(2)

        # Trigger bar animations once they have their final width
        def _start_bars():
            for b in bars:
                b.animateTo(float(b.property("_targetRatio")), duration=750)
        QApplication.instance().processEvents()
        _start_bars()

    def _update_banner(self, report: AnalysisReport) -> None:
        if report.ids_result.detected:
            n_sigs = len(report.ids_result.triggered_signatures)
            self.banner_label.setText(
                f"IDS DETECTAT   ·   {n_sigs} firma(es) activada(es)"
            )
            self.banner_label.setStyleSheet(f"color: {COL_CRITICAL};")
            self._pulse_banner(times=3)
        else:
            self.banner_label.setText("IDS NO DETECTAT   ·   ruta neta")
            self.banner_label.setStyleSheet(f"color: {COL_SUCCESS};")
            self._pulse_banner(times=1)
        self.banner_stats.setText(
            f"hops {report.path.hops}   ·   pes {report.path.total_weight:.2f}   "
            f"·   risc {report.path.avg_risk:.2f}"
        )

    def _pulse_banner(self, times: int = 2) -> None:
        eff = QGraphicsOpacityEffect(self.banner_label)
        self.banner_label.setGraphicsEffect(eff)
        seq = QSequentialAnimationGroup(self.banner_label)
        for _ in range(times):
            down = QPropertyAnimation(eff, b"opacity")
            down.setDuration(160)
            down.setStartValue(1.0)
            down.setEndValue(0.35)
            down.setEasingCurve(QEasingCurve.InOutSine)
            seq.addAnimation(down)
            up = QPropertyAnimation(eff, b"opacity")
            up.setDuration(220)
            up.setStartValue(0.35)
            up.setEndValue(1.0)
            up.setEasingCurve(QEasingCurve.InOutSine)
            seq.addAnimation(up)
        seq.start()
        self._banner_anim = seq

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.setText(text)
        self.status_label.setObjectName("statusErr" if error else "statusOk")
        self.status_label.setStyleSheet(
            f"color: {COL_ACCENT if error else COL_TEXT_DIM};"
            f" font-size: 11px; {'font-weight: 600;' if error else ''}"
        )

    # ---------------------------------------------------------------
    # Fase 3 — funcionalitats noves integrades a la GUI
    # ---------------------------------------------------------------

    def _current_strategy_label(self) -> str:
        if self.radio_short.isChecked():
            return "shortest"
        if self.radio_safe.isChecked():
            return "safest"
        return "fewest-hops"


    # --- Generador de topologies sintètiques -----------------------

    def _on_generate_synthetic(self) -> None:
        dlg = _SyntheticDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        n, density, critical_ratio, seed = dlg.values()
        try:
            topo = generate_topology(
                n_nodes=n, edge_density=density,
                critical_ratio=critical_ratio, seed=seed,
            )
            out_path = _PathLib("data/topology_synthetic.json")
            save_topology(topo, str(out_path))
            self.path_input.setText(str(out_path))
            self._load_topology()
            self._set_status(
                f"Topologia generada · N={n} · densitat={density:.2f}"
            )
        except Exception as exc:
            self._set_status(f"Error generant: {exc}", error=True)
            traceback.print_exc()


class _SyntheticDialog(QDialog):
    """Diàleg per a configurar el generador de topologies sintètiques."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generar topologia sintètica")
        self.setModal(True)
        self.setMinimumWidth(360)

        form = QFormLayout(self)
        self.n_spin = QSpinBox()
        self.n_spin.setRange(2, 5000)
        self.n_spin.setValue(20)
        form.addRow("Nombre de nodes (V):", self.n_spin)

        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0.0, 1.0)
        self.density_spin.setSingleStep(0.05)
        self.density_spin.setValue(0.20)
        form.addRow("Densitat d'arestes:", self.density_spin)

        self.critical_spin = QDoubleSpinBox()
        self.critical_spin.setRange(0.0, 1.0)
        self.critical_spin.setSingleStep(0.05)
        self.critical_spin.setValue(0.20)
        form.addRow("Ratio CRITICAL:", self.critical_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(42)
        form.addRow("Llavor (seed):", self.seed_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return (
            self.n_spin.value(),
            self.density_spin.value(),
            self.critical_spin.value(),
            self.seed_spin.value(),
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = RedTraceWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
