# RedTrace

Simulador de moviment lateral en xarxes corporatives. Modela la xarxa com un graf dirigit ponderat, hi cerca les rutes d'atac més probables i avalua si un IDS les detectaria.

## Integrants del grup

| Persona | Branca | Mòdul |
|---|---|---|
| Hamza  | `feat/scanner-engine` | ShadowScan bridge + Dijkstra |
| Oscar  | `feat/vpn-routing`    | DFS + RouteStrategy |
| Nico   | `feat/risk-ids`       | Arbre de decisió + IDS |
| Gerard | `feat/report-cli`     | Informes + CLI + visualització |

## Context i problemàtica

En una auditoria ofensiva, un atacant que ja ha aconseguit entrar a una xarxa corporativa s'intenta moure lateralment fins als actius més críticsV. Detectar i tallar aquestes rutes manualment és inviable en xarxes grans.

RedTrace **automatitza l'anàlisi del moviment lateral** a partir de la sortida de l'escàner **ShadowScan**:

- Calcula la ruta d'atac de menor cost entre un punt d'entrada i un objectiu.
- Classifica el risc de cada equip segons els seus ports i serveis.
- Detecta bucles a la topologia que afavoreixen la persistència.
- Simula la reacció d'un IDS davant la ruta proposada i suggereix mitigacions per nivell de risc.

L'objectiu és donar al blue team una visió previa de **quins camins seguiria un atacant i què es pot fer per tallar-los**.

## Funcionalitats principals

- **Parser de topologia**: lectura i validació del JSON de ShadowScan (nodes, ports, serveis, arestes ponderades).
- **Cerca de ruta d'atac**: Dijkstra modificat amb min-heap (`heapq`) per al camí mínim acumulat.
- **Estratègies de ruta intercanviables**: `ShortestRoute` i `SafestRoute` (evita nodes amb risc ≥ 0.80).
- **Detecció de cicles**: DFS recursiu sobre el graf dirigit.
- **Classificació de risc per node**: arbre de decisió ID3 de scikit-learn entrenat amb un dataset sintètic generat automàticament.
- **Recomanacions polimòrfiques**: `LowRisk`, `MediumRisk` i `CriticalRisk` retornen mitigacions adaptades al seu nivell.
- **Simulador d'IDS**: taula hash de 4 firmes. Ruta llarga (> 4 salts), node amb Telnet, ≥ 2 nodes CRITICAL consecutius i risc mitjà acumulat > 0.70.
- **Informes**: sortida en JSON i en text amb la ruta, els cicles i el veredicte de l'IDS.
- **Visualització**: graf interactiu amb matplotlib i interfície gràfica completa amb Qt6 (PySide6) amb tabs per a graf, informe, cicles i estadístiques.

## Dependències i instal·lació

Requereix **Python 3.12**.

```bash
git clone <repo-url>
cd RedTrace
pip install -r requirements.txt
```

Llibreries (`requirements.txt`):
- `networkx>=3.2` → graf dirigit
- `matplotlib>=3.8` → visualització
- `scikit-learn>=1.4` → arbre de decisió
- `pandas>=2.2`, `numpy>=1.26` → dataset i extracció de features
- `PySide6>=6.6` → interfície gràfica
- `pytest>=8.0` → tests

## Ús POO

El projecte aplica els quatre pilars de la programació orientada a objectes:

**Herència i classes abstractes** : `source/engine/base.py` defineix les ABC del domini:
- `AttackPathFinder` → implementat per `DijkstraFinder`
- `RouteStrategy` → implementat per `ShortestRoute` i `SafestRoute`
- `RiskClassifier` → implementat per `LowRisk`, `MediumRisk` i `CriticalRisk`
- `ReportGenerator` → implementat per `JSONReport` i `TextReport`

**Polimorfisme** : el CLI i la GUI substitueixen `ShortestRoute` per `SafestRoute` sense tocar res més del pipeline. Cada subclasse de `RiskClassifier` retorna recomanacions i colors diferents amb la mateixa interfície.

**Encapsulació** : `TopologyGraph` encapsula un `networkx.DiGraph` i exposa només l'API que necessita la resta del projecte. `DecisionTreeRiskClassifier` amaga l'entrenament del model i la generació del dataset darrere de `classify()`.

**Composició** : `IDSSimulator` agrupa les firmes de detecció en un diccionari de funcions, fàcilment ampliable sense modificar la classe.

**Dataclasses** : `Node`, `Edge`, `Path`, `IDSResult` i `AnalysisReport` (`types.py`) defineixen els tipus de domini.

## Instruccions d'execució

Totes les comandes es llencen des del directori `source/`:

```bash
cd source
```

### Interfície gràfica (recomanada)

```bash
python -m cli.gui
```

S'obre una finestra Qt6 amb tema fosc on es pot triar topologia, entrada, objectiu i estratègia, i veure el graf, l'informe, els cicles i les estadístiques en pestanyes separades.

### CLI

```bash
python -m cli.main --topology data/topology_mock.json --strategy shortest
```

Opcions disponibles:

| Flag | Descripció |
|---|---|
| `--topology` | Fitxer JSON de ShadowScan (obligatori) |
| `--entry` | IP del punt d'entrada |
| `--target` | IP de l'objectiu |
| `--strategy` | `shortest` o `safest` (per defecte `shortest`) |
| `--report-dir` | Directori de sortida (per defecte `out`) |
| `--no-plot` | Desactiva la visualització matplotlib |

### Tests

```bash
python -m pytest Tests
```

## Enllaç al vídeo

pendent

## Ús IA

pendent 
