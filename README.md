# RedTrace v2.0

Simulador de moviment lateral en xarxes corporatives — projecte de l'assignatura **ADAA** (ENTI-UB, 2025-26).

## Equip

| Persona | Branca | Mòdul |
|---|---|---|
| Hamza  | `feat/scanner-engine` | ShadowScan bridge, Dijkstra, AllPaths, generador sintètic |
| Oscar  | `feat/vpn-routing`    | DFS cicles, RouteStrategy (Shortest/Safest/FewestHops), BFS |
| Nico   | `feat/risk-ids`       | Arbre de decisió ID3, IDS simulator, documentació formal |
| Gerard | `feat/report-cli`     | Informes, CLI, GUI Qt6, benchmarks |

## Novetats v2.0 (Fase 2 + 3)

- **Nous algoritmes:** BFS (`engine.bfs`), enumeració de camins simples per backtracking (`engine.all_paths`)
- **Nova estratègia de ruta:** `FewestHopsRoute` (menor nombre de salts, ignorant pesos)
- **Generador de topologies sintètiques** (`scanner.synthetic`) per a tests i benchmarks
- **Benchmarks empírics** (`benchmarks/run.py`) amb gràfica log-log i CSV
- **GUI ampliada:** tabs "All Paths" i "Benchmarks", radio selector d'algoritme, diàleg de topologia sintètica
- **Documentació formal:** anàlisi de complexitat (best/avg/worst), diagrames UML, diagrames de flux mermaid
- **+27 tests** (12 → 39)

## Requisits

- Python 3.12 (3.11 també funciona)
- `pip install -r requirements.txt`

Dependencies principals: `networkx`, `matplotlib`, `scikit-learn`, `pandas`, `numpy`, `pytest`, `PySide6`.

## Ús

```powershell
# CLI
python -m cli.main --topology data/topology_mock.json --no-plot

# GUI (sense finestra de consola)
pythonw -m cli.gui

# Tests
python -m pytest Tests -q

# Benchmark
python -m benchmarks.run
```

## Estructura

```
RedTrace/
├── engine/        # Motor: Dijkstra, BFS, AllPaths, DFS, IDS, decision tree
├── scanner/       # Parser, normalizer, generador sintètic
├── cli/           # Entrada CLI + GUI Qt6
├── report/        # Generador d'informes + visualitzador
├── benchmarks/    # Runner empíric + plots
├── Tests/         # 39 tests pytest
├── docs/          # UML, complexity, flow, presentation, future_work
└── data/          # Topologies d'exemple
```

## Documentació addicional

- `docs/complexity_analysis.md` — anàlisi formal de complexitat
- `docs/uml/` — diagrames de classes i paquets
- `docs/flow/` — flowcharts mermaid dels algoritmes
- `docs/presentation_phase3.md` — slides de la presentació
- `docs/future_work.md` — propostes de millora
- `benchmarks/summary.md` — resum empíric dels temps mesurats

## Llicència

Vegeu `LICENSE`.
