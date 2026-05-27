"""Punt d'entrada CLI: orquestra tot el pipeline de RedTrace."""

import argparse
import sys
from pathlib import Path as _PathLib

from source.engine.decision_tree import DecisionTreeRiskClassifier
from source.engine.dfs import CycleDetector
from source.engine.graph import TopologyGraph
from source.engine.ids_sim import IDSSimulator
from source.engine.route_strategy import SafestRoute, ShortestRoute
from source.engine.types import AnalysisReport
from source.report.generator import JSONReport, TextReport
from source.scanner.parser import NetworkParser


def _parse_args(argv=None) -> argparse.Namespace:
    # Defineix tots els arguments que accepta el programa per línia de comandes.
    # argv=None fa que argparse llegeixi sys.argv per defecte; passar-li
    # una llista explícita és útil per als tests automatitzats.
    parser = argparse.ArgumentParser(
        prog="redtrace",
        description="Simulador de moviment lateral en xarxes corporatives",
    )

    # Argument obligatori: sense topologia no es pot fer res
    parser.add_argument("--topology", required=True, help="Fitxer JSON de ShadowScan")

    # Entrada i objectiu són opcionals; si no es passen, el JSON ja en porta uns per defecte
    parser.add_argument("--entry", default=None, help="IP del punt d'entrada (sobreescriu el del JSON)")
    parser.add_argument("--target", default=None, help="IP de l'objectiu (sobreescriu el del JSON)")

    # Limita les opcions a "shortest" i "safest" per evitar valors invàlids
    parser.add_argument(
        "--strategy",
        default="shortest",
        choices=("shortest", "safest"),
        help="Estratègia de selecció de ruta",
    )

    parser.add_argument("--report-dir", default="out", help="Directori de sortida")

    # Flag booleà: si es passa, salta la generació de la imatge PNG
    parser.add_argument("--no-plot", action="store_true", help="Desactiva la visualització")

    return parser.parse_args(argv)


def run(argv=None) -> int:
    # Parseja els arguments i comença a construir el pipeline
    args = _parse_args(argv)

    # Crea el parser però comprova l'existència del fitxer abans de carregar-lo.
    # Així el missatge d'error és més clar que el que donaria NetworkParser sol.
    np_parser = NetworkParser(args.topology)
    if not NetworkParser.exists(args.topology):
        print(f"[error] No es troba la topologia: {args.topology}", file=sys.stderr)
        return 2

    # Carrega nodes, arestes i els nodes d'entrada/objectiu per defecte del JSON
    nodes, edges, default_entry, default_target = np_parser.load()

    # Si l'usuari ha passat --entry o --target per CLI, tenen prioritat sobre els del JSON
    entry = args.entry or default_entry
    target = args.target or default_target

    # Construeix el graf i anota el nivell de risc de cada node amb l'arbre de decisió
    graph = TopologyGraph().build(nodes, edges)
    classifier = DecisionTreeRiskClassifier()
    classifier.annotate_nodes(nodes)

    # Detecta cicles sobre el graf complet abans de calcular la ruta
    cycles = CycleDetector(graph).find_cycles()

    # Selecciona l'estratègia de ruta segons el que ha passat l'usuari
    strategy = ShortestRoute() if args.strategy == "shortest" else SafestRoute()
    path = strategy.select(graph, entry, target)

    # Si no existeix cap ruta possible entre els dos nodes, surt amb error
    if path is None:
        print(f"[error] No s'ha trobat ruta entre {entry} i {target}", file=sys.stderr)
        return 3

    # Simula l'IDS sobre la ruta calculada per veure si hauria estat detectada
    ids_result = IDSSimulator().evaluate(path)

    # Agrupa tots els resultats en un únic objecte per passar als generadors d'informe
    report = AnalysisReport(
        entry=entry,
        target=target,
        path=path,
        cycles=cycles,
        ids_result=ids_result,
        # Guarda la classificació de risc de tots els nodes del graf, no només els de la ruta
        node_classifications={n.id: n.risk_level for n in nodes},
    )

    # Genera els informes JSON i text al directori de sortida
    out_dir = _PathLib(args.report_dir)
    JSONReport().generate(report, str(out_dir / "report.json"))
    TextReport().generate(report, str(out_dir / "report.txt"))

    # La generació de la imatge PNG és opcional perquè pot trigar en grafs grans
    if not args.no_plot:
        from source.report.visualizer import TopologyVisualizer
        TopologyVisualizer(graph).plot(
            path, str(out_dir / "topology.png"), title=f"RedTrace · {entry} -> {target}"
        )

    # Resum final per consola per confirmar que tot ha anat bé
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
    # raise SystemExit propaga el codi de retorn de run() com a codi de sortida
    # del procés, que és el comportament estàndard per a eines de línia de comandes
    raise SystemExit(run())


if __name__ == "__main__":
    main()