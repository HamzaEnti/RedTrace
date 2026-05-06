"""Punt d'entrada de la línia de comandes de RedTrace."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="redtrace",
        description="Simulador de moviment lateral en xarxes corporatives",
    )
    p.add_argument("--topology", required=True, help="Fitxer JSON de topologia")
    p.add_argument("--entry", required=True, help="IP d'entrada de l'atac")
    p.add_argument("--target", required=True, help="IP objectiu")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    # TODO: connectar amb engine
    print(f"RedTrace — topologia: {args.topology}")
    print(f"Entry: {args.entry}  →  Target: {args.target}")
    print("Engine pendent d'implementació.")


if __name__ == "__main__":
    main()
