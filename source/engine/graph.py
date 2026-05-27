"""Estructura de graf dirigit i ponderat construïda sobre networkx."""

from typing import Dict, Iterable, List, Optional

import networkx as nx

from source.engine.types import Edge, Node


class TopologyGraph:
    """Embolcalla un DiGraph de networkx amb metadades de RedTrace."""

    def __init__(self):
        self._g: nx.DiGraph = nx.DiGraph()
        self._nodes: Dict[str, Node] = {}

    def add_node(self, node: Node) -> None:
        self._nodes[node.id] = node
        self._g.add_node(node.id, data=node)

    def add_edge(self, edge: Edge) -> None:
        self._g.add_edge(edge.from_node, edge.to_node, weight=edge.weight)

    def build(self, nodes: Iterable[Node], edges: Iterable[Edge]) -> "TopologyGraph":
        for n in nodes:
            self.add_node(n)
        for e in edges:
            self.add_edge(e)
        return self

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    @property
    def nodes(self) -> List[Node]:
        return list(self._nodes.values())

    @property
    def node_ids(self) -> List[str]:
        return list(self._nodes.keys())

    def neighbors(self, node_id: str) -> List[str]:
        return list(self._g.successors(node_id))

    def edge_weight(self, u: str, v: str) -> Optional[float]:
        if self._g.has_edge(u, v):
            return self._g[u][v]["weight"]
        return None

    @property
    def raw(self) -> nx.DiGraph:
        return self._g

    def num_nodes(self) -> int:
        return self._g.number_of_nodes()

    def num_edges(self) -> int:
        return self._g.number_of_edges()
