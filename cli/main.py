"""Punt d'entrada de la línia de comandes de RedTrace."""

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="redtrace",
        description="Simulador de moviment lateral en xarxes corporatives",
    )
    p.add_argument("--topology", default="data/topology_mock.json",
                   help="Fitxer JSON de topologia (default: data/topology_mock.json)")
    p.add_argument("--entry", required=True, help="IP d'entrada de l'atac")
    p.add_argument("--target", required=True, help="IP objectiu")
    p.add_argument("--strategy", choices=["shortest", "safest"], default="shortest",
                   help="Estratègia de ruta (default: shortest)")
    p.add_argument("--report-dir", default="./out",
                   help="Directori on desar els informes (default: ./out)")
    p.add_argument("--no-plot", action="store_true",
                   help="Desactiva la visualització matplotlib")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not Path(args.topology).is_file():
        print(f"[ERROR] No s'ha trobat el fitxer de topologia: {args.topology}")
        sys.exit(1)

    print(f"[RedTrace] Topologia: {args.topology}")
    print(f"[RedTrace] Entry: {args.entry}  →  Target: {args.target}")
    print(f"[RedTrace] Estratègia: {args.strategy}")
    # TODO: carregar topologia, executar anàlisi i generar informe


if __name__ == "__main__":
    main()
