# Dia 6 · 17:00 · Gerard — GUI v5 polish + MERGE final + tag v2.0

## Pas 1: Commit GUI v5 a `feat/report-cli`

```powershell
git checkout feat/report-cli

# Copia cli/gui.py d'aquesta carpeta al teu repo
# Diferencia respecte v4 (commit del Dia 5): el títol de la finestra deixa
# de tenir "[BETA]" — això és el "polish" final.

git add cli/gui.py
git commit -m "feat(gui): final polish — remove [BETA] tag from window title"
```

## Pas 2: Sync develop a la branca (per resoldre qualsevol conflicte abans del merge final)

```powershell
git merge develop --no-ff -m "chore: sync develop into feat/report-cli before final merge"
```

Si hi ha conflictes:
- Probablement a `cli/gui.py` (imports d'`engine` actualitzats per Hamza/Oscar).
- Resol manualment mantenint els imports de `engine.all_paths`, `engine.bfs`, `engine.route_strategy.FewestHopsRoute`, `scanner.synthetic`.

## Pas 3: Merge final `feat/report-cli` → `develop`

```powershell
git checkout develop
git merge feat/report-cli --no-ff -m "chore: merge feat/report-cli (benchmarks + gui v2 + docs report)"
```

## Pas 4: Merge `develop` → `main` i tag v2.0

```powershell
git checkout main
git merge develop --no-ff -m "release: RedTrace v2.0 — fase 2+3 (benchmarks, BFS, AllPaths, GUI v2)"
git tag -a v2.0 -m "RedTrace v2.0 (fase 2+3): synthetic topology, BFS, AllPaths backtracking, benchmarks, GUI ampliada"
```

## Pas 5: Push a remote

```powershell
git push origin main develop --tags
```

També es poden netejar les branques locals si voleu:

```powershell
git branch -d feat/scanner-engine feat/vpn-routing feat/risk-ids feat/report-cli
git push origin --delete feat/scanner-engine feat/vpn-routing feat/risk-ids feat/report-cli
```

## Verificació final

```powershell
git log --oneline --graph --all -20
git tag
python -m pytest Tests -q     # han de passar 39 tests
python -m benchmarks.run       # genera CSV + PNG actualitzats
python -m cli.gui              # arrenca la GUI (6 tabs: Graf, Informe, Cicles, Estadístiques, AllPaths, Benchmarks)
```

🎉 **RedTrace v2.0 alliberat.**
