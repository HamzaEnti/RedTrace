"""Visualització matplotlib del graf amb la ruta d'atac destacada.

Aquest mòdul s'utilitza des del pipeline CLI (main.py) per generar
una imatge PNG del graf de xarxa amb la ruta d'atac ressaltada en vermell.
En la GUI (gui.py) es fa servir matplotlib directament integrat a Qt,
però aquí el backend és 'Agg' (sense finestra) per poder desar a fitxer.
"""

from pathlib import Path as _PathLib
from typing import Set, Tuple

# Forçem el backend no interactiu d'Agg ABANS d'importar pyplot.
# Si no ho fem aquí, matplotlib pot intentar obrir una finestra gràfica
# i fallar en entorns sense display (p. ex. servidors o CI/CD).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import networkx as nx

# Importem les classes del motor de RedTrace
from engine.graph import TopologyGraph
from engine.risk import make_classifier
from engine.types import Path


class TopologyVisualizer:
    """Genera una imatge PNG del graf de topologia amb la ruta d'atac destacada.

    La classe rep el graf ja construït i exposa un únic mètode públic
    (plot) que renderitza la visualització i la desa a disc.
    """

    def __init__(self, graph: TopologyGraph):
        # Guardem la referència al graf per accedir-hi des de plot()
        self.graph = graph

    def plot(self, path: Path, output_path: str, title: str = "RedTrace") -> None:
        """Renderitza el graf i el desa com a imatge PNG.

        Paràmetres:
          path        → la ruta d'atac calculada (Dijkstra / BFS / Safest)
          output_path → ruta de sortida del fitxer PNG
          title       → títol de la figura (per defecte "RedTrace")

        El procés és:
          1. Calcular les posicions dels nodes (layout)
          2. Assignar colors per nivell de risc
          3. Diferenciar arestes de la ruta (vermell gros) vs. la resta (gris prim)
          4. Dibuixar nodes, arestes, etiquetes i pesos
          5. Afegir llegenda i desar
        """

        # Obtenim el graf de NetworkX que hi ha darrere de TopologyGraph
        g = self.graph.raw

        # Pas 1: layout de spring.
        # spring_layout simula forces de repulsió/atracció entre nodes.
        # seed=42 garanteix reproduïbilitat; k i iterations ajusten l'espaiat.
        pos = nx.spring_layout(g, seed=42, k=1.5, iterations=80)

        # Pas 2: colors dels nodes per nivell de risc.
        # Cada node té un risk_level (LOW/MEDIUM/CRITICAL); el classificador
        # ens retorna el color hexadecimal corresponent (verd/taronja/vermell).
        node_colors = []
        for nid in g.nodes:
            node = self.graph.get_node(nid)
            # Si el node existeix al graf, usem el seu color de risc;
            # si per algun motiu no el trobem, posem gris com a fallback
            color = make_classifier(node.risk_level).get_color() if node else "#888"
            node_colors.append(color)

        # Pas 3: colors i gruixos de les arestes.
        # Construïm un conjunt d'arestes que pertanyen a la ruta d'atac
        # per poder fer la comprovació en O(1) dins el bucle.
        path_edges: Set[Tuple[str, str]] = {(e.from_node, e.to_node) for e in path.edges}

        edge_colors = []
        edge_widths = []
        for u, v in g.edges:
            if (u, v) in path_edges:
                # Aresta de la ruta d'atac → vermell fosc i línia gruixuda
                edge_colors.append("#D32F2F")
                edge_widths.append(3.0)
            else:
                # Aresta de fons → gris clar i línia prima
                edge_colors.append("#BDBDBD")
                edge_widths.append(1.0)

        # Pas 4: dibuix de tots els elements del graf.
        # Creem una figura gran per tenir prou espai per als labels.
        plt.figure(figsize=(13, 9))

        # Dibuixem els nodes amb el color de risc i una vora negra
        nx.draw_networkx_nodes(
            g, pos,
            node_color=node_colors,
            node_size=1100,
            edgecolors="black"  # vora per distingir nodes adjacents del mateix color
        )

        # Dibuixem les arestes amb colors i gruixos calculats al pas 3
        nx.draw_networkx_edges(
            g, pos,
            edge_color=edge_colors,
            width=edge_widths,
            arrows=True,        # graf dirigit → fletxes de direcció
            arrowsize=14
        )

        # Afegim etiquetes de text sobre cada node (l'ID del node)
        nx.draw_networkx_labels(g, pos, font_size=8, font_weight="bold")

        # Afegim el pes de cada aresta al seu centre (format 2 decimals)
        edge_labels = {(u, v): f"{g[u][v]['weight']:.2f}" for u, v in g.edges}
        nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=7)

        # Pas 5: llegenda i desament.
        # Construïm la llegenda manualment amb scatter (nodes) i plot (aresta ruta).
        legend_handles = [
            plt.scatter([], [], c="#4CAF50", s=120, label="LOW"),
            plt.scatter([], [], c="#FF9800", s=120, label="MEDIUM"),
            plt.scatter([], [], c="#F44336", s=120, label="CRITICAL"),
            # L'[0] extreu el Line2D de la llista que retorna plt.plot()
            plt.plot([], [], color="#D32F2F", linewidth=3, label="Ruta d'atac")[0],
        ]
        plt.legend(handles=legend_handles, loc="upper left")
        plt.title(title)
        plt.axis("off")       # amaguem els eixos numèrics (no aporten informació aquí)
        plt.tight_layout()    # ajustem els marges per evitar que els labels es retallin

        # Creem el directori de sortida si no existeix i desem la imatge
        out = _PathLib(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out, dpi=120, bbox_inches="tight")  # dpi alt per a presentacions
        plt.close()  # alliberem la memòria de la figura (important en processos llargs)
