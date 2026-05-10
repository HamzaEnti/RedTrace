"""Arbre de decisió ID3 (entropia) per classificar el risc dels nodes.

S'entrena amb un dataset sintètic de ~200 files generat segons regles de
seguretat de moviment lateral. Si el CSV no existeix, es genera al primer ús.
"""

from pathlib import Path as _PathLib
from typing import List

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from engine.base import RiskClassifier
from engine.risk import make_classifier
from engine.types import Node, RiskLevel

FEATURE_COLS = (
    "has_smb",
    "has_rdp",
    "has_telnet",
    "has_ssh",
    "has_http",
    "has_db",
    "num_ports",
)
DEFAULT_DATASET_PATH = _PathLib("data") / "risk_dataset.csv"
DB_SERVICES = {"mysql", "postgres", "postgresql", "oracle", "mssql", "mongo", "mongodb"}

def _label_from_rules(
    has_smb: int,
    has_rdp: int,
    has_telnet: int,
    has_ssh: int,
    has_http: int,
    has_db: int,
    num_ports: int,
) -> str:
    if has_telnet:
        return "CRITICAL"
    if has_db and num_ports >= 4:
        return "CRITICAL"
    if has_smb and has_rdp:
        return "CRITICAL"
    if has_smb and num_ports >= 5:
        return "CRITICAL"
    if has_db:
        return "MEDIUM"
    if has_smb or has_rdp:
        return "MEDIUM"
    if num_ports >= 5:
        return "MEDIUM"
    return "LOW"


def generate_synthetic_dataset(
    output_path: _PathLib = DEFAULT_DATASET_PATH,
    n_rows: int = 200,
    noise_ratio: float = 0.08,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    labels = ("LOW", "MEDIUM", "CRITICAL")
    for _ in range(n_rows):
        has_smb = int(rng.random() < 0.40)
        has_rdp = int(rng.random() < 0.30)
        has_telnet = int(rng.random() < 0.15)
        has_ssh = int(rng.random() < 0.55)
        has_http = int(rng.random() < 0.50)
        has_db = int(rng.random() < 0.20)
        num_ports = int(rng.integers(1, 9))

        label = _label_from_rules(
            has_smb, has_rdp, has_telnet, has_ssh, has_http, has_db, num_ports
        )
        if rng.random() < noise_ratio:
            label = str(rng.choice(labels))

        rows.append(
            {
                "has_smb": has_smb,
                "has_rdp": has_rdp,
                "has_telnet": has_telnet,
                "has_ssh": has_ssh,
                "has_http": has_http,
                "has_db": has_db,
                "num_ports": num_ports,
                "label": label,
            }
        )

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def _extract_features(node: Node) -> List[int]:
    services = {s.lower() for s in node.services.values()}
    has_smb = int("smb" in services or 445 in node.ports)
    has_rdp = int("rdp" in services or 3389 in node.ports)
    has_telnet = int("telnet" in services or 23 in node.ports)
    has_ssh = int("ssh" in services or 22 in node.ports)
    has_http = int(
        "http" in services
        or "https" in services
        or 80 in node.ports
        or 443 in node.ports
    )
    has_db = int(any(s in DB_SERVICES for s in services))
    return [has_smb, has_rdp, has_telnet, has_ssh, has_http, has_db, len(node.ports)]


class DecisionTreeRiskClassifier:
    """Embolcalla un DecisionTreeClassifier de scikit-learn. WIP."""

    def __init__(self, dataset_path: _PathLib = DEFAULT_DATASET_PATH):
        self.dataset_path = dataset_path
        self.model = DecisionTreeClassifier(criterion="entropy", random_state=42)
        self._trained: bool = False

    def ensure_trained(self) -> None:
        if self._trained:
            return
        if not self.dataset_path.exists():
            generate_synthetic_dataset(self.dataset_path)
        df = pd.read_csv(self.dataset_path)
        x = df[list(FEATURE_COLS)].to_numpy()
        y = df["label"].to_numpy()
        self.model.fit(x, y)
        self._trained = True

    def classify(self, node: Node) -> RiskLevel:
        self.ensure_trained()
        features = np.array([_extract_features(node)])
        prediction = self.model.predict(features)[0]
        return RiskLevel(str(prediction))  
    def get_classifier(self, node: Node) -> RiskClassifier:
        return make_classifier(self.classify(node))

    def annotate_nodes(self, nodes: List[Node]) -> None:
        for n in nodes:
            n.risk_level = self.classify(n)    
