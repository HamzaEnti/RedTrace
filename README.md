# RedTrace

[![Python Version](https://img.shields.io/badge/python-3.12%2B-3776AB?style=for-the-badge&logo=python)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success?style=for-the-badge)](https://github.com/HamzaEnti/RedTrace)
[![Architecture](https://img.shields.io/badge/architecture-OOP-blue?style=for-the-badge)](https://en.wikipedia.org/wiki/Object-oriented_programming)
[![Version](https://img.shields.io/badge/version-2.0.0-purple?style=for-the-badge)](https://github.com/HamzaEnti/RedTrace/releases)

Simulador de moviment lateral en xarxes corporatives. Modela com un atacant pot desplaçar-se entre nodes d'una xarxa real o sintètica, avaluant camins òptims, classificació de risc per node i detecció IDS, a partir de topologies exportades per **ShadowScan** o generades sintèticament.

> **AVIS LEGAL**: Aquesta eina es exclusivament per a us educatiu i entorns controlats. Projecte academic de l'assignatura **ADAA** (ENTI-UB, 2025-26).

---

## Taula de Continguts

1. [Descripció General](#descripcio-general)
2. [Integrants del Grup](#integrants-del-grup)
3. [Funcionalitats Principals](#funcionalitats-principals)
4. [Integració amb ShadowScan](#integracio-amb-shadowscan)
5. [Arquitectura i Disseny OOP](#arquitectura-i-disseny-oop)
6. [Detalls Tècnics — Codi](#detalls-tecnics--codi)
7. [Anàlisi de Complexitat](#analisi-de-complexitat)
8. [Requisits del Sistema](#requisits-del-sistema)
9. [Instal·lació](#installacio)
10. [Instruccions d'Execució](#instruccions-dexecucio)
11. [Estructura del Projecte](#estructura-del-projecte)
12. [Configuració](#configuracio)
13. [Ús d'Intel·ligència Artificial](#us-dintelligencia-artificial)
14. [Roadmap](#roadmap)
15. [Autors](#autors)
16. [Enllaç Vídeo — Presentació + Demo](#enllac-video--presentacio--demo)

---

## Descripcio General

RedTrace cobreix un buit que les eines de pentesting tradicionals no adrecen: no n'hi ha prou amb detectar quins ports i serveis estan exposats a cada màquina; cal entendre com un atacant que ja ha compromès un node intern pot moure's lateralment per la xarxa fins a arribar al seu objectiu real. Els escàners de vulnerabilitats mostren punts febles aïllats, però no modelitzen la **mobilitat entre nodes** ni prioritzen les rutes des d'una perspectiva de teoria de grafs.

RedTrace resol exactament aquest problema. Pren la topologia real escaneijada per **ShadowScan** — o en genera una de sintètica per a tests i benchmarks — i simula tots els possibles camins de moviment lateral, classificant cada node per nivell de risc mitjançant un arbre de decisió ID3 i avaluant si un IDS hipotètic detectaria el moviment. El resultat és un informe detallat, en format JSON i text pla, que permet a l'analista de seguretat identificar les rutes crítiques i blindar-les de manera preventiva.

A diferència d'eines CLI tradicionals, RedTrace ofereix múltiples estratègies d'atac seleccionables en temps d'execució, visualització del graf amb matplotlib, benchmarks de rendiment algorísmic i una GUI interactiva que facilita l'anàlisi sense necessitat de conèixer els paràmetres de cada algorisme.

---

## Integrants del Grup

| Desenvolupador | Branca                | Rol                  | Responsabilitats principals |
|----------------|-----------------------|----------------------|-----------------------------|
| Hamza          | `feat/scanner-engine` | Backend Lead         | Bridge ShadowScan, generador sintètic, Dijkstra, docstrings i anàlisi de complexitat del motor |
| Oscar          | `feat/vpn-routing`    | Routing Engineer     | BFSFinder, `FewestHopsRoute`, `RouteStrategy`, tests de rutes i estratègies |
| Nico           | `feat/risk-ids`       | Data & Docs Architect| Arbre de decisió ID3, simulador IDS, anàlisi formal de complexitat, diagrames UML i diagrames de flux |
| Gerard         | `feat/report-cli`     | Frontend & QA Lead   | GUI PySide6, generació d'informes, suite de benchmarks, anàlisi de temps mitjans |

---

## Funcionalitats Principals

### Resum de Moduls

| Modul | Fitxers | Descripcio | Fase |
|-------|---------|------------|------|
| Motor d'algorismes | `engine/dijkstra.py`, `bfs.py`, `dfs.py`, `all_paths.py` | Dijkstra, BFS, DFS, backtracking, A* | Fase 1–3 |
| Estratègies de ruta | `engine/route_strategy.py` | ShortestRoute, SafestRoute, FewestHopsRoute | Fase 1–3 |
| Classificador de risc | `engine/decision_tree.py` | Arbre de decisió ID3 per nivell LOW/MEDIUM/CRITICAL | Fase 2 |
| Simulador IDS | `engine/ids_sim.py` | Taula hash de firmes, detecció de patrons d'atac | Fase 2 |
| Generador sintètic | `scanner/synthetic.py` | Topologies de N nodes amb densitat i risc configurables | Fase 3 |
| Parser ShadowScan | `scanner/parser.py`, `normalizer.py` | Ingesta del `topology.json` exportat per ShadowScan | Fase 1 |
| Informes | `report/generator.py` | Exportació JSON + text pla amb recomanacions per node | Fase 2 |
| Visualitzacio | `report/visualizer.py` | Graf amb matplotlib, codificació de colors per risc | Fase 2 |
| GUI interactiva | `cli/gui.py` | Pestanyes per algorisme, selector d'estratègia, visualitzacio | Fase 2–3 |
| Benchmarks | `benchmarks/run.py` | Temps d'execucio comparats, CSV + gràfic PNG | Fase 3 |

### Motor d'Algorismes

| Algorisme | Classe | Criteri d'optimitzacio | Complexitat promig |
|-----------|--------|------------------------|--------------------|
| Dijkstra  | `DijkstraFinder` | Minim pes acumulat (risc) | O((V+E) log V) |
| BFS       | `BFSFinder`      | Minim nombre de salts     | Θ(V+E) |
| DFS       | `CycleDetector`  | Deteccio de cicles al graf | O(V+E) |
| Backtracking | `AllPathsFinder` | Tots els camins simples possibles | O(V!) pitjor cas |
| A\*       | `AStarFinder`    | Dijkstra + heuristica de risc mig | O((V+E) log V) |

### Estratègies de Ruta

Les tres estratègies implementen la mateixa interfície `RouteStrategy` i son intercanviables en temps d'execucio sense modificar el codi client:

- **`ShortestRoute`** — ruta de menor pes total via `DijkstraFinder`. Cap restriccio sobre els nodes travessats. Modela un atacant que minimitza el risc acumulat del camí.
- **`SafestRoute`** — exclou nodes amb risc >= 0.80 i delega en `DijkstraFinder`. Modela un atacant sigilós que evita nodes crítics per no activar alertes.
- **`FewestHopsRoute`** — camí amb menys arestes via `BFSFinder`, amb opcio d'evitar crítics. Modela un atacant que prioritza velocitat (ransomware, moviment automatic).

### Classificador de Risc ID3

El classificador entrena un `DecisionTreeClassifier` de scikit-learn (criterio d'entropia, equivalent a ID3) sobre un dataset sintètic de ~200 instàncies generades a partir de regles de seguretat reals. Les features son la presència de serveis per port (SMB, RDP, Telnet, SSH, HTTP, DB) i el nombre total de ports oberts. La sortida per cada node és `LOW`, `MEDIUM` o `CRITICAL`.

| Condicio | Classificacio |
|----------|---------------|
| Telnet obert (port 23) | CRITICAL |
| BD obert + >= 4 ports  | CRITICAL |
| SMB + RDP simultanis   | CRITICAL |
| BD sense altres riscos | MEDIUM    |
| SMB o RDP sol          | MEDIUM    |
| Resta de casos         | LOW       |

### Simulador IDS

`IDSSimulator` manté una taula hash (`dict`) de signatures on cada clau és el nom de la firma i el valor és una funció `Callable[[Path], Tuple[bool, str]]`. Les quatre firmes implementades son:

| Firma | Condicio de deteccio |
|-------|---------------------|
| `long_path` | Ruta amb mes de 4 salts |
| `telnet_in_path` | Qualsevol node de la ruta te el port 23 obert |
| `consecutive_critical` | 2 o mes nodes CRITICAL consecutius |
| `high_avg_risk` | Risc mig del camí > 0.70 |

### Generador de Topologies Sintètiques

Genera grafs de N nodes amb densitat d'arestes, ràtio de nodes crítics i seed aleatori configurables. El format de sortida és idèntic al `topology.json` de ShadowScan, de manera que el pipeline complet funciona igual amb dades reals o sintètiques. Complexitat de generació: O(n²).

### Informes i Visualitzacio

Cada execucio produeix:
- `out/report.json` — informe estructurat amb metadades, pas a pas de la ruta, risc i recomanacions per node, cicles detectats i resultat IDS.
- `out/report.txt` — informe llegible en text pla amb el mateix contingut.
- PNG del graf — nodes colorejats per nivell de risc (verd/groc/vermell), ruta d'atac destacada.

---

## Integracio amb ShadowScan

RedTrace és el segon esglao d'un pipeline de dos eines desenvolupades com a projectes complementaris de l'assignatura ADAA.

### Pipeline complet

```
+---------------------+     topology.json      +---------------------+
|     ShadowScan      |  ─────────────────────> |      RedTrace       |
|  (Java · Swing)     |                         |  (Python · PySide6) |
+---------------------+                         +---------------------+
         |                                                |
  Escaneig de xarxa                             Simulacio de moviment
  Deteccio de ports                             lateral sobre el graf
  Classificacio de risc                         Informe amb ruta optima
  Export topology.json                          + deteccio IDS
```

### Com exportar des de ShadowScan

Un cop finalitzat l'escaneig al panel de Discovery de ShadowScan (v1.1 o superior), el boto **"Exportar RedTrace"** genera el fitxer `topology.json` compatible. El boto es deshabilita durant l'escaneig actiu per evitar exportacions incompletes.

Internament, ShadowScan crida `JsonExporter.saveToTopology(resultats, "topology.json")`, que infereix el tipus de cada node a partir dels ports oberts i calcula els pesos d'explotacio per aresta.

### Format topology.json (input de RedTrace)

```json
{
  "metadata": {
    "generated_by": "ShadowScan",
    "version": "1.1",
    "hosts_active": 9
  },
  "nodes": [
    {
      "id": "192.168.1.1",
      "type": "router",
      "ports": [22, 53, 80, 443],
      "services": {"22": "ssh", "53": "dns", "80": "http", "443": "https"},
      "risk": 0.30
    },
    {
      "id": "192.168.1.40",
      "type": "server",
      "ports": [23, 21, 80],
      "services": {"23": "telnet", "21": "ftp", "80": "http"},
      "risk": 0.85
    }
  ],
  "edges": [
    {"from": "192.168.1.1", "to": "192.168.1.10", "weight": 0.35},
    {"from": "192.168.1.10", "to": "192.168.1.40", "weight": 0.40}
  ],
  "entry_point": "192.168.1.1",
  "target": "192.168.1.100"
}
```

**Logica de pesos per aresta (ShadowScan)**: Telnet / SMB / RDP = pes alt (0.70–0.90), SSH / MySQL = pes mig (0.35–0.50), resta = pes baix (0.10–0.30).

### Format report.json (output de RedTrace)

```json
{
  "metadata": {
    "entry": "192.168.1.1",
    "target": "192.168.1.100",
    "total_weight": 1.15,
    "hops": 3,
    "avg_risk": 0.625,
    "ids_detected": true
  },
  "events": [
    {
      "step": 0,
      "node_id": "192.168.1.1",
      "type": "router",
      "risk_score": 0.30,
      "risk_level": "LOW",
      "ports": [22, 53, 80, 443],
      "recommendations": ["Mantenir actualitzacions periodiques del sistema operatiu"]
    },
    {
      "step": 2,
      "node_id": "192.168.1.40",
      "type": "server",
      "risk_score": 0.85,
      "risk_level": "CRITICAL",
      "ports": [23, 21, 80],
      "recommendations": [
        "AILLAR immediatament en una VLAN segregada",
        "Desactivar serveis insegurs (Telnet, SMBv1, FTP en clar)"
      ]
    },
    {
      "phase": "ids_evaluation",
      "detected": true,
      "triggered_signatures": ["telnet_in_path"],
      "message": "Node 192.168.1.40 amb Telnet (port 23) a la ruta"
    }
  ],
  "node_classifications": {
    "192.168.1.1": "LOW",
    "192.168.1.40": "CRITICAL",
    "192.168.1.100": "MEDIUM"
  }
}
```

### Exemple de report.txt

```
======================================================================
INFORME REDTRACE — ANALISI DE MOVIMENT LATERAL
======================================================================
Entrada : 192.168.1.1
Objectiu: 192.168.1.100
Pes total: 1.15  |  Salts: 3  |  Risc mitja: 0.625

-- Ruta d'atac --
  [0] 192.168.1.1  (router) — risc 0.30 · classificacio LOW
  [1] 192.168.1.10 (router) — risc 0.40 · classificacio LOW
  [2] 192.168.1.40 (server) — risc 0.85 · classificacio CRITICAL
      > AILLAR immediatament en una VLAN segregada
      > Desactivar serveis insegurs (Telnet, SMBv1, FTP en clar)
  [3] 192.168.1.100 (server) — risc 0.95 · classificacio MEDIUM

-- Cicles detectats: 1 --
  · 192.168.1.50 -> 192.168.1.100 -> 192.168.1.50

-- Avaluacio IDS --
  Resultat: DETECTAT
  Firmes activades: telnet_in_path
  Missatge: Node 192.168.1.40 amb Telnet (port 23) a la ruta
======================================================================
```

---

## Arquitectura i Disseny OOP

RedTrace implementa una arquitectura per capes amb abstraccions en cada nivell. Les classes base de `engine/base.py` defineixen els contractes que totes les implementacions concretes han de respectar, garantint polimorfisme complet i adherència al principi Open/Closed.

### Diagrama de Capes

```
+------------------------------------------------------------------+
|                          CLI / GUI                               |
|   cli/gui.py  (PySide6)         Pestanyes per algorisme,         |
|                                 selector d'estrategia, PNG graf  |
+--------------------------------+---------------------------------+
                                 | crida
+--------------------------------v---------------------------------+
|                      CAPA DE SERVEIS                            |
|   scanner/parser.py            Ingesta topology.json            |
|   scanner/normalizer.py        Normalitzacio i validacio         |
|   scanner/synthetic.py         Generador de topologies O(n^2)   |
|   report/generator.py          JSON + text pla                  |
|   report/visualizer.py         Graf matplotlib                  |
+--------------------------------+---------------------------------+
                                 | crida
+--------------------------------v---------------------------------+
|                        ENGINE (core)                            |
|                                                                 |
|   base.py  <-- ABCs: AttackPathFinder, RouteStrategy,           |
|                       RiskClassifier, ReportGenerator           |
|                                                                 |
|   AttackPathFinder (ABC)                                        |
|   +-- DijkstraFinder    minim pes, heapq, O((V+E) log V)        |
|   +-- BFSFinder         menys salts, deque, O(V+E)              |
|   +-- AStarFinder       heuristica de risc, O((V+E) log V)      |
|                                                                 |
|   RouteStrategy (ABC)                                           |
|   +-- ShortestRoute     delega en DijkstraFinder                |
|   +-- SafestRoute       filtra nodes critics + Dijkstra         |
|   +-- FewestHopsRoute   delega en BFSFinder                     |
|                                                                 |
|   CycleDetector         DFS recursiu, 3 estats per node         |
|   AllPathsFinder        backtracking pur amb yield              |
|   DecisionTreeClassifier  ID3 via scikit-learn, ~200 mostres    |
|   IDSSimulator          taula hash de firmes Callable           |
|                                                                 |
|   TopologyGraph         embolcalla nx.DiGraph amb metadades     |
|   types.py              @dataclass: Node, Edge, Path, IDSResult |
+------------------------------------------------------------------+
```

### Principis de Disseny Aplicats

**Open/Closed Principle** — `RouteStrategy` i `AttackPathFinder` estan obertes a extensio (afegir noves estratègies o algorismes) i tancades a modificacio. Afegir `YenKShortestPaths` no requereix tocar cap codi existent.

**Polimorfisme** — La GUI i la CLI seleccionen una `RouteStrategy` en temps d'execucio. `strategy.select(graph, entry, target)` retorna sempre un `Optional[Path]` independentment de la implementacio concreta.

**Encapsulament** — `TopologyGraph` embolcalla `nx.DiGraph` i n'amaga la implementacio interna. El codi client mai accedeix directament al graf de networkx; ho fa sempre a través de l'API pública (`neighbors`, `edge_weight`, `get_node`).

**Abstraccio** — `engine/base.py` defineix quatre ABCs. Les capes superiors (scanner, report, cli) depenen únicament d'aquestes interfícies, mai de les implementacions concretes.

**Dataclasses** — `Node`, `Edge`, `Path`, `IDSResult` i `AnalysisReport` son `@dataclass`, amb comparacio estructural, `__repr__` automatic i validacio de tipus en static analysis.

---

## Detalls Tecnics — Codi

### ABCs Base (`engine/base.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class AttackPathFinder(ABC):
    @abstractmethod
    def find_path(self, graph, entry: str, target: str) -> Optional["Path"]:
        ...

class RouteStrategy(ABC):
    @abstractmethod
    def select(self, graph, entry: str, target: str) -> Optional["Path"]:
        ...

class RiskClassifier(ABC):
    @property
    @abstractmethod
    def level(self) -> "RiskLevel": ...

    @abstractmethod
    def get_recommendations(self) -> List[str]: ...
```

### Dijkstra amb min-heap (`engine/dijkstra.py`)

```python
class DijkstraFinder(AttackPathFinder):
    def find_path(self, graph, entry: str, target: str) -> Optional[Path]:
        distances = {nid: float("inf") for nid in graph.node_ids}
        distances[entry] = 0.0
        previous = {nid: None for nid in graph.node_ids}
        visited: Set[str] = set()
        heap = [(0.0, entry)]

        while heap:
            current_dist, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            if u == target:
                break
            for v in graph.neighbors(u):
                if v in self.blocked_nodes or v in visited:
                    continue
                new_dist = current_dist + graph.edge_weight(u, v)
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    previous[v] = u
                    heapq.heappush(heap, (new_dist, v))

        return self._reconstruct(graph, previous, distances, entry, target)
```

### BFS amb deque (`engine/bfs.py`)

```python
class BFSFinder(AttackPathFinder):
    def find_path(self, graph, entry: str, target: str) -> Optional[Path]:
        queue = deque([entry])
        visited = {entry}
        parent: Dict[str, Optional[str]] = {entry: None}

        while queue:
            u = queue.popleft()
            if u == target:
                return self._reconstruct(graph, parent, entry, target)
            for v in graph.neighbors(u):
                if v not in visited and v not in self.blocked_nodes:
                    visited.add(v)
                    parent[v] = u
                    queue.append(v)
        return None
```

### Backtracking recursiu (`engine/all_paths.py`)

```python
class AllPathsFinder:
    def _backtrack(self, graph, u, target, current_ids, visited, results):
        if self.max_paths and len(results) >= self.max_paths:
            return
        if u == target:
            results.append(self._materialize(graph, current_ids))
            return
        for v in graph.neighbors(u):
            if v in visited or v in self.blocked_nodes:
                continue
            visited.add(v)
            current_ids.append(v)
            self._backtrack(graph, v, target, current_ids, visited, results)
            current_ids.pop()      # desfà
            visited.remove(v)      # desfà
```

El mètode `find_best()` permet aplicar qualsevol funció de cost arbitrària sobre tots els camins trobats, per exemple minimitzar el risc màxim del camí en lloc de la suma — un criteri que Dijkstra no suporta directament.

### Estratègies de Ruta (`engine/route_strategy.py`)

```python
class ShortestRoute(RouteStrategy):
    def select(self, graph, entry, target):
        return DijkstraFinder().find_path(graph, entry, target)

class SafestRoute(RouteStrategy):
    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold

    def select(self, graph, entry, target):
        blocked = {n.id for n in graph.nodes
                   if n.risk >= self.threshold and n.id not in (entry, target)}
        return DijkstraFinder(blocked_nodes=blocked).find_path(graph, entry, target)

class FewestHopsRoute(RouteStrategy):
    def select(self, graph, entry, target):
        return BFSFinder(blocked_nodes=self.blocked).find_path(graph, entry, target)
```

### Classificador de Risc ID3 (`engine/decision_tree.py`)

```python
FEATURE_COLS = ("has_smb", "has_rdp", "has_telnet", "has_ssh",
                "has_http", "has_db", "num_ports")

class DecisionTreeRiskClassifier(RiskClassifier):
    def __init__(self, node: Node):
        self._clf = DecisionTreeClassifier(criterion="entropy")
        df = self._load_or_generate_dataset()
        X, y = df[list(FEATURE_COLS)], df["label"]
        self._clf.fit(X, y)
        features = self._extract_features(node)
        self._level = RiskLevel[self._clf.predict([features])[0]]
```

### Simulador IDS amb taula hash de firmes

```python
class IDSSimulator:
    def __init__(self):
        self.signatures: Dict[str, SignatureFn] = {
            "long_path":            self._sig_long_path,
            "telnet_in_path":       self._sig_telnet_in_path,
            "consecutive_critical": self._sig_consecutive_critical,
            "high_avg_risk":        self._sig_high_avg_risk,
        }

    def evaluate(self, path: Path) -> IDSResult:
        triggered, messages = [], []
        for name, check in self.signatures.items():
            detected, msg = check(path)
            if detected:
                triggered.append(name)
                messages.append(msg)
        return IDSResult(detected=bool(triggered),
                         triggered_signatures=triggered,
                         message="; ".join(messages) or "Cap firma activada")
```

---

## Analisi de Complexitat

| Algorisme | Millor cas | Cas promig | Pitjor cas | Espai |
|-----------|-----------|------------|------------|-------|
| Dijkstra (`DijkstraFinder`) | Ω(E + V log V) | Θ((V+E) log V) | O(V² log V) graf dens | O(V+E) |
| BFS (`BFSFinder`) | Ω(1) entry==target | Θ(V+E) | O(V²) graf complet | O(V) |
| A\* (`AStarFinder`) | Ω(E + V log V) | Θ((V+E) log V) | O(V² log V) | O(V+E) |
| DFS cicles (`CycleDetector`) | Ω(V) | Θ(V+E) | O(V+E) | O(V) |
| Backtracking (`AllPathsFinder`) | Ω(V+E) | Θ(k·V) | O(V!) graf complet | O(V) |
| Generador sintetic | — | Θ(n²) | O(n²) | O(n²) |
| Classificador ID3 | Ω(log f) inferència | Θ(n·f) entrenament | O(n·f) | O(n·f) |
| IDS (`IDSSimulator`) | Ω(1) | Θ(|sigs|·V) | O(|sigs|·V) | O(1) |

On V = nodes, E = arestes, k = nombre de camins simples, n = mostres d'entrenament, f = features.

**Observacions rellevants del benchmark:**

- BFS es estrictament mes rapid que Dijkstra en grafs no ponderats o quan nomes interessa el nombre de salts — fins a 3x en topologies de 500 nodes.
- AllPathsFinder amb `max_paths=50` és manejable fins a ~30 nodes. Per a grafs mes grans, la poda evita l'explosio factorial.
- El generador sintètic mostra comportament quadratic clar a partir de n=200, consistent amb l'enumeracio de parells dirigits.

Per a la justificacio formal cas a cas, consulta [`docs/complexity_analysis.md`](docs/complexity_analysis.md).

---

## Requisits del Sistema

### Requisits de Maquinari

| Component | Minim | Recomanat |
|-----------|-------|-----------|
| Processador | Dual-core 2.0 GHz | Quad-core 2.5 GHz |
| Memoria RAM | 2 GB | 4 GB |
| Espai en disc | 200 MB | 500 MB |

### Requisits de Programari

| Component | Versio minima | Obligatori | Us |
|-----------|---------------|------------|-----|
| Python | 3.12 | Si | Interprete |
| networkx | 3.2 | Si | Estructura del graf |
| matplotlib | 3.8 | Si | Visualitzacio |
| scikit-learn | 1.4 | Si | Classificador ID3 |
| pandas | 2.2 | Si | Dataset del classificador |
| numpy | 1.26 | Si | Operacions numeriques |
| PySide6 | 6.6 | Si | GUI interactiva |
| pytest | 8.0 | Tests | Suite de tests |

---

## Installacio

### 1. Clonar el repositori

```bash
git clone https://github.com/HamzaEnti/RedTrace.git
cd RedTrace
```

### 2. Crear un entorn virtual (recomanat)

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instal·lar les dependencies

```bash
pip install -r requirements.txt
```

### 4. Verificar la instal·lacio

```bash
pytest Tests/ -v
```

Sortida esperada:

```
Tests/test_all_paths.py::test_finds_all_paths                PASSED
Tests/test_all_paths.py::test_max_paths_limit                PASSED
Tests/test_bfs.py::test_fewest_hops                          PASSED
Tests/test_bfs.py::test_avoid_critical_nodes                 PASSED
Tests/test_dijkstra.py::test_shortest_path                   PASSED
Tests/test_dijkstra.py::test_blocked_nodes                   PASSED
Tests/test_parser.py::test_load_topology                     PASSED
Tests/test_route_strategy_extra.py::test_safest_route        PASSED
Tests/test_synthetic.py::test_generate_topology              PASSED
Tests/test_synthetic.py::test_edge_density                   PASSED
```

---

## Instruccions d'Execucio

### Mode GUI (recomanat)

```bash
python cli/gui.py
```

La GUI ofereix pestanyes independents per a cada algorisme (Dijkstra, BFS, A\*, AllPaths, Benchmarks), selector d'estratègia de ruta via radio buttons, visualitzacio del graf amb codificacio de colors per risc i boto d'exportacio d'informes.

### Mode CLI amb topologia de ShadowScan

Exporta primer la topologia des de ShadowScan (boto **"Exportar RedTrace"** al panell Discovery), despres:

```bash
python -m redtrace --input topology.json --entry 192.168.1.1 --target 192.168.1.100 --strategy shortest
```

### Mode CLI amb topologia sintetica

```bash
python -m redtrace --synthetic --nodes 20 --density 0.3 --critical-ratio 0.2 --strategy safest
```

### Taula de parametres

| Parametre | Valors possibles | Valor per defecte | Descripcio |
|-----------|-----------------|-------------------|------------|
| `--input` | Path `.json` | — | Topologia exportada per ShadowScan |
| `--strategy` | `shortest`, `safest`, `fewest-hops` | `shortest` | Estrategia de ruta |
| `--entry` | IP o ID de node | `entry_point` del JSON | Node d'entrada de l'atacant |
| `--target` | IP o ID de node | `target` del JSON | Node objectiu |
| `--all-paths` | — | Desactivat | Activa backtracking per llistar tots els camins |
| `--max-paths` | Enter positiu | 100 | Limit de camins per a `--all-paths` |
| `--synthetic` | — | Desactivat | Genera topologia sintetica |
| `--nodes` | Enter positiu | 10 | Nombre de nodes (mode sintetic) |
| `--density` | 0.0 – 1.0 | 0.25 | Densitat d'arestes (mode sintetic) |
| `--critical-ratio` | 0.0 – 1.0 | 0.20 | Ratio de nodes critics (mode sintetic) |
| `--output` | Path | `out/` | Directori de sortida dels informes |

### Executar els tests

```bash
# Tots els tests
pytest Tests/ -v

# Un fitxer concret
pytest Tests/test_bfs.py -v

# Amb cobertura
pytest Tests/ --cov=engine --cov-report=term-missing
```

### Executar els benchmarks

```bash
python benchmarks/run.py
```

Genera `benchmarks/results.csv` amb els temps d'execucio i `benchmarks/results.png` amb el grafic comparatiu de tots els algorismes per a mides de graf N = 10 fins a N = 500.

---

## Estructura del Projecte

```text
RedTrace/
|
+-- cli/
|   +-- gui.py                      # Interficie grafica PySide6
|
+-- engine/                         # Motor d'algorismes (core)
|   +-- base.py                     # ABCs: AttackPathFinder, RouteStrategy,
|   |                               #       RiskClassifier, ReportGenerator
|   +-- types.py                    # Dataclasses: Node, Edge, Path,
|   |                               #              IDSResult, AnalysisReport
|   +-- graph.py                    # TopologyGraph — embolcalla nx.DiGraph
|   +-- dijkstra.py                 # DijkstraFinder — ruta de minim pes
|   +-- bfs.py                      # BFSFinder — ruta de menys salts
|   +-- dfs.py                      # CycleDetector — DFS recursiu de cicles
|   +-- ids_sim.py                  # IDSSimulator — taula hash de firmes
|   +-- decision_tree.py            # Classificador de risc ID3
|   +-- risk.py                     # Fabrica de classificadors de risc
|   +-- all_paths.py                # AllPathsFinder — backtracking recursiu
|   +-- route_strategy.py           # ShortestRoute, SafestRoute, FewestHopsRoute
|   +-- __init__.py
|
+-- scanner/                        # Ingesta de dades
|   +-- parser.py                   # NetworkParser — llegeix topology.json
|   +-- normalizer.py               # Normalitzacio i validacio de la topologia
|   +-- synthetic.py                # Generador de topologies sintetiques O(n^2)
|   +-- __init__.py
|
+-- report/                         # Generacio d'informes
|   +-- generator.py                # JSONReportGenerator + TextReportGenerator
|   +-- visualizer.py               # Visualitzacio del graf amb matplotlib
|   +-- __init__.py
|
+-- benchmarks/                     # Rendiment comparatiu
|   +-- run.py                      # Script de benchmark (N = 10..500)
|   +-- results.csv                 # Resultats numerics
|   +-- results.png                 # Grafic comparatiu
|   +-- summary.md                  # Analisi de temps mitjans
|
+-- Tests/                          # Suite de tests (pytest)
|   +-- test_all_paths.py
|   +-- test_bfs.py
|   +-- test_dijkstra.py
|   +-- test_parser.py
|   +-- test_route_strategy_extra.py
|   +-- test_synthetic.py
|   +-- __init__.py
|
+-- docs/                           # Documentacio tecnica
|   +-- complexity_analysis.md      # Analisi formal: best/avg/worst per algorisme
|   +-- new_features.md             # Propostes de noves funcionalitats (Fase 3)
|   +-- future_work.md              # Optimitzacions i treball futur
|   +-- uml/                        # Diagrames UML en Mermaid
|   |   +-- classes_RedTrace.mmd
|   |   +-- packages_RedTrace.mmd
|   +-- flow/                       # Diagrames de flux per algorisme
|       +-- dijkstra.md
|       +-- dfs_cycles.md
|       +-- all_paths.md
|       +-- ids_evaluate.md
|       +-- pipeline_cli.md
|
+-- out/                            # Sortida de l'ultima execucio
|   +-- report.json
|   +-- report.txt
|
+-- requirements.txt
+-- LICENSE
```

---

## Configuracio

### Parametres configurables

| Parametre | Valor per defecte | Fitxer | Descripcio |
|-----------|-------------------|--------|------------|
| Llindar risc CRITICAL | 0.80 | `route_strategy.py` | Nodes amb risc >= valor son considerats critics per SafestRoute i FewestHopsRoute |
| Hops maxims IDS | 4 | `ids_sim.py` | Firma `long_path`: rutes amb mes salts son detectades |
| Risc mig maxim IDS | 0.70 | `ids_sim.py` | Firma `high_avg_risk`: per sobre d'aquest valor es dispara la firma |
| Critics consecutius IDS | 2 | `ids_sim.py` | Nombre de nodes CRITICAL seguits que activen `consecutive_critical` |
| Densitat arestes sintetica | 0.25 | `synthetic.py` | Fraccio d'arestes possibles que es generen |
| Ratio critics sintetic | 0.20 | `synthetic.py` | Fraccio de nodes generats amb ports d'alt risc |
| Max paths (backtracking) | 100 | `all_paths.py` | Limit de camins per evitar explosio factorial en grafs grans |
| Dataset ID3 | `data/risk_dataset.csv` | `decision_tree.py` | Path del dataset d'entrenament; es genera automaticament si no existeix |

### Ports per nivell de risc

| Port | Servei | Nivell de risc |
|------|--------|----------------|
| 23 | Telnet | CRITICAL |
| 445 | SMB | CRITICAL |
| 3389 | RDP | CRITICAL |
| 21 | FTP | CRITICAL |
| 22 | SSH | MEDIUM |
| 3306 | MySQL | MEDIUM |
| 5432 | PostgreSQL | MEDIUM |
| 1433 | MSSQL | MEDIUM |
| 80 | HTTP | LOW |
| 443 | HTTPS | LOW |
| 53 | DNS | LOW |

---

## Us d'Intel·ligencia Artificial

Durant el desenvolupament de RedTrace s'ha fet servir Intel·ligencia Artificial com a eina de suport en els aspectes tecnics seguents:

### Arees on s'ha utilitzat IA

1. **Disseny arquitectural** *(Assisted by Claude — Anthropic)*
   - Definicio de les ABCs a `engine/base.py` i la jerarquia `AttackPathFinder -> DijkstraFinder / BFSFinder / AStarFinder`.
   - Aplicacio del patro `Strategy` a `RouteStrategy` per garantir el principi Open/Closed i permetre seleccio en temps d'execucio sense modificar el codi client.

2. **Disseny del format d'interoperabilitat**
   - Especificacio del format `topology.json` compartit entre ShadowScan i RedTrace: camps `nodes`, `edges`, `entry_point`, `target`, logica de pesos per aresta basada en el nivell de risc del port.

3. **Generacio de documentacio tecnica**
   - Estructuracio del README i de l'analisi de complexitat a `docs/complexity_analysis.md`.
   - Docstrings en format NumPy per a tots els moduls del motor amb seccions de complexitat inline.

4. **Revisio de codi i deteccio de casos limit**
   - Identificacio de condicions de cursa potencials en accessos concurrents al graf durant benchmarks.
   - Revisio de casos limit en `AllPathsFinder`: graf buit, entry == target, nodes bloquejats que aïllen l'objectiu.
   - Proposta del parametre `max_depth` a `AllPathsFinder` per acotar la recursio en grafs ciclics.

5. **Optimitzacio del backtracking**
   - Proposta d'usar `max_paths` i `max_depth` per podar l'arbre de recursio i evitar l'explosio factorial en topologies denses.
   - Disseny de `find_best()` com a complement de `find_all()` per suportar funcions de cost arbitraries.

6. **Disseny del classificador ID3**
   - Seleccio de les 7 features optimes per a la classificacio de risc (`has_smb`, `has_rdp`, `has_telnet`, `has_ssh`, `has_http`, `has_db`, `num_ports`) i generacio de les regles del dataset sintetic d'entrenament.

---

## Roadmap

### Fase 1 — Parser, Graf i Dijkstra

- [x] Parser del JSON de ShadowScan (`NetworkParser`)
- [x] Normalitzador i validador de topologia
- [x] Estructura de graf dirigit ponderat (`TopologyGraph` sobre networkx)
- [x] `DijkstraFinder` amb min-heap (`heapq`) i lazy deletion
- [x] `CycleDetector` DFS recursiu amb 3 estats i deduplicacio de cicles
- [x] Dataclasses del domini (`Node`, `Edge`, `Path`, `IDSResult`, `AnalysisReport`)
- [x] ABCs base (`AttackPathFinder`, `RouteStrategy`, `RiskClassifier`, `ReportGenerator`)

### Fase 2 — Classificador, IDS, Informes i GUI

- [x] Classificador de risc ID3 (`DecisionTreeClassifier`, dataset sintetic auto-generat)
- [x] `IDSSimulator` amb taula hash de 4 firmes
- [x] `ShortestRoute` i `SafestRoute` (2 estrategies polimorfiques)
- [x] `JSONReportGenerator` i `TextReportGenerator`
- [x] Visualitzacio del graf amb matplotlib (colors per nivell de risc)
- [x] GUI interactiva en PySide6 (pestanyes per algorisme, selector d'estrategia)
- [x] Tests unitaris de Dijkstra, parser i estrategies

### Fase 3 — AllPaths, BFS, Benchmarks i Documentacio

- [x] `AllPathsFinder` — backtracking recursiu pur amb `max_paths` i `max_depth`
- [x] `BFSFinder` + `FewestHopsRoute` — tercera estrategia polimòrfica
- [x] Generador de topologies sintetiques (`scanner/synthetic.py`)
- [x] Suite de benchmarks (N = 10..500, CSV + grafic PNG)
- [x] Analisi formal de complexitat (best/avg/worst/espai per algorisme)
- [x] Diagrames UML de classes i paquets (Mermaid)
- [x] Diagrames de flux per a cada algorisme
- [x] Ampliacio de la GUI (pestanyes AllPaths i Benchmarks)
- [x] +27 tests pytest — cobertura del nou codi de Fase 3

---

## Autors

| Desenvolupador | Rol | Responsabilitats |
|----------------|-----|------------------|
| Hamza | Backend Lead | ShadowScan bridge, generador sintetic, `DijkstraFinder`, docstrings i complexitat del motor |
| Oscar | Routing Engineer | `BFSFinder`, `FewestHopsRoute`, `RouteStrategy`, tests de rutes i estrategies |
| Nico | Data & Docs Architect | Arbre de decisio ID3, `IDSSimulator`, analisi de complexitat, diagrames UML i diagrames de flux |
| Gerard | Frontend & QA Lead | GUI PySide6, `ReportGenerator`, benchmarks, analisi de temps mitjans |

---

## Enllac Video — Presentacio + Demo

> **Video de presentacio + demo**: https://youtu.be/b9Mfy7GJy2E

---

<p align="center">
  <strong>RedTrace</strong> — Lateral Movement Simulator &nbsp;&middot;&nbsp; v2.0.0 &nbsp;&middot;&nbsp; MIT License<br>
  Projecte ADAA &nbsp;&middot;&nbsp; ENTI-UB &nbsp;&middot;&nbsp; 2025-26
</p>
