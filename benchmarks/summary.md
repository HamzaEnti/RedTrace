# Resum de benchmarks RedTrace

Repeticions per cas: **3**.

| V | E | Dijkstra | Safest | BFS | DFS cicles | AllPaths |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 16 | 0.02 ms | 0.02 ms | 0.01 ms | 0.02 ms | 0.02 ms |
| 25 | 71 | 0.02 ms | 0.02 ms | 0.01 ms | 0.08 ms | — |
| 50 | 226 | 0.07 ms | 0.05 ms | 0.02 ms | 2.11 ms | — |
| 100 | 853 | 0.22 ms | 0.31 ms | 0.09 ms | 62.52 ms | — |
| 250 | 5234 | 1.09 ms | 0.77 ms | 0.16 ms | 6077.91 ms | — |
| 500 | 20407 | 4.75 ms | 3.40 ms | 0.56 ms | 263814.59 ms | — |

**Observacions:** els temps creixen segons la complexitat teòrica.
AllPaths explota fins i tot amb topologies petites; per això el cap és V ≤ 15.