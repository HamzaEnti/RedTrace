"""Interfície gràfica de RedTrace amb Qt6 (PySide6).

Tema fosc amb accent vermell, tabs per a graf/informe/cicles/estadístiques i
graf de xarxa interactiu via matplotlib (backend QtAgg).

Asistencia d'ia per a l'edició de comentaris degut a la gran extensio del codi.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path as _PathLib
from typing import List, Optional

# Configurem matplotlib per usar el backend Qt6 ABANS d'importar pyplot.
# QtAgg integra el canvas de matplotlib directament com un widget de Qt.
import matplotlib
matplotlib.use("QtAgg")

import networkx as nx
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Importem els components de PySide6 (Qt per Python)
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

# Importem el motor intern de RedTrace
from engine.all_paths import AllPathsFinder
from engine.decision_tree import DecisionTreeRiskClassifier
from engine.dfs import CycleDetector
from engine.graph import TopologyGraph
from engine.ids_sim import IDSSimulator
from engine.risk import make_classifier
from engine.route_strategy import FewestHopsRoute, SafestRoute, ShortestRoute
from engine.types import AnalysisReport, Edge as RTEdge, Node as RTNode, Path as RTPath, RiskLevel
from scanner.parser import NetworkParser
from scanner.synthetic import generate_topology, save_topology


# Paleta de colors del tema fosc amb accent vermell

# Colors de fons en escala de grisos molt foscos
COL_BG = "#0E0E12"         # fons global de la finestra (quasi negre)
COL_PANEL = "#181821"      # fons de panells i sidebar
COL_CARD = "#23232E"       # fons de camps d'entrada i botons
COL_CARD_HOVER = "#2A2A36" # fons quan el ratolí passa per sobre un botó
COL_BORDER = "#2D2D3A"     # color dels marges i separadors

# Colors d'acció i estat
COL_ACCENT = "#E53935"      # vermell principal (botó Run, títols de seccions)
COL_ACCENT_DARK = "#B71C1C" # vermell fosc (botó Carregar, botó benchmark)

# Colors de text
COL_TEXT = "#ECEFF4"        # text principal (blanc trencat)
COL_TEXT_DIM = "#7A8090"    # text secundari i placeholders (gris blavós)

# Colors semafòric de nivell de risc
COL_LOW = "#43A047"         # verd → risc baix
COL_MEDIUM = "#FB8C00"      # taronja → risc mitjà
COL_CRITICAL = "#E53935"    # vermell → risc crític
COL_SUCCESS = "#43A047"     # verd → IDS no detectat / cap cicle

# Diccionari de mapeig RiskLevel → color (per usar-lo de forma centralitzada)
LEVEL_COLOR = {
    RiskLevel.LOW: COL_LOW,
    RiskLevel.MEDIUM: COL_MEDIUM,
    RiskLevel.CRITICAL: COL_CRITICAL,
}



# Full stylesheet de Qt (CSS per a widgets PySide6)

# Tota la interfície s'estilitza amb Qt Style Sheets (QSS), que és un CSS
# adaptat als widgets de Qt. Usem f-string per inserir les constants de color.
STYLESHEET = f"""
* {{ font-family: "Segoe UI", "SF Pro Display", "Inter", sans-serif; }}
QMainWindow, QWidget {{ background: {COL_BG}; color: {COL_TEXT}; }}

QFrame#header {{ background: {COL_PANEL}; border-bottom: 1px solid {COL_BORDER}; }}
QFrame#footer {{ background: {COL_PANEL}; border-top: 1px solid {COL_BORDER}; }}
QFrame#header QLabel {{ background: transparent; }}
QFrame#footer QLabel {{ background: transparent; }}
QLabel#sectionTitle {{ background: transparent; }}
QLabel#fieldLabel {{ background: transparent; }}
QLabel#tagline {{ background: transparent; }}
QLabel#statusOk {{ background: transparent; }}
QLabel#statusErr {{ background: transparent; }}
QRadioButton {{ background: transparent; }}
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



# Funcions d'utilitat per crear widgets estilitzats comuns
def _hsep() -> QFrame:
    """Crea una línia separadora horitzontal d'1 píxel d'alçada."""
    f = QFrame()
    f.setObjectName("separator")  # el QSS el reconeix per l'objectName
    f.setFixedHeight(1)
    return f


def _row_sep() -> QFrame:
    """Separador de fila per a llistes (lleugerament diferent del hsep global)."""
    f = QFrame()
    f.setObjectName("rowSep")
    f.setFixedHeight(1)
    return f


def _section_title(text: str) -> QLabel:
    """Etiqueta de títol de secció en majúscules i color d'accent."""
    lbl = QLabel(text)
    lbl.setObjectName("sectionTitle")
    return lbl


def _field_label(text: str) -> QLabel:
    """Etiqueta descriptiva per a un camp d'entrada (gris i lleugera)."""
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    return lbl


def _level_text(level: RiskLevel) -> QLabel:
    """Crea un QLabel amb el text i el color del nivell de risc indicat.

    Alinea el text a la dreta per usar-lo en files de nodes de la ruta.
    """
    lbl = QLabel(level.value)
    lbl.setStyleSheet(
        f"color: {LEVEL_COLOR[level]}; font-size: 11px; "
        f"font-weight: 800; letter-spacing: 1.2px;"
    )
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl



# Animacions de la GUI

# <-- inici us d'ia
# Les tres funcions següents implementen animacions sobre propietats de Qt.
# La complexitat ve de tres factors combinats:
#   1. QGraphicsOpacityEffect i QPropertyAnimation operen sobre el sistema
#      de meta-objectes de Qt (signals/slots en C++), invocats des de Python.
#   2. Les animacions es connecten a signals via lambda, cosa que crea
#      closures que capturen referències als widgets.
#   3. Qt destrueix els objectes d'animació quan no hi ha cap referència C++
#      viva; per evitar-ho cal emmagatzemar-los explícitament com a propietats
#      del widget amb setProperty(), un patró no obvi i específic de PySide6.

def _fade_in(widget: QWidget, duration: int = 320) -> QPropertyAnimation:
    """Aplica una animació de fade-in (opacitat 0→1) a un widget.

    Crea un QGraphicsOpacityEffect i l'anima amb QPropertyAnimation.
    L'animació s'emmagatzema com a propietat del widget per evitar que
    el garbage collector de Python la destrueixi abans que acabi.
    """
    eff = QGraphicsOpacityEffect(widget)
    eff.setOpacity(0.0)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)  # suavitza la desacceleració final
    anim.start()
    widget.setProperty("_fadeAnim", anim)  # evita que Python l'elimini
    return anim


def _animate_int(label: QLabel, target: int, duration: int = 700) -> QVariantAnimation:
    """Anima un QLabel des de 0 fins a un valor enter amb efecte de comptador.

    Ideal per a les targetes d'estadístiques (nº de salts, nº de cicles...).
    """
    anim = QVariantAnimation(label)
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(int(target))
    anim.setEasingCurve(QEasingCurve.OutQuart)  # arrenca ràpid i frena al final
    # Cada vegada que el valor canvia, actualitzem el text del label
    anim.valueChanged.connect(lambda v: label.setText(str(int(v))))
    anim.start()
    label.setProperty("_intAnim", anim)  # evitem que Python destrueixi l'animació
    return anim


def _animate_float(
    label: QLabel, target: float, duration: int = 700, fmt: str = "{:.2f}"
) -> QVariantAnimation:
    """Igual que _animate_int però per a valors decimals amb format configurable.

    Exemple d'ús: mostrar el pes total de la ruta o el risc mitjà.
    """
    anim = QVariantAnimation(label)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(float(target))
    anim.setEasingCurve(QEasingCurve.OutQuart)
    anim.valueChanged.connect(lambda v: label.setText(fmt.format(float(v))))
    anim.start()
    label.setProperty("_floatAnim", anim)
    return anim
# <-- fi us d'ia



# Widget de barra de progrés animada per a la distribució de risc

# <-- inici us d'ia
# AnimatedBar és un widget completament personalitzat que no existeix a Qt.
# La complexitat principal és que l'emplenat (self._fill) és un QFrame fill
# posicionat manualment amb setGeometry, de manera que cal recalcular-lo
# tant quan canvia el ratio com quan el widget extern es redimensiona
# (resizeEvent). Sense reimplementar resizeEvent, la barra quedaria incorrecta
# en qualsevol redimensionament de finestra.
# A més, animateTo() usa QVariantAnimation connectat a setRatio per interpolar
# suaument entre 0.0 i el valor objectiu, guardant la referència a self._anim
# per evitar que el GC de Python la destrueixi abans que acabi l'animació.
class AnimatedBar(QFrame):
    """Barra horitzontal amb fons fix i emplenat animat.

    S'usa a la pestanya d'Estadístiques per mostrar la distribució
    de nodes per nivell de risc (LOW / MEDIUM / CRITICAL).

    Internament conté un QFrame fill (self._fill) que s'eixampla
    progressivament fins a ocupar la proporció indicada.
    """

    def __init__(self, color: str, height: int = 18) -> None:
        super().__init__()
        self.setFixedHeight(height)
        self.setStyleSheet(f"background: {COL_PANEL}; border-radius: 4px;")
        self._ratio = 0.0  # proporció actual (0.0 = buit, 1.0 = ple)

        # Widget fill que representa l'emplenat de la barra
        self._fill = QFrame(self)
        self._fill.setStyleSheet(f"background: {color}; border-radius: 4px;")
        self._fill.setGeometry(0, 0, 0, height)  # comença amb amplada 0

        self._anim: QVariantAnimation | None = None  # referència a l'animació activa

    def resizeEvent(self, event) -> None:
        """Quan el widget es redimensiona, recalculem l'amplada del fill."""
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        """Actualitza l'amplada del fill en funció de self._ratio i l'amplada real."""
        w = max(0, int(self.width() * self._ratio))
        self._fill.setGeometry(0, 0, w, self.height())

    def setRatio(self, ratio: float) -> None:
        """Estableix la proporció i refresca immediatament (sense animació)."""
        self._ratio = max(0.0, min(1.0, float(ratio)))
        self._refresh()

    def animateTo(self, target: float, duration: int = 700) -> None:
        """Anima la barra des de 0.0 fins al valor objectiu amb easing cúbic."""
        anim = QVariantAnimation(self)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(max(0.0, min(1.0, float(target))))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(self.setRatio)  # cada tick actualitza la barra
        anim.start()
        self._anim = anim  # mantenim la referència per evitar que Python l'elimini
# <-- fi us d'ia



# Finestra principal de l'aplicació
class RedTraceWindow(QMainWindow):
    """Finestra principal de RedTrace.

    Estructura de la UI:
      ┌─────────── Header ────────────┐
      │ Sidebar  │  Panell principal  │
      │ (controls│  (tabs: Graf /     │
      │  càrrega │   Informe /        │
      │  anàlisi)│   Cicles /         │
      │          │   Estadístiques /  │
      │          │   AllPaths /       │
      │          │   Benchmarks)      │
      └─────────── Footer ────────────┘
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RedTrace · Lateral Movement Simulator")
        self.resize(1340, 880)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        # Classificador de risc per als nodes (arbre de decisió intern)
        self.classifier = DecisionTreeRiskClassifier()

        # Estat intern de l'aplicació
        self.graph: Optional[TopologyGraph] = None  # graf carregat actualment
        self.nodes: List = []                        # llista de nodes del graf
        self.node_ids: List[str] = []                # IDs dels nodes per als combos
        self.last_report: Optional[AnalysisReport] = None  # darrer informe generat

        # Construïm tots els widgets de la interfície
        self._build_ui()

        # Si existeix el fitxer de topologia de mostra, el carreguem automàticament
        default_topo = _PathLib("data") / "topology_mock.json"
        if default_topo.is_file():
            self.path_input.setText(str(default_topo))
            self._load_topology()


    # Construcció de la UI
    def _build_ui(self) -> None:
        """Assembla l'estructura principal: header + body (sidebar + main) + footer."""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        # El body ocupa tot l'espai disponible i conté el sidebar i el panell principal
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 12)
        body_layout.setSpacing(10)
        body_layout.addWidget(self._build_sidebar())
        body_layout.addWidget(self._build_main(), 1)  # el factor 1 fa que s'expandeixi

        root.addWidget(body, 1)
        root.addWidget(self._build_footer())

    def _build_header(self) -> QFrame:
        """Construeix la barra superior amb el nom del projecte i el curs."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(72)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)

        # Bloc esquerra: "RedTrace" + separador vertical + tagline
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
        layout.addStretch()  # empeny el curs cap a la dreta

        course = QLabel("ADAA · ENTI-UB · 2025-26")
        course.setObjectName("tagline")
        layout.addWidget(course)
        return header

    def _build_footer(self) -> QFrame:
        """Construeix la barra inferior amb l'estat de l'IDS i les estadístiques ràpides."""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(56)
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 0, 24, 0)

        # Etiqueta principal del footer: canvia de color si l'IDS detecta la ruta
        self.banner_label = QLabel("IDS · esperant anàlisi")
        self.banner_label.setObjectName("bannerText")
        self.banner_label.setStyleSheet(f"color: {COL_TEXT_DIM};")
        layout.addWidget(self.banner_label)
        layout.addStretch()

        # Etiqueta dreta: resum numèric (hops, pes, risc)
        self.banner_stats = QLabel("")
        self.banner_stats.setObjectName("statText")
        layout.addWidget(self.banner_stats)
        return footer

    def _build_sidebar(self) -> QFrame:
        """Construeix el panell lateral esquerre amb els controls de l'anàlisi.

        Conté:
          - Selector de fitxer de topologia
          - Botons de càrrega i generació sintètica
          - Combos d'entrada i objectiu
          - Botons de ràdio per l'estratègia de ruta
          - Botó principal "Executar anàlisi"
          - Etiqueta d'estat
        """
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(20, 22, 20, 20)
        v.setSpacing(8)

        # Secció TOPOLOGIA
        v.addWidget(_section_title("TOPOLOGIA"))
        v.addWidget(_hsep())
        v.addSpacing(8)

        # Camp de text per a la ruta del fitxer JSON
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Ruta al JSON de ShadowScan…")
        v.addWidget(self.path_input)

        # Botons "Examinar" i "Carregar" en fila
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

        # Secció ANÀLISI
        v.addSpacing(22)
        v.addWidget(_section_title("ANÀLISI"))
        v.addWidget(_hsep())
        v.addSpacing(8)

        # Selector del node d'entrada
        v.addWidget(_field_label("Punt d'entrada"))
        self.entry_combo = QComboBox()
        self.entry_combo.setEditable(False)
        v.addWidget(self.entry_combo)

        v.addSpacing(8)

        # Selector del node objectiu
        v.addWidget(_field_label("Objectiu"))
        self.target_combo = QComboBox()
        self.target_combo.setEditable(False)
        v.addWidget(self.target_combo)

        v.addSpacing(12)

        # Grup de botons de ràdio per triar l'estratègia de ruta
        v.addWidget(_field_label("Estratègia de ruta"))
        self.strat_group = QButtonGroup(self)
        self.radio_short = QRadioButton("Camí més curt (Dijkstra)")
        self.radio_safe = QRadioButton("Camí més segur (evita CRITICAL)")
        self.radio_bfs = QRadioButton("Menys salts (BFS)")
        self.radio_short.setChecked(True)  # Dijkstra seleccionat per defecte
        self.strat_group.addButton(self.radio_short)
        self.strat_group.addButton(self.radio_safe)
        self.strat_group.addButton(self.radio_bfs)
        v.addWidget(self.radio_short)
        v.addWidget(self.radio_safe)
        v.addWidget(self.radio_bfs)

        v.addSpacing(20)

        # Botó principal de l'aplicació
        self.run_btn = QPushButton("EXECUTAR ANÀLISI")
        self.run_btn.setObjectName("runBtn")
        self.run_btn.clicked.connect(self._on_run)
        v.addWidget(self.run_btn)

        v.addSpacing(16)
        v.addWidget(_hsep())
        v.addSpacing(8)

        # Etiqueta d'estat que dona feedback a l'usuari (errors, nº nodes, etc.)
        self.status_label = QLabel("Carrega una topologia per començar.")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        v.addWidget(self.status_label)

        v.addStretch()  # empeny tots els elements cap a la part superior
        return sidebar

    def _build_main(self) -> QFrame:
        """Construeix el panell principal amb les sis pestanyes de la UI."""
        main = QFrame()
        main.setObjectName("mainPanel")
        v = QVBoxLayout(main)
        v.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_graph_tab(), "Graf")
        self.tabs.addTab(self._build_report_tab(), "Informe")
        self.tabs.addTab(self._build_cycles_tab(), "Cicles")
        self.tabs.addTab(self._build_stats_tab(), "Estadístiques")
        self.tabs.addTab(self._build_all_paths_tab(), "Tots els camins")
        self.tabs.addTab(self._build_benchmarks_tab(), "Benchmarks")
        v.addWidget(self.tabs)
        return main

    # Construcció de les pestanyes

    def _build_graph_tab(self) -> QWidget:
        """Pestanya 1: visualització del graf de xarxa amb matplotlib embedded."""
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(8, 12, 8, 8)

        # Creem la figura de matplotlib i l'integrem com a widget de Qt
        self.fig = Figure(figsize=(10, 7), facecolor=COL_PANEL, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()
        self._draw_empty()  # missatge inicial mentre no hi ha dades

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setStyleSheet(f"background: {COL_PANEL};")
        layout.addWidget(self.canvas)
        return wrap

    def _build_report_tab(self) -> QWidget:
        """Pestanya 2: informe detallat de la ruta node per node amb scroll."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.report_holder = QWidget()
        self.report_layout = QVBoxLayout(self.report_holder)
        self.report_layout.setContentsMargins(12, 12, 12, 12)
        self.report_layout.setSpacing(10)
        self._report_placeholder()  # contingut inicial mentre no hi ha anàlisi
        scroll.setWidget(self.report_holder)
        return scroll

    def _build_cycles_tab(self) -> QWidget:
        """Pestanya 3: llista dels cicles detectats al graf per DFS."""
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
        """Pestanya 4: targetes numèriques animades + distribució de risc."""
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Grid per a les targetes de mètriques (hops, pes, risc, IDS)
        self.stats_grid_holder = QWidget()
        self.stats_grid = QGridLayout(self.stats_grid_holder)
        self.stats_grid.setHorizontalSpacing(12)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stats_grid_holder)

        # Contenidor per a les barres de distribució de risc
        self.dist_holder = QFrame()
        self.dist_holder.setObjectName("card")
        self.dist_layout = QVBoxLayout(self.dist_holder)
        self.dist_layout.setContentsMargins(18, 16, 18, 18)
        self.dist_layout.setSpacing(8)
        layout.addWidget(self.dist_holder)

        layout.addStretch()
        self._stats_placeholder()
        return wrap

    # Continguts placeholder (mentre no hi ha dades)

    def _report_placeholder(self) -> None:
        """Mostra un missatge centrat a la pestanya Informe quan no hi ha dades."""
        self._clear_layout(self.report_layout)
        lbl = QLabel("Cap anàlisi executada encara.\n\nCarrega una topologia i prem «Executar anàlisi».")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px; padding: 60px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.report_layout.addWidget(lbl)
        self.report_layout.addStretch()

    def _cycles_placeholder(self) -> None:
        """Missatge inicial per a la pestanya Cicles."""
        self._clear_layout(self.cycles_layout)
        lbl = QLabel("Cap cicle analitzat encara.")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px; padding: 60px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.cycles_layout.addWidget(lbl)
        self.cycles_layout.addStretch()

    def _stats_placeholder(self) -> None:
        """Missatge inicial per a la pestanya Estadístiques."""
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.dist_layout)
        lbl = QLabel("Executa una anàlisi per veure estadístiques.")
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 13px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.dist_layout.addWidget(lbl)

    # <-- inici us d'ia
    # _clear_layout és recursiva perquè els layouts de Qt poden contenir
    # tant widgets com altres layouts fills (QHBoxLayout dins QVBoxLayout, etc.).
    # takeAt(0) extreu l'element de la posició 0 però NO el destrueix;
    # cal cridar deleteLater() sobre els widgets per destruir-los de forma
    # segura dins l'event loop de Qt. Si usem del directament, Qt pot intentar
    # accedir a memòria ja alliberada i causar un crash (objecte C++ destruït
    # però la referència Python encara viva).
    def _clear_layout(self, layout) -> None:
        """Elimina recursivament tots els widgets i layouts fills d'un layout.

        Necessitem eliminar recursivament perquè els layouts poden contenir
        altres layouts (no només widgets), i takeAt() no els destrueix sols.
        """
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)  # treu l'element de l'índex 0 i el retorna
            w = item.widget()
            if w is not None:
                w.setParent(None)   # desconnectem del widget pare
                w.deleteLater()     # programem la destrucció segura (event loop)
            else:
                child = item.layout()
                if child is not None:
                    self._clear_layout(child)  # crida recursiva per a layouts fills
    # <-- fi us d'ia


    # Lògica de dibuix del graf (matplotlib embedded)
    def _draw_empty(self) -> None:
        """Dibuixa el missatge d'espera quan no hi ha cap graf carregat."""
        self.ax.clear()
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()
        self.ax.text(
            0.5, 0.5,
            "Carrega una topologia\nper visualitzar la xarxa",
            ha="center", va="center",
            color=COL_TEXT_DIM, fontsize=14,
            transform=self.ax.transAxes,  # coordenades relatives (0-1) dins l'eix
        )
        if hasattr(self, "canvas"):
            self.canvas.draw_idle()  # redibuja de forma asíncrona (no bloqueja la UI)

    def _on_browse(self) -> None:
        """Obre el diàleg de selecció de fitxer i carrega la topologia si l'usuari n'escull un."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecciona topologia ShadowScan",
            "", "JSON (*.json);;Tots els fitxers (*.*)",
        )
        if path:
            self.path_input.setText(path)
            self._load_topology()

    def _load_topology(self) -> None:
        """Carrega i processa el fitxer JSON de topologia seleccionat.

        El flux és:
          1. Validar que el fitxer existeix
          2. Parsejar el JSON amb NetworkParser
          3. Construir el TopologyGraph
          4. Omplir els combos d'entrada/objectiu
          5. Dibuixar el graf buit (sense ruta destacada)
        """
        topo_path = self.path_input.text().strip()
        if not topo_path or not _PathLib(topo_path).is_file():
            self._set_status("Fitxer no trobat", error=True)
            return
        try:
            parser = NetworkParser(topo_path)
            nodes, edges, default_entry, default_target = parser.load()

            self.nodes = nodes
            self.node_ids = [n.id for n in nodes]

            # Construïm el graf de NetworkX intern de RedTrace
            self.graph = TopologyGraph().build(nodes, edges)

            # El classificador d'arbre de decisió anota el risk_level de cada node
            self.classifier.annotate_nodes(nodes)

            # Omplim els desplegables amb tots els IDs de nodes
            self.entry_combo.clear()
            self.entry_combo.addItems(self.node_ids)
            self.entry_combo.setCurrentText(default_entry)

            self.target_combo.clear()
            self.target_combo.addItems(self.node_ids)
            self.target_combo.setCurrentText(default_target)

            # Dibuixem el graf sense cap ruta destacada (conjunt buit)
            self._draw_graph(set())
            self._set_status(
                f"Topologia carregada · {len(nodes)} nodes · {len(edges)} arestes"
            )
        except Exception as exc:
            self._set_status(f"Error en carregar: {exc}", error=True)
            traceback.print_exc()

    def _on_run(self) -> None:
        """Executa el pipeline complet d'anàlisi quan l'usuari prem el botó Run.

        Passos:
          1. Validar l'estat (graf carregat, entrada ≠ objectiu)
          2. Seleccionar l'estratègia de ruta
          3. Calcular la ruta
          4. Detectar cicles (DFS)
          5. Simular l'IDS
          6. Construir l'AnalysisReport
          7. Actualitzar totes les pestanyes de la GUI
        """
        if self.graph is None or not self.nodes:
            self._set_status("Carrega una topologia primer", error=True)
            return
        entry = self.entry_combo.currentText()
        target = self.target_combo.currentText()
        if entry == target:
            self._set_status("Entrada i objectiu han de ser diferents", error=True)
            return

        # Desactivem el botó mentre s'executa per evitar doble-clic
        self.run_btn.setEnabled(False)
        self.run_btn.setText("EXECUTANT...")
        QApplication.processEvents()  # forcem la actualització de la UI ara

        try:
            # Triem l'estratègia de ruta basant-nos en el botó de ràdio actiu
            if self.radio_short.isChecked():
                strategy = ShortestRoute()   # Dijkstra pel pes total mínim
            elif self.radio_safe.isChecked():
                strategy = SafestRoute()     # Dijkstra evitant nodes CRITICAL
            else:
                strategy = FewestHopsRoute() # BFS pel nombre mínim de salts

            path = strategy.select(self.graph, entry, target)
            if path is None:
                self._set_status(f"Sense ruta entre {entry} i {target}", error=True)
                return

            # Detecció de cicles sobre el graf complet (no només la ruta)
            cycles = CycleDetector(self.graph).find_cycles()

            # Simulació de l'IDS: comprova si la ruta dispara alguna firma
            ids_result = IDSSimulator().evaluate(path)

            # Construïm l'objecte informe que agrupa tots els resultats
            report = AnalysisReport(
                entry=entry, target=target, path=path,
                cycles=cycles, ids_result=ids_result,
                node_classifications={n.id: n.risk_level for n in self.nodes},
            )
            self.last_report = report

            # Actualitzem la visualització del graf destacant les arestes de la ruta
            highlighted = {(e.from_node, e.to_node) for e in path.edges}
            self._draw_graph(highlighted)

            # Actualitzem les pestanyes amb els resultats
            self._render_report(report)
            self._render_cycles(cycles)
            self._render_stats(report)
            self._update_banner(report)
            self._set_status(
                f"OK · {path.hops} salts · pes {path.total_weight:.2f}"
            )
            self.tabs.setCurrentIndex(0)  # tornem a la pestanya del graf
        except Exception as exc:
            self._set_status(f"Error: {exc}", error=True)
            traceback.print_exc()
        finally:
            # Reactivem el botó tant si ha tingut èxit com si ha fallat
            self.run_btn.setEnabled(True)
            self.run_btn.setText("EXECUTAR ANÀLISI")

    def _draw_graph(self, highlighted_edges) -> None:
        """Renderitza el graf de xarxa en el canvas de matplotlib.

        Assigna colors per risc als nodes i destaca les arestes de la ruta
        seleccionada en vermell gruixut. Usa spring_layout per al posicionament.

        El paràmetre highlighted_edges és un conjunt de tuples (u, v) que
        representa les arestes de la ruta d'atac calculada.
        """
        if self.graph is None:
            self._draw_empty()
            return

        g = self.graph.raw  # graf de NetworkX subjacent
        self.ax.clear()
        self.ax.set_facecolor(COL_PANEL)
        self.ax.set_axis_off()

        # Calculem el layout una vegada i reutilitzem per a tots els draw_networkx_*
        # seed=42 garanteix que el layout és sempre el mateix per al mateix graf
        pos = nx.spring_layout(g, seed=42, k=1.7, iterations=100)

        # Assignem un color a cada node segons el seu nivell de risc
        node_colors = []
        for nid in g.nodes:
            n = self.graph.get_node(nid)
            color = LEVEL_COLOR.get(n.risk_level, COL_TEXT_DIM) if n else COL_TEXT_DIM
            node_colors.append(color)

        # Decidim el color i el gruix de cada aresta
        edge_colors = []
        edge_widths = []
        for u, v in g.edges:
            if (u, v) in highlighted_edges:
                edge_colors.append(COL_ACCENT)  # vermell per a la ruta d'atac
                edge_widths.append(3.5)
            else:
                edge_colors.append("#3A3A48")   # gris fosc per a la resta d'arestes
                edge_widths.append(1.0)

        # Dibuixem per capes: nodes → arestes → labels → pesos
        nx.draw_networkx_nodes(
            g, pos, node_color=node_colors, node_size=950,
            edgecolors=COL_TEXT, linewidths=1.4, ax=self.ax,
        )
        nx.draw_networkx_edges(
            g, pos, edge_color=edge_colors, width=edge_widths,
            arrows=True, arrowsize=14, ax=self.ax,
            connectionstyle="arc3,rad=0.06",  # arestes corbes per distingir-les millor
        )
        nx.draw_networkx_labels(
            g, pos, font_size=8, font_weight="bold",
            font_color=COL_TEXT, ax=self.ax,
        )
        edge_labels = {(u, v): f"{g[u][v]['weight']:.2f}" for u, v in g.edges}
        nx.draw_networkx_edge_labels(
            g, pos, edge_labels=edge_labels, font_size=7,
            font_color=COL_TEXT_DIM,
            bbox=dict(facecolor=COL_PANEL, edgecolor="none", pad=1),
            ax=self.ax,
        )

        self.fig.tight_layout()
        self.canvas.draw_idle()  # refresca el canvas de Qt de forma asíncrona

    # Renderitzat de les pestanyes d'informe, cicles i estadístiques
    def _render_report(self, report: AnalysisReport) -> None:
        """Omple la pestanya Informe amb els resultats de l'anàlisi.

        Estructura visual:
          - Capçalera: ruta i mètriques globals
          - Files de nodes: índex, ID, tipus, risc i recomanacions
          - Bloc IDS: barra d'accent i text de veredicte
        """
        self._clear_layout(self.report_layout)

        # Capçalera
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

        # Files de nodes de la ruta
        for i, node in enumerate(report.path.nodes):
            row_wrap = QWidget()
            cl = QVBoxLayout(row_wrap)
            cl.setContentsMargins(0, 6, 0, 6)
            cl.setSpacing(6)

            top = QHBoxLayout()
            top.setSpacing(12)

            # Número de pas en vermell (índex de la ruta)
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

            # Recomanacions de seguretat indentades sota la fila del node
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

        # Bloc IDS
        # Usem una barra d'accent lateral (4px) en comptes d'un fons de color
        # per no sobrecarregar visualment la secció
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

        # Animem l'entrada del contingut per donar sensació de resposta immediata
        _fade_in(self.report_holder)

    def _render_cycles(self, cycles) -> None:
        """Omple la pestanya Cicles amb els cicles detectats per DFS.

        Si no n'hi ha cap, mostra un missatge de "cap cicle detectat" en verd.
        Si n'hi ha, els llista numerats en format A → B → C → A.
        """
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

            # Nodes del cicle separats per espais i fletxes per llegibilitat
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
        """Omple la pestanya Estadístiques amb targetes animades i barres de distribució.

        Targetes numèriques (animades 0 → valor real):
          - SALTS       → nombre d'arestes de la ruta
          - PES TOTAL   → suma dels pesos de les arestes
          - RISC MITJÀ  → mitjana dels risk_score dels nodes
          - IDS         → text estàtic "DETECTAT" o "NEGATIU"

        Barres de distribució: proporció de nodes LOW / MEDIUM / CRITICAL al graf.
        """
        self._clear_layout(self.stats_grid)
        self._clear_layout(self.dist_layout)

        # Color de la targeta de risc mitjà: canvia segons el rang del valor
        avg_color = (
            COL_CRITICAL if report.path.avg_risk > 0.7
            else COL_MEDIUM if report.path.avg_risk > 0.4
            else COL_SUCCESS
        )
        ids_color = COL_CRITICAL if report.ids_result.detected else COL_SUCCESS
        ids_text = "DETECTAT" if report.ids_result.detected else "NEGATIU"

        # Definim les 4 targetes: (etiqueta, valor, tipus d'animació, color)
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

            # El label del valor comença a "0" i s'anima fins al valor real
            l2 = QLabel("0" if kind != "static" else "")
            l2.setStyleSheet(
                f"color: {color}; font-size: 32px; font-weight: 800; letter-spacing: 1px;"
            )
            cl.addWidget(l1)
            cl.addWidget(l2)
            self.stats_grid.addWidget(tile, 0, c)
            self.stats_grid.setColumnStretch(c, 1)  # distribuïm l'espai equitativament

            # Llancem l'animació adequada per al tipus de dada
            if kind == "int":
                _animate_int(l2, int(value), duration=750)
            elif kind == "float":
                _animate_float(l2, float(value), duration=750)
            else:
                l2.setText(str(value))
                _fade_in(l2, duration=400)

        # Distribució de risc: una barra per nivell
        title = QLabel("DISTRIBUCIÓ DE RISC AL GRAF")
        title.setObjectName("cardLabel")
        self.dist_layout.addWidget(title)
        self.dist_layout.addSpacing(8)

        # Comptem quants nodes hi ha de cada nivell
        dist = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 0, RiskLevel.CRITICAL: 0}
        for lvl in report.node_classifications.values():
            dist[lvl] = dist.get(lvl, 0) + 1
        total = sum(dist.values()) or 1  # evitem divisió per zero

        bars: list[AnimatedBar] = []
        for level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.CRITICAL):
            row = QHBoxLayout()
            row.setSpacing(12)

            # Etiqueta de nivell (alineada i de color)
            tag = QLabel(level.value)
            tag.setFixedWidth(90)
            tag.setStyleSheet(
                f"color: {LEVEL_COLOR[level]}; font-size: 11px; "
                f"font-weight: 800; letter-spacing: 1.2px;"
            )
            row.addWidget(tag)

            # Barra animada que s'omplirà fins a la proporció calculada
            bar = AnimatedBar(LEVEL_COLOR[level], height=18)
            bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # Emmagatzemem el ratio com a propietat del widget per usar-lo després
            bar.setProperty("_targetRatio", dist[level] / total)
            row.addWidget(bar, 1)
            bars.append(bar)

            # Comptador numèric animat a la dreta de la barra
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

        # <-- inici us d'ia
        # Les barres AnimatedBar calculen l'amplada de l'emplenat en píxels reals
        # (self.width() * ratio). Però en aquest punt del codi, els widgets
        # tot just s'acaben d'afegir al layout i Qt encara no els ha assignat
        # les dimensions definitives (el layout pass és diferit).
        # Si llancem animateTo() ara, self.width() val 0 i les barres no es
        # mouen. La solució és forçar un processEvents() per executar el layout
        # pass de Qt i que els widgets tinguin amplades reals, i llavors cridar
        # _start_bars() per llançar les animacions ja amb mides correctes.
        def _start_bars():
            for b in bars:
                b.animateTo(float(b.property("_targetRatio")), duration=750)
        QApplication.instance().processEvents()
        _start_bars()
        # <-- fi us d'ia

    def _update_banner(self, report: AnalysisReport) -> None:
        """Actualitza el footer amb el resultat de l'IDS i les estadístiques.

        Si l'IDS ha detectat la ruta, el text es posa en vermell i es fa
        un efecte de parpadeig (pulse) per cridar l'atenció de l'usuari.
        """
        if report.ids_result.detected:
            n_sigs = len(report.ids_result.triggered_signatures)
            self.banner_label.setText(
                f"IDS DETECTAT   ·   {n_sigs} firma(es) activada(es)"
            )
            self.banner_label.setStyleSheet(f"color: {COL_CRITICAL};")
            self._pulse_banner(times=3)  # 3 parpadeigs per a alertes crítiques
        else:
            self.banner_label.setText("IDS NO DETECTAT   ·   ruta neta")
            self.banner_label.setStyleSheet(f"color: {COL_SUCCESS};")
            self._pulse_banner(times=1)  # 1 sol parpadeig per a confirmar l'OK

        # Actualitzem les estadístiques ràpides de la dreta
        self.banner_stats.setText(
            f"hops {report.path.hops}   ·   pes {report.path.total_weight:.2f}   "
            f"·   risc {report.path.avg_risk:.2f}"
        )

    # <-- inici us d'ia
    # _pulse_banner construeix en temps d'execució un QSequentialAnimationGroup
    # amb N*2 animacions encadenades (N baixades + N pujades d'opacitat).
    # La clau no trivial és que totes comparteixen el mateix QGraphicsOpacityEffect
    # (eff), que s'aplica al widget abans d'iniciar el grup. Si no es guarda
    # self._banner_anim, Python destrueix seq i totes les animacions abans
    # que Qt les executi (el mateix problema del GC que a _fade_in).
    def _pulse_banner(self, times: int = 2) -> None:
        """Fa parpellejar l'etiqueta del banner N vegades per cridar l'atenció.

        Usa QSequentialAnimationGroup per encadenar les animacions d'opacitat
        (baixada 1→0.35 i pujada 0.35→1) sense bloquejar el thread de la UI.
        """
        eff = QGraphicsOpacityEffect(self.banner_label)
        self.banner_label.setGraphicsEffect(eff)
        seq = QSequentialAnimationGroup(self.banner_label)

        # Afegim times parells d'animació (baixada + pujada)
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
        # Guardem referència per evitar que Python destrueixi el grup d'animació
        self._banner_anim = seq
    # <-- fi us d'ia

    def _set_status(self, text: str, error: bool = False) -> None:
        """Actualitza l'etiqueta d'estat del sidebar.

        En mode error el text apareix en vermell i en negreta; en mode normal
        s'usa el gris atenuat del tema.
        """
        self.status_label.setText(text)
        self.status_label.setObjectName("statusErr" if error else "statusOk")
        self.status_label.setStyleSheet(
            f"color: {COL_ACCENT if error else COL_TEXT_DIM};"
            f" font-size: 11px; {'font-weight: 600;' if error else ''}"
        )

    # Funcionalitats de la Fase 3 (AllPaths i Benchmarks)
    def _current_strategy_label(self) -> str:
        """Retorna una etiqueta de text per a l'estratègia de ruta seleccionada."""
        if self.radio_short.isChecked():
            return "shortest"
        if self.radio_safe.isChecked():
            return "safest"
        return "fewest-hops"

    #Pestanya "Tots els camins" (AllPathsFinder via backtracking)
    def _build_all_paths_tab(self) -> QWidget:
        """Construeix la pestanya AllPaths amb controls de profunditat i resultats.

        L'usuari pot ajustar:
          - Màx camins: límit de camins a retornar (per evitar bloquejos)
          - Profunditat màx: límit de nodes per camí (per evitar explosió)
          - Evita CRITICAL: filtra nodes de risc crític del backtracking
        """
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        # Fila de controls
        ctl = QHBoxLayout()
        ctl.setSpacing(10)

        ctl.addWidget(_field_label("Màx camins"))
        self.ap_max_paths = QSpinBox()
        self.ap_max_paths.setRange(1, 5000)
        self.ap_max_paths.setValue(50)
        self.ap_max_paths.setFixedWidth(90)
        ctl.addWidget(self.ap_max_paths)

        ctl.addSpacing(12)
        ctl.addWidget(_field_label("Profunditat màx"))
        self.ap_max_depth = QSpinBox()
        self.ap_max_depth.setRange(2, 100)
        self.ap_max_depth.setValue(10)
        self.ap_max_depth.setFixedWidth(90)
        ctl.addWidget(self.ap_max_depth)

        ctl.addSpacing(12)
        self.ap_avoid_critical = QCheckBox("Evita CRITICAL")
        ctl.addWidget(self.ap_avoid_critical)

        ctl.addStretch()
        self.ap_run_btn = QPushButton("Cercar tots els camins")
        self.ap_run_btn.setStyleSheet(
            f"background: {COL_ACCENT}; color: white; border: none;"
            f" border-radius: 6px; padding: 8px 14px; font-weight: 700;"
        )
        self.ap_run_btn.clicked.connect(self._on_run_all_paths)
        ctl.addWidget(self.ap_run_btn)
        v.addLayout(ctl)

        # Àrea de desplaçament per als resultats
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.ap_holder = QWidget()
        self.ap_layout = QVBoxLayout(self.ap_holder)
        self.ap_layout.setContentsMargins(8, 8, 8, 8)
        self.ap_layout.setSpacing(6)
        self._all_paths_placeholder()
        scroll.setWidget(self.ap_holder)
        v.addWidget(scroll, 1)

        return wrap

    def _all_paths_placeholder(self) -> None:
        """Missatge inicial de la pestanya AllPaths amb advertència de complexitat."""
        self._clear_layout(self.ap_layout)
        lbl = QLabel(
            "Carrega una topologia, tria entrada/objectiu i prem\n"
            "«Cercar tots els camins» per enumerar-los amb backtracking.\n\n"
            "⚠ Algoritme O(V!) — limita els paràmetres en grafs grans."
        )
        lbl.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 12px; padding: 40px;")
        lbl.setAlignment(Qt.AlignCenter)
        self.ap_layout.addWidget(lbl)
        self.ap_layout.addStretch()

    def _on_run_all_paths(self) -> None:
        """Executa AllPathsFinder amb els paràmetres actuals i mostra els resultats.

        Si l'opció "Evita CRITICAL" és activa, construïm un conjunt de nodes
        bloquejats (tots els CRITICAL excepte l'entrada i l'objectiu) i el passem
        al finder perquè no els visiti durant el backtracking.
        """
        if self.graph is None:
            self._set_status("Carrega una topologia primer", error=True)
            return
        entry = self.entry_combo.currentText()
        target = self.target_combo.currentText()
        if entry == target:
            self._set_status("Entrada i objectiu han de ser diferents", error=True)
            return

        self.ap_run_btn.setEnabled(False)
        self.ap_run_btn.setText("Calculant…")
        QApplication.processEvents()

        try:
            # Construïm el conjunt de nodes bloquejats si el checkbox és actiu
            blocked = set()
            if self.ap_avoid_critical.isChecked():
                blocked = {
                    n.id for n in self.graph.nodes
                    if n.risk_level == RiskLevel.CRITICAL
                    and n.id not in (entry, target)  # mai bloquem l'entrada ni el target
                }

            # Instanciem el finder i executem el backtracking
            # <-- inici us d'ia
            finder = AllPathsFinder(
                blocked_nodes=blocked,
                max_paths=self.ap_max_paths.value(),
                max_depth=self.ap_max_depth.value(),
            )
            paths = finder.find_all(self.graph, entry, target)
            # <-- fi us d'ia

            self._render_all_paths(paths, entry, target)
        except Exception as exc:
            self._set_status(f"Error AllPaths: {exc}", error=True)
            traceback.print_exc()
        finally:
            self.ap_run_btn.setEnabled(True)
            self.ap_run_btn.setText("Cercar tots els camins")

    def _render_all_paths(self, paths, entry: str, target: str) -> None:
        """Renderitza la llista de camins trobats ordenats per pes ascendent.

        Cada fila mostra: índex, mètriques (hops / pes / risc) i la seqüència
        de nodes del camí separats per fletxes.
        """
        self._clear_layout(self.ap_layout)
        if not paths:
            lbl = QLabel(f"Cap camí entre {entry} i {target}")
            lbl.setStyleSheet(f"color: {COL_ACCENT}; font-size: 13px; padding: 30px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.ap_layout.addWidget(lbl)
            self.ap_layout.addStretch()
            return

        header = QLabel(f"{len(paths)} camins trobats · {entry}  ➜  {target}")
        header.setStyleSheet(
            f"color: {COL_TEXT}; font-size: 13px; font-weight: 700; padding-bottom: 6px;"
        )
        self.ap_layout.addWidget(header)
        self.ap_layout.addWidget(_row_sep())

        # Ordenem per pes total ascendent: el camí "més barat" apareix primer
        ranked = sorted(paths, key=lambda p: p.total_weight)
        for i, p in enumerate(ranked, 1):
            row = QWidget()
            cl = QVBoxLayout(row)
            cl.setContentsMargins(0, 6, 0, 6)
            cl.setSpacing(2)

            top = QHBoxLayout()
            idx = QLabel(f"#{i:02d}")
            idx.setStyleSheet(
                f"color: {COL_ACCENT}; font-family: Consolas, monospace;"
                f" font-size: 13px; font-weight: 800; min-width: 38px;"
            )
            top.addWidget(idx)
            stats = QLabel(
                f"{p.hops} salts   ·   pes {p.total_weight:.2f}   ·   "
                f"risc mitjà {p.avg_risk:.2f}"
            )
            stats.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 11px;")
            top.addWidget(stats)
            top.addStretch()
            cl.addLayout(top)

            # Seqüència completa de nodes del camí
            seq = QLabel("  →  ".join(n.id for n in p.nodes))
            seq.setStyleSheet(
                f"color: {COL_TEXT}; font-family: Consolas, monospace; font-size: 11px;"
            )
            seq.setWordWrap(True)
            cl.addWidget(seq)

            self.ap_layout.addWidget(row)
            if i < len(ranked):
                self.ap_layout.addWidget(_row_sep())

        self.ap_layout.addStretch()

    # Pestanya "Benchmarks"

    def _build_benchmarks_tab(self) -> QWidget:
        """Construeix la pestanya Benchmarks amb botó de re-execució i visor d'imatge.

        La imatge PNG generada per benchmarks/run.py es mostra directament
        com a QPixmap. Si no existeix, es mostra un missatge d'ajuda.
        """
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        # Fila de controls
        ctl = QHBoxLayout()
        self.bench_run_btn = QPushButton("Re-executar benchmark")
        self.bench_run_btn.setStyleSheet(
            f"background: {COL_ACCENT_DARK}; color: white; border: none;"
            f" border-radius: 6px; padding: 8px 14px; font-weight: 700;"
        )
        self.bench_run_btn.clicked.connect(self._on_run_benchmark)
        ctl.addWidget(self.bench_run_btn)

        # Barra de progrés indeterminada (spinner) mentre el benchmark s'executa
        self.bench_progress = QProgressBar()
        self.bench_progress.setRange(0, 0)  # mode indeterminat (pulsant)
        self.bench_progress.setVisible(False)
        self.bench_progress.setFixedHeight(8)
        ctl.addWidget(self.bench_progress, 1)
        v.addLayout(ctl)

        self.bench_status = QLabel("")
        self.bench_status.setStyleSheet(f"color: {COL_TEXT_DIM}; font-size: 11px;")
        v.addWidget(self.bench_status)

        # Visor de la imatge PNG generada pel benchmark
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        h = QVBoxLayout(holder)
        h.setContentsMargins(0, 0, 0, 0)
        self.bench_image = QLabel()
        self.bench_image.setAlignment(Qt.AlignCenter)
        h.addWidget(self.bench_image)
        scroll.setWidget(holder)
        v.addWidget(scroll, 1)

        # Intentem carregar la imatge si ja existeix d'una execució anterior
        self._refresh_benchmark_image()
        return wrap

    def _refresh_benchmark_image(self) -> None:
        """Carrega i mostra la imatge PNG del benchmark si existeix al disc."""
        png = _PathLib("benchmarks/results.png")
        if png.is_file():
            pix = QPixmap(str(png))
            # Escalem a 900px d'amplada mantenint la proporció (SmoothTransformation)
            self.bench_image.setPixmap(pix.scaledToWidth(900, Qt.SmoothTransformation))
            self.bench_status.setText(f"Imatge: {png.resolve()}")
        else:
            # La imatge no existeix: mostrem un missatge informatiu
            self.bench_image.setText(
                "Encara no hi ha resultats.\n"
                "Prem «Re-executar benchmark» per generar-los."
            )
            self.bench_image.setStyleSheet(
                f"color: {COL_TEXT_DIM}; font-size: 13px; padding: 60px;"
            )

    def _on_run_benchmark(self) -> None:
        """Llança el mòdul de benchmark com a subprocés i refresca la imatge.

        Usem subprocess.run (bloquejant) perquè el benchmark pot trigar
        varis minuts. Durant l'execució activem la barra de progrés.

        NOTA: en producció seria millor usar QProcess (no bloqueja la UI),
        però per a un prototip acadèmic subprocess és suficient.
        """
        import subprocess
        self.bench_run_btn.setEnabled(False)
        self.bench_progress.setVisible(True)
        self.bench_status.setText("Executant… pot trigar uns minuts.")
        QApplication.processEvents()  # mostrem els canvis a la UI abans de bloquejar

        try:
            # Executem el benchmark com a mòdul Python (-m) per respectar el PYTHONPATH
            proc = subprocess.run(
                [sys.executable, "-u", "-m", "benchmarks.run"],
                capture_output=True, text=True, timeout=900,  # 15 minuts màxim
            )
            if proc.returncode != 0:
                QMessageBox.warning(
                    self, "Benchmark fallit",
                    f"Codi de sortida {proc.returncode}\n\nstderr:\n{proc.stderr[-1000:]}",
                )
            # Tant si ha tingut èxit com si no, intentem mostrar la imatge
            self._refresh_benchmark_image()
            self.bench_status.setText("Benchmark completat ✓")
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "Timeout", "El benchmark ha excedit 15 minuts.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self.bench_progress.setVisible(False)
            self.bench_run_btn.setEnabled(True)

    # Generador de topologies sintètiques
    def _on_generate_synthetic(self) -> None:
        """Obre el diàleg de configuració i genera una topologia sintètica.

        Si l'usuari confirma el diàleg, genera el JSON amb els paràmetres
        indicats, el desa a data/topology_synthetic.json i el carrega.
        """
        dlg = _SyntheticDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return  # l'usuari ha cancel·lat

        n, density, critical_ratio, seed = dlg.values()
        try:
            topo = generate_topology(
                n_nodes=n, edge_density=density,
                critical_ratio=critical_ratio, seed=seed,
            )
            out_path = _PathLib("data/topology_synthetic.json")
            save_topology(topo, str(out_path))

            # Actualitzem el camp de text i carreguem la nova topologia
            self.path_input.setText(str(out_path))
            self._load_topology()
            self._set_status(
                f"Topologia generada · N={n} · densitat={density:.2f}"
            )
        except Exception as exc:
            self._set_status(f"Error generant: {exc}", error=True)
            traceback.print_exc()


# Diàleg de configuració del generador sintètic
class _SyntheticDialog(QDialog):
    """Diàleg modal per configurar els paràmetres de la topologia sintètica.

    L'usuari pot ajustar:
      - Nombre de nodes (V): mida del graf
      - Densitat d'arestes: probabilitat que dos nodes estiguin connectats
      - Ratio CRITICAL: fracció de nodes amb risc crític
      - Seed: llavor per a resultats reproduïbles
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generar topologia sintètica")
        self.setModal(True)
        self.setMinimumWidth(360)

        # Usem QFormLayout per alinear les etiquetes i els camps automàticament
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

        # Botons OK / Cancel·lar estàndard de Qt
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        """Retorna els valors actuals dels camps del formulari com a tupla."""
        return (
            self.n_spin.value(),
            self.density_spin.value(),
            self.critical_spin.value(),
            self.seed_spin.value(),
        )


# Punt d'entrada de la GUI
def main() -> None:
    """Inicialitza l'aplicació Qt i mostra la finestra principal de RedTrace."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # estil base consistent entre plataformes (Win/Mac/Linux)
    win = RedTraceWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
