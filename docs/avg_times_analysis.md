# Anàlisi de temps mitjans — Fase 3

Resultats reproduïbles del script `python -m benchmarks.run`. Topologies
sintètiques generades amb `scanner.synthetic.generate_topology(seed=42)` i
densitat 0.08. Cada cas és la mitjana de 3 execucions.

Màquina de referència: Windows 11, Python 3.12.10. Tots els temps en
mil·lisegons.

## Taula resum

| V | E | Dijkstra | SafestRoute | BFS | DFS cicles | AllPaths (cap V≤15) |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 16 | 0.02 | 0.02 | 0.01 | 0.02 | 0.02 |
| 25 | 71 | 0.02 | 0.02 | 0.01 | 0.08 | — |
| 50 | 226 | 0.07 | 0.05 | 0.02 | 2.11 | — |
| 100 | 853 | 0.22 | 0.31 | 0.09 | 62.52 | — |
| 250 | 5 234 | 1.09 | 0.77 | 0.16 | 6 077.91 | — |
| 500 | 20 407 | 4.75 | 3.40 | 0.56 | 263 814.59 | — |

## Interpretació per algoritme

### Dijkstra · O((V+E) log V)

De 10 a 500 nodes, el temps creix de 0.02 ms a 4.75 ms. La proporció (×236)
és coherent amb el creixement de E (×1275) mitigat pel factor logarítmic.
La gràfica log-log es manté quasi recta amb pendent ≈ 1, com s'espera per
a un algoritme polinòmic-logarítmic.

### SafestRoute · Dijkstra + filtre O(V)

Sorprenent: més ràpid que Dijkstra pur a partir de V=250. La causa és que
**filtrar nodes CRITICAL redueix el graf efectiu** que Dijkstra ha
d'explorar (menys arestes vàlides). El cost del filtre O(V) és menyspreable
davant del guany de tenir menys nodes a la cua.

### BFS · O(V+E)

L'algoritme més ràpid de tots: a V=500, 0.56 ms — vuit vegades més ràpid que
Dijkstra. Confirma la teoria: sense `decrease-key` i sense pes a comparar,
cada operació és O(1).

### DFS de cicles · O(V + E) ideal → empíricament molt pitjor

És l'únic algoritme que **escala malament**. De 50 a 500 nodes el temps
creix de 2 ms a 264 segons (×125 000). Cap a O(V³) en aquest experiment.

**Causes identificades:**

1. La canonicalització de cicles és O(V) per cicle (`min(rotations)`).
2. En grafs densos amb risc alt, el nombre de cicles k creix
   superlinearment amb V — empíricament k ∼ E^1.5 en el nostre cas.
3. El temps total és O(k · V), no O(V + E) com el DFS pur.

**Implicació pràctica**: el detector és apte per a xarxes de fins a ~200
nodes. Per a topologies més grans cal **podar** (límit de profunditat de
cicle, mostreig) o substituir per Tarjan SCC (O(V + E) per a components
fortament connexes, no cicles individuals).

### AllPaths · O(V!) factorial

Només l'hem mesurat fins V=15 perquè a V=25 amb la densitat 0.08 ja explota
el cap de temps. Confirma la natura factorial del backtracking.

## Conclusions

1. **Per a rutes individuals (Dijkstra, BFS, Safest)** el sistema escala
   raonablement fins als 500-1000 nodes en una màquina ordinària.
2. **El coll d'ampolla actual és la detecció de cicles** en grafs densos.
   És el principal candidat a optimitzar a la propera iteració.
3. **AllPaths és una eina d'anàlisi forense en grafs petits**, no un mòdul
   de producció. Cal documentar-ho clarament a l'API.

Vegeu [`results.png`](../benchmarks/results.png) per a la gràfica log-log
de tots els algoritmes.
