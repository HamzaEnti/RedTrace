"""Benchmark runner de RedTrace (WIP - skeleton).

Versió inicial: només esquelet amb constants i un main() buit.
La implementació arribarà al commit `complete-benchmark-csv-and-plot` (Dia 2).
"""

from __future__ import annotations

import sys
from typing import Dict, List


# Mides de prova (placeholder — ampliarà al Dia 2)
SIZES = [10, 25, 50]
REPEATS = 3


def _log(msg: str) -> None:
    print(msg, flush=True)


def run() -> List[Dict]:
    """Executa el sweep de benchmarks. (WIP)"""
    # TODO: per cada N en SIZES, mesurar Dijkstra/Safest/BFS/DFS-cicles/AllPaths
    return []


def main() -> None:
    _log("[bench] WIP - implementació prevista al Dia 2")
    _ = run()


if __name__ == "__main__":
    main()
