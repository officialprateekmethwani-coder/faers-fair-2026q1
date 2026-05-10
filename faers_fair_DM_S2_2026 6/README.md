# FAERS-FAIR — Data Management Course Project (SRH Munich, S2 2026)

A FAIR audit, six-dimension data-quality profile, deterministic cleaning pipeline, and property-graph analytics layer over the U.S. FDA Adverse Event Reporting System (FAERS) Quarterly Data Extract for **2026 Q1**.

**Authors:** Prateek Methwani · Chandana · Dhyan
**Course:** Data Management, SRH Hochschule München (Summer 2026)
**Submission date:** 2026-05-07

## What's in this repository

| Path | Purpose |
|---|---|
| [reports/joint_report.pdf](reports/joint_report.pdf) | Final 10-page group report (3,051-word body; 6 embedded figures) |
| [reports/joint_report.md](reports/joint_report.md) | Markdown source of the joint report |
| [reports/component_*.md](reports/) | Per-component sections (FAIR / Quality / Cleaning / Graph) |
| [reports/reflection_*.md](reports/) | Three individual reflection logs |
| [reports/qna_prep.md](reports/qna_prep.md) | Locked viva defenses (7 Q&A entries) |
| [src/](src/) | Python package: loaders, profiling, cleaning, graph, render |
| [notebooks/](notebooks/) | 5 executed Jupyter notebooks (EDA, quality profile, cleaning, graph build, graph analytics) |
| [metadata/](metadata/) | schema.org JSON-LD, Dublin Core XML, DataCite XML, persistent-ID strategy, graph schema, Gephi workflow |
| [data/processed/](data/processed/) | 7 cleaned CSV tables + 3 GEXF graph exports + summary JSON |
| [figures/](figures/) | 9 PNG figures (Phase 1 + 2 + 3 plus F-UJI screenshot) |
| [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) | Verification of the 9 mandatory deliverables |

## Headline numbers

- **F-UJI baseline:** 3 / 26 (11.5 %), "initial" maturity (full per-metric breakdown in [reports/fuji_baseline_summary.csv](reports/fuji_baseline_summary.csv))
- **Six-dimension quality profile:** completeness 78.93, uniqueness 97.50, consistency 99.24, validity 99.99, accuracy 100.00, timeliness 65.75
- **Cleaning impact:** Banda 8-criteria fingerprint deduplication removes **8.36 %** of DEMO cases (33,202 of 397,224) — see [reports/cleaning_audit_log.csv](reports/cleaning_audit_log.csv)
- **Property graph:** 70,743 nodes / 572,253 edges (50,000-case stratified sample, seed = 42)
- **Louvain modularity:** Q = **0.2941** across 71 drug-co-prescription communities

## Reproducing the project end-to-end

The project is fully reproducible from the raw FAERS release plus this codebase. Total wall-clock time on a 2024 MacBook is **~3 minutes** end-to-end.

### One-time setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Acquire the raw data

The 350 MB FAERS 2026 Q1 release is **not bundled** in this repository. Download from the FDA's public FIS dashboard:

```
https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
```

Unzip into `data/raw/faers_ascii_2026q1/` so that `data/raw/faers_ascii_2026q1/ASCII/DEMO26Q1.txt` (and the other six tables) exists.

### Regenerate every artefact

Run the following in order; each step is deterministic and uses `seed = 42`:

```bash
# 1. Cleaning pipeline (~30 s) — produces data/processed/*_clean.csv
.venv/bin/python -m src.cleaning.pipeline

# 2. Quality profile (~30 s) — produces reports/02_quality_profile.json
.venv/bin/python -m src.profiling.quality_dimensions data/raw/faers_ascii_2026q1

# 3. F-UJI parsing (instant) — produces reports/fuji_baseline_summary.csv from the JSON
.venv/bin/python scripts/parse_fuji.py

# 4. Property graph build (~6 s) — produces data/processed/faers_graph.{gexf,pkl}
.venv/bin/python -m src.graph.build_graph

# 5. Graph analytics (~14 s) — produces reports/03_*.csv + figures/03_*.png + GEXF projections
.venv/bin/python -m src.graph.analytics

# 6. HD community figure (~4 s) — produces figures/03_drug_communities_hd.png
.venv/bin/python -m src.graph.render_hd_figure

# 7. Joint report markdown (instant)
.venv/bin/python scripts/build_joint_report.py

# 8. Joint report PDF (~3 s)
.venv/bin/python scripts/build_pdf.py
```

Notebooks 01-05 in [notebooks/](notebooks/) wrap the same calls into executable Jupyter form; they are pre-executed in the repository.

### Notes on PDF rendering

The PDF is produced via `markdown-pdf` (pure Python, reportlab-backed) because no LaTeX engine and no `libpango`/`libcairo` are present on the build machine. If a LaTeX engine is available, `pandoc reports/joint_report.md -o reports/joint_report.pdf --pdf-engine=xelatex --toc -V geometry:margin=1in` produces a typographically more polished result. The embedded figures and content are identical either way.

## Out-of-scope (deferred)

- **Zenodo deposit** of the derivative dataset (post-submission paper work)
- **F-UJI re-run** against the Zenodo URL (requires the deposit to exist first)
- **RxNorm / ATC integration** for drug normalisation (documented in Component C limitations)
- **Tableau Prep flow** (confirmed unnecessary by the course team)

## Licence

The derivative artefacts in this repository are released under **CC0 1.0 Universal** (Public Domain Dedication), matching the upstream FAERS release. See [metadata/schema_org.jsonld](metadata/schema_org.jsonld) and [metadata/datacite.xml](metadata/datacite.xml) for machine-readable licence declarations.

## AI-usage declaration

Anthropic's Claude (and the Claude Code VS Code extension) were used as productivity tools for code drafting, figure scaffolding, and report drafting. All methodological decisions, citation choices, and final review and revisions were performed by the student team. The full declaration is in [reports/ai_usage_declaration.md](reports/ai_usage_declaration.md) and at the end of the joint report (Appendix A).
