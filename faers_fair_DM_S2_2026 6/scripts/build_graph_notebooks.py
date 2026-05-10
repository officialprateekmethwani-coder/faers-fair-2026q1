"""Build the two Phase-3 graph notebooks (04_graph_build, 05_graph_analytics).

Mirrors `scripts/build_notebooks.py` so the .ipynb files can be regenerated
deterministically from this single source.
"""
from __future__ import annotations

import json
from pathlib import Path

NB_ROOT = Path(__file__).resolve().parents[1] / "notebooks"


def _nb(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t.splitlines(keepends=True)}
def code(t): return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": t.splitlines(keepends=True)}


BUILD_CELLS = [
    md("# 04 — FAERS property-graph build\n\nLoads cleaned tables, draws a stratified 50k case sample (seed = 42), and "
       "constructs a `MultiDiGraph` per the schema in [metadata/graph_schema.md](../metadata/graph_schema.md). "
       "Saves three artefacts: `data/processed/faers_graph.pkl`, `.gexf`, and `graph_summary.json`."),
    code("""\
import sys, os
from pathlib import Path
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import json
import networkx as nx
from src.graph.build_graph import build_graph, summarize, save_artifacts, show_top_degree, show_random_walks
"""),
    md("## 1. Build the graph"),
    code("""\
import time
t0 = time.time()
G = build_graph()
print(f'\\nbuild_graph runtime: {time.time()-t0:.1f}s')
print(f'  nodes={G.number_of_nodes():,}  edges={G.number_of_edges():,}')
"""),
    md("## 2. Summarise + persist"),
    code("""\
summary = summarize(G)
print(json.dumps(summary, indent=2))
save_artifacts(G, summary)
"""),
    md("## 3. Top-degree nodes + example walks"),
    code("""\
show_top_degree(G, k=10)
print()
show_random_walks(G, k=3)
"""),
]

ANALYTICS_CELLS = [
    md("# 05 — Graph analytics\n\nThree measures on the property graph built in Notebook 04:\n\n"
       "1. **Drug-Reaction weighted degree centrality** — top 50 drugs and reactions, log-log degree distribution.\n"
       "2. **Louvain community detection** on Drug-Drug co-prescription — modularity, top communities, proposed labels.\n"
       "3. **Eigenvector centrality** on the heterogeneous graph (collapsed undirected) — top 100 bridging cases.\n\n"
       "All artefacts land under [reports/](../reports) and [figures/](../figures)."),
    code("""\
import sys, os
from pathlib import Path
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import json
import pandas as pd
from src.graph.analytics import main as run_analytics
"""),
    md("## 1. Run all three measures"),
    code("""\
summary = run_analytics()
print('\\n--- driver summary ---')
print(json.dumps(summary, indent=2, default=str))
"""),
    md("## 2. Inspect outputs"),
    code("""\
print('--- top 50 drugs by weighted degree ---')
print(pd.read_csv('reports/03_top_drugs_by_degree.csv').head(15).to_string(index=False))
print()
print('--- top 50 reactions by weighted degree ---')
print(pd.read_csv('reports/03_top_reactions_by_degree.csv').head(15).to_string(index=False))
print()
print('--- top 5 communities by total weighted degree ---')
df = pd.read_csv('reports/03_louvain_communities.csv')
sizes = df.groupby('community_id').agg(n=('drug_canonical','count'), label=('drug_class_proposed','first'), sum_w=('weighted_degree','sum')).sort_values('sum_w', ascending=False).head(5)
print(sizes.to_string())
print()
print('--- top 10 bridging cases by eigenvector centrality ---')
print(pd.read_csv('reports/03_bridging_cases.csv').head(10).to_string(index=False))
"""),
    md("## 3. Display the figures"),
    code("""\
from IPython.display import Image, display
for f in ['figures/03_degree_distribution.png', 'figures/03_drug_communities.png']:
    display(Image(f))
"""),
]


def main():
    nbs = {"04_graph_build.ipynb": BUILD_CELLS, "05_graph_analytics.ipynb": ANALYTICS_CELLS}
    for name, cells in nbs.items():
        path = NB_ROOT / name
        path.write_text(json.dumps(_nb(cells), indent=1))
        print(f"wrote {path}  ({len(cells)} cells)")


if __name__ == "__main__":
    main()
