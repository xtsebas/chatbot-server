# MCP Wordle Solver (Python)


Servidor **MCP** (Model Context Protocol) que resuelve **Wordle** por **entropía**.


- Sugiere la mejor jugada (máxima ganancia de información)
- Aplica feedback (verde/amarillo/gris) de forma **robusta** a letras repetidas
- Explica por qué la jugada es óptima
- Scraper opcional con **Playwright** para clones compatibles (p. ej. sitios que exponen `data-state="correct|present|absent"`)
- Alternativa para **NYT Wordle** vía *bookmarklet* (no se puede leer `localStorage` a distancia)


## Requisitos


- Python 3.10+
- `pip install -r requirements.txt`
- (Scraper) `playwright install`


```bash
python -m venv .venv && source .venv/bin/activate # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
playwright install # para el scraper
```

### Para correr demo
```bash
mcp dev server.py
```

### Para correr stdio
```bash
python3 server.py stdio
```
