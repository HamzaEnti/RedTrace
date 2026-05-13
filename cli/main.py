"""Punt d'entrada CLI: orquestra tot el pipeline de RedTrace."""

import argparse
import sys
from pathlib import Path as _PathLib

from engine.decision_tree import DecisionTreeRiskClassifier
from engine.dfs import CycleDetector
from engine.graph import TopologyGraph
from engine.ids_sim import IDSSimulator
from engine.route_strategy import SafestRoute, ShortestRoute
from engine.types import AnalysisReport
from report.generator import JSONReport, TextReport
from scanner.parser import NetworkParser


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="redtrace",
        description="Simulador de moviment lateral en xarxes corporatives",
    )
    parser.add_argument("--topology", required=True, help="Fitxer JSON de ShadowScan")
    parser.add_argument("--entry", default=None, help="IP del punt d'entrada (sobreescriu el del JSON)")
    parser.add_argument("--target", default=None, help="IP de l'objectiu (sobreescriu el del JSON)")
    parser.add_argument(
        "--strategy",
        default="shortest",
        choices=("shortest", "safest"),
        help="Estratègia de selecció de ruta",
    )
    parser.add_argument("--report-dir", default="out", help="Directori de sortida")
    parser.add_argument("--no-plot", action="store_true", help="Desactiva la visualització")
    return parser.parse_args(argv)


def run(argv=None) -> int:
    args = _parse_args(argv)

    np_parser = NetworkParser(args.topology)
    if not NetworkParser.exists(args.topology):
        print(f"[error] No es troba la topologia: {args.topology}", file=sys.stderr)
        return 2
    nodes, edges, default_entry, default_target = np_parser.load()

    entry = args.entry or default_entry
    target = args.target or default_target

    graph = TopologyGraph().build(nodes, edges)

    classifier = DecisionTreeRiskClassifier()
    classifier.annotate_nodes(nodes)

    cycles = CycleDetector(graph).find_cycles()

    strategy = ShortestRoute() if args.strategy == "shortest" else SafestRoute()
    path = strategy.select(graph, entry, target)
    if path is None:
        print(f"[error] No s'ha trobat ruta entre {entry} i {target}", file=sys.stderr)
        return 3

    ids_result = IDSSimulator().evaluate(path)

    report = AnalysisReport(
        entry=entry,
        target=target,
        path=path,
        cycles=cycles,
        ids_result=ids_result,
        node_classifications={n.id: n.risk_level for n in nodes},
    )

    out_dir = _PathLib(args.report_dir)
    JSONReport().generate(report, str(out_dir / "report.json"))
    TextReport().generate(report, str(out_dir / "report.txt"))

    if not args.no_plot:
        from report.visualizer import TopologyVisualizer

        TopologyVisualizer(graph).plot(
            path, str(out_dir / "topology.png"), title=f"RedTrace · {entry} → {target}"
        )

    print(
        f"Ruta {entry} -> {target}: {len(path.nodes)} nodes, "
        f"{path.hops} salts, pes {path.total_weight:.2f}"
    )
    print(
        f"IDS: {'DETECTAT' if ids_result.detected else 'NO DETECTAT'} - {ids_result.message}"
    )
    print(f"Cicles detectats: {len(cycles)}")
    print(f"Informes desats a {out_dir}/")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
