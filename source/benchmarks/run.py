"""Benchmark de tots els algoritmes principals de RedTrace."""
from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path as _PathLib
from typing import Callable, Dict, List

import matplotlib.pyplot as plt

from source.engine.all_paths import AllPathsFinder
from source.engine.bfs import BFSFinder
from source.engine.dfs import CycleDetector
from source.engine.dijkstra import DijkstraFinder
from source.engine.graph import TopologyGraph
from source.engine.route_strategy import SafestRoute
from source.engine.types import Edge, Node
from source.scanner.synthetic import generate_topology


"""Mides de graf i paràmetres globals del benchmark"""
SIZES = [10, 25, 50, 100, 250, 500]
REPEATS = 3
ALL_PATHS_CAP = 15
ALL_PATHS_MAX_PATHS = 50
ALL_PATHS_MAX_DEPTH = 8
# El nombre de cicles simples en grafs densos pot ser exponencial.
# Cap per evitar que el DFS exploti en N=250 o N=500.
CYCLES_MAX = 500


def _log(msg: str) -> None:
    """Imprimeix un missatge per stdout sense buffer"""
    print(msg, flush=True)


def _build_graph(n: int, seed: int = 42):
    """Construeix un TopologyGraph sintètic de n nodes i en retorna entry/target"""
    topo = generate_topology(n_nodes=n, edge_density=0.08, critical_ratio=0.2, seed=seed)
    nodes = [
        Node(
            id=d["id"], type=d["type"], ports=d["ports"],
            services=d["services"], risk=d["risk"],
        )
        for d in topo["nodes"]
    ]
    edges = [
        Edge(from_node=e["from"], to_node=e["to"], weight=e["weight"])
        for e in topo["edges"]
    ]
    return TopologyGraph().build(nodes, edges), topo["entry_point"], topo["target"]


def _time(fn: Callable[[], object], repeats: int) -> tuple[float, float]:
    """Executa fn R cops i retorna (mitjana, desviació estàndard) en segons"""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    mean = statistics.mean(samples)
    stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return mean, stdev


def run() -> List[Dict]:
    """Executa tots els algoritmes per a cada mida i retorna la taula de resultats"""
    results: List[Dict] = []

    for n in SIZES:
        _log(f"[bench] preparing N={n}...")
        graph, entry, target = _build_graph(n)
        _log(f"[bench] N={n}  V={graph.num_nodes()}  E={graph.num_edges()}")

        row: Dict = {"n": n, "V": graph.num_nodes(), "E": graph.num_edges()}

        _log("  - Dijkstra")
        m, s = _time(lambda: DijkstraFinder().find_path(graph, entry, target), REPEATS)
        row["dijkstra_mean"], row["dijkstra_stdev"] = m, s

        _log("  - Safest")
        m, s = _time(lambda: SafestRoute().select(graph, entry, target), REPEATS)
        row["safest_mean"], row["safest_stdev"] = m, s

        _log("  - BFS")
        m, s = _time(lambda: BFSFinder().find_path(graph, entry, target), REPEATS)
        row["bfs_mean"], row["bfs_stdev"] = m, s

        _log("  - DFS cycles")
        m, s = _time(lambda: CycleDetector(graph).find_cycles(max_cycles=CYCLES_MAX), REPEATS)
        row["dfs_cycles_mean"], row["dfs_cycles_stdev"] = m, s

        """AllPaths només per grafs petits"""
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
            row["all_paths_mean"] = None
            row["all_paths_stdev"] = None

        results.append(row)

    return results


def write_csv(results: List[Dict], path: str) -> None:
    """Escriu la taula de resultats a un fitxer CSV"""
    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)
    fields = list(results[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(r)
    _log(f"[bench] CSV -> {path}")


"""Assitencia de IA"""
def plot(results: List[Dict], path: str) -> None:
    """Genera la gràfica log-log dels temps d'execució per algoritme"""
    sizes = [r["n"] for r in results]
    series = {
        "Dijkstra O((V+E) log V)": [r["dijkstra_mean"] for r in results],
        "SafestRoute": [r["safest_mean"] for r in results],
        "BFS O(V+E)": [r["bfs_mean"] for r in results],
        "DFS cicles O(V+E)": [r["dfs_cycles_mean"] for r in results],
        f"AllPaths O(V!) (≤{ALL_PATHS_CAP})": [r["all_paths_mean"] for r in results],
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    for label, values in series.items():
        xs = [n for n, v in zip(sizes, values) if v is not None and v > 0]
        ys = [v for v in values if v is not None and v > 0]
        if xs:
            ax.plot(xs, ys, marker="o", label=label)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Nombre de nodes (V)")
    ax.set_ylabel("Temps mitjà (s)")
    ax.set_title("RedTrace — Temps d'execució per algoritme (log-log)")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    _log(f"[bench] PNG -> {path}")


def write_summary(results: List[Dict], path: str) -> None:
    """Escriu un resum en Markdown amb la taula de temps per algoritme"""
    lines = ["# Resum de benchmarks RedTrace", ""]
    lines.append(f"Repeticions per cas: **{REPEATS}**.")
    lines.append("")
    lines.append("| V | E | Dijkstra | Safest | BFS | DFS cicles | AllPaths |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        ap = (
            f"{r['all_paths_mean']*1000:.2f} ms"
            if r["all_paths_mean"] is not None else "—"
        )
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
    lines.append("AllPaths explota fins i tot amb topologies petites; per això el "
                 f"cap és V ≤ {ALL_PATHS_CAP}.")

    _PathLib(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    _log(f"[bench] Summary -> {path}")
"""Fi assistencia de IA"""


def main() -> None:
    """Punt d'entrada: executa benchmarks i escriu CSV, PNG i resum"""
    _log(f"[bench] sizes={SIZES} repeats={REPEATS}")
    results = run()
    write_csv(results, "source/benchmarks/results.csv")
    plot(results, "source/benchmarks/results.png")
    write_summary(results, "source/benchmarks/summary.md")
    _log("[bench] done.")


if __name__ == "__main__":
    main()