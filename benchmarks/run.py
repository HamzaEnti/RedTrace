"""Benchmark de tots els algoritmes principals de RedTrace.

Mesura el temps mitjà (sobre R repeticions) d'executar:
    - Dijkstra (ShortestRoute)
    - SafestRoute (Dijkstra + filtre)
    - BFS (FewestHopsRoute)
    - DFS de detecció de cicles
    - AllPathsFinder (només per grafs petits, és O(V!))

Genera:
    benchmarks/results.csv   — taula amb temps mitjans
    benchmarks/results.png   — gràfica log-log
    benchmarks/summary.md    — resum textual

Ús:
    python -m benchmarks.run
"""

from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path as _PathLib
from typing import Callable, Dict, List

import matplotlib.pyplot as plt

# Importem tots els algoritmes que volem benchmarcar
from engine.all_paths import AllPathsFinder
from engine.bfs import BFSFinder
from engine.dfs import CycleDetector
from engine.dijkstra import DijkstraFinder
from engine.graph import TopologyGraph
from engine.route_strategy import SafestRoute
from engine.types import Edge, Node
from scanner.synthetic import generate_topology


# Paràmetres globals del benchmark

# Mides de graf que provarem (V = nombre de nodes)
SIZES = [10, 25, 50, 100, 250, 500]

# Quantes vegades executem cada algoritme per mida per calcular la mitjana.
# Amb 3 repeticions tenim prou variabilitat sense fer el benchmark massa lent.
REPEATS = 3

# AllPaths és O(V!) → EXPLOTA ràpidament. Posem un límit molt conservador.
ALL_PATHS_CAP = 15           # màxim V per al qual executem AllPaths
ALL_PATHS_MAX_PATHS = 50     # nombre màxim de camins a retornar
ALL_PATHS_MAX_DEPTH = 8      # profunditat màxima de backtracking


def _log(msg: str) -> None:
    """Imprimeix un missatge de progrés amb flush immediat.

    El flush és important perquè, si la sortida va a un pipe o a un
    subprocés (com fa la GUI), els missatges apareguin en temps real.
    """
    print(msg, flush=True)


def _build_graph(n: int, seed: int = 42):
    """Genera una topologia sintètica de n nodes i la converteix a TopologyGraph.

    Fa servir generate_topology() del mòdul scanner.synthetic, que crea
    nodes, arestes i punts d'entrada/sortida de forma determinista (seed).

    Retorna:
        (graph, entry_point, target)  — el graf i els dos extrems de la ruta
    """
    # Generem la topologia com a diccionari Python (nodes + arestes + metadades)
    topo = generate_topology(n_nodes=n, edge_density=0.08, critical_ratio=0.2, seed=seed)

    # Convertim els dicts de nodes a objectes Node tipats
    nodes = [
        Node(
            id=d["id"], type=d["type"], ports=d["ports"],
            services=d["services"], risk=d["risk"],
        )
        for d in topo["nodes"]
    ]

    # Convertim els dicts d'arestes a objectes Edge tipats
    edges = [
        Edge(from_node=e["from"], to_node=e["to"], weight=e["weight"])
        for e in topo["edges"]
    ]

    # Construïm el TopologyGraph i retornem juntament amb l'entrada i l'objectiu
    return TopologyGraph().build(nodes, edges), topo["entry_point"], topo["target"]


def _time(fn: Callable[[], object], repeats: int) -> tuple[float, float]:
    """Mesura el temps d'execució d'una funció sobre un nombre de repeticions.

    Executa fn() exactament `repeats` vegades, mesura cada execució amb
    perf_counter (alta resolució) i retorna la mitjana i la desviació estàndard.

    Retorna:
        (mean_seconds, stdev_seconds)
    """
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()                                      # executem la funció a mesurar
        samples.append(time.perf_counter() - t0)  # acumulem el temps transcorregut

    mean = statistics.mean(samples)
    # Si només tenim 1 mostra, stdev no té sentit (divisió per 0); posem 0.0
    stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return mean, stdev


# Funció principal de benchmark
def run() -> List[Dict]:
    """Executa tots els benchmarks per a cada mida de graf definida a SIZES.

    Per a cada mida V:
      1. Genera el graf sintètic
      2. Executa cada algoritme REPEATS vegades
      3. Desa la mitjana i la desviació en un diccionari de fila

    Retorna la llista de files (una per mida de graf).
    """
    results: List[Dict] = []

    for n in SIZES:
        _log(f"[bench] preparing N={n}...")
        graph, entry, target = _build_graph(n)
        _log(f"[bench] N={n}  V={graph.num_nodes()}  E={graph.num_edges()}")

        # Iniciem la fila amb les mètriques bàsiques del graf
        row: Dict = {"n": n, "V": graph.num_nodes(), "E": graph.num_edges()}

        # Dijkstra — camí mínim. Complexitat O((V+E) log V).
        _log("  - Dijkstra")
        m, s = _time(lambda: DijkstraFinder().find_path(graph, entry, target), REPEATS)
        row["dijkstra_mean"], row["dijkstra_stdev"] = m, s

        # SafestRoute — Dijkstra amb filtre de nodes CRITICAL. Similar en complexitat
        # però pot explorar menys nodes si n'hi ha molts de bloquejats.
        _log("  - Safest")
        m, s = _time(lambda: SafestRoute().select(graph, entry, target), REPEATS)
        row["safest_mean"], row["safest_stdev"] = m, s

        # BFS — cerca en amplada per trobar la ruta amb menys salts. O(V+E).
        _log("  - BFS")
        m, s = _time(lambda: BFSFinder().find_path(graph, entry, target), REPEATS)
        row["bfs_mean"], row["bfs_stdev"] = m, s

        # DFS detecció de cicles — DFS sobre tot el graf per trobar cicles. O(V+E).
        _log("  - DFS cycles")
        m, s = _time(lambda: CycleDetector(graph).find_cycles(), REPEATS)
        row["dfs_cycles_mean"], row["dfs_cycles_stdev"] = m, s

        # AllPaths — enumera TOTS els camins simples entre entry i target.
        # La complexitat és factorial (O(V!)) → MOLT perillós amb grafs grans.
        # Per això només l'executem si V ≤ ALL_PATHS_CAP.
        if n <= ALL_PATHS_CAP:
            _log("  - AllPaths (backtracking)")
            m, s = _time(
                lambda: AllPathsFinder(
                    max_paths=ALL_PATHS_MAX_PATHS,
                    max_depth=ALL_PATHS_MAX_DEPTH,
                ).find_all(graph, entry, target),
                REPEATS,
            )
            row["all_paths_mean"], row["all_paths_stdev"] = m, s
        else:
            # Per a grafs grans, marquem amb None per indicar que no s'ha executat
            row["all_paths_mean"] = None
            row["all_paths_stdev"] = None

        results.append(row)

    return results


# Funcions d'exportació de resultats

def write_csv(results: List[Dict], path: str) -> None:
    """Exporta els resultats del benchmark a un fitxer CSV.

    Utilitza la llista de claus de la primera fila per determinar les
    columnes, de manera que s'adapta automàticament si afegim camps nous.
    """
    # Creem el directori de sortida si no existeix
    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)

    fields = list(results[0].keys())  # capçalera = claus del primer diccionari
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r)
    _log(f"[bench] CSV -> {path}")


def plot(results: List[Dict], path: str) -> None:
    """Genera la gràfica log-log de temps d'execució per algoritme.

    Cada sèrie és un algoritme; l'eix X és el nombre de nodes V (log)
    i l'eix Y és el temps mitjà en segons (log). La representació log-log
    permet veure visualment la diferència de creixement entre O(n log n),
    O(n) i O(n!).
    """
    sizes = [r["n"] for r in results]

    # Definim les sèries que volem representar: nom → llista de temps (pot tenir None)
    series = {
        "Dijkstra O((V+E) log V)": [r["dijkstra_mean"] for r in results],
        "SafestRoute": [r["safest_mean"] for r in results],
        "BFS O(V+E)": [r["bfs_mean"] for r in results],
        "DFS cicles O(V+E)": [r["dfs_cycles_mean"] for r in results],
        f"AllPaths O(V!) (≤{ALL_PATHS_CAP})": [r["all_paths_mean"] for r in results],
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    for label, values in series.items():
        # Filtrem els punts None i els zeros (log(0) no existeix) per evitar errors
        xs = [n for n, v in zip(sizes, values) if v is not None and v > 0]
        ys = [v for v in values if v is not None and v > 0]
        if xs:
            ax.plot(xs, ys, marker="o", label=label)

    # Escales logarítmiques als dos eixos (log-log)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Nombre de nodes (V)")
    ax.set_ylabel("Temps mitjà (s)")
    ax.set_title("RedTrace — Temps d'execució per algoritme (log-log)")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)  # graella major i menor
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()

    # Desem la imatge i tanquem la figura per alliberar memòria
    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    _log(f"[bench] PNG -> {path}")


def write_summary(results: List[Dict], path: str) -> None:
    """Escriu un resum en format Markdown amb una taula de temps.

    El fitxer resultant es pot incloure directament a la documentació
    o visualitzar amb qualsevol visor de Markdown (GitHub, Obsidian, etc.).
    """
    lines = ["# Resum de benchmarks RedTrace", ""]
    lines.append(f"Repeticions per cas: **{REPEATS}**.")
    lines.append("")

    # Capçalera de la taula Markdown
    lines.append("| V | E | Dijkstra | Safest | BFS | DFS cicles | AllPaths |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")

    for r in results:
        # Per a AllPaths, mostrem "—" si no s'ha executat (V > ALL_PATHS_CAP)
        ap = (
            f"{r['all_paths_mean']*1000:.2f} ms"
            if r["all_paths_mean"] is not None else "—"
        )
        # Convertim de segons a mil·lisegons (x1000) per llegibilitat
        lines.append(
            f"| {r['V']} | {r['E']} | "
            f"{r['dijkstra_mean']*1000:.2f} ms | "
            f"{r['safest_mean']*1000:.2f} ms | "
            f"{r['bfs_mean']*1000:.2f} ms | "
            f"{r['dfs_cycles_mean']*1000:.2f} ms | "
            f"{ap} |"
        )

    lines.append("")
    lines.append("**Observacions:** els temps creixen segons la complexitat teòrica.")
    lines.append(
        "AllPaths explota fins i tot amb topologies petites; per això el "
        f"cap és V ≤ {ALL_PATHS_CAP}."
    )

    # Creem el directori i escrivim el fitxer Markdown
    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    _log(f"[bench] Summary -> {path}")


# Punt d'entrada
def main() -> None:
    """Orquestra l'execució completa del benchmark i l'exportació de resultats."""
    _log(f"[bench] sizes={SIZES} repeats={REPEATS}")

    # 1. Executem tots els benchmarks i obtenim la llista de resultats
    results = run()

    # 2. Exportem els resultats en els tres formats
    write_csv(results, "benchmarks/results.csv")
    plot(results, "benchmarks/results.png")
    write_summary(results, "benchmarks/summary.md")

    _log("[bench] done.")


if __name__ == "__main__":
    main()
