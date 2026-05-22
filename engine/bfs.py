"""
Breadth-First Search per trobar el camí amb menys salts entrada→objectiu.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, List, Optional, Set

from engine.base import AttackPathFinder
from engine.graph import TopologyGraph
from engine.types import Edge, Node, Path


class BFSFinder(AttackPathFinder):
    """Troba el camí amb el menor nombre d'arestes (hops). (WIP)"""

    def __init__(self, blocked_nodes: Optional[Set[str]] = None):
        self.blocked_nodes: Set[str] = blocked_nodes or set()

    def find_path(
        self, graph: TopologyGraph, entry: str, target: str
    ) -> Optional[Path]:
        # TODO: implementació BFS amb deque + visited + previous (Dia 2)
        return None