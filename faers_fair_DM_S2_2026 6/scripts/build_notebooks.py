"""Build the three Phase-1 notebooks from inline cell lists.

Run with `python scripts/build_notebooks.py`. Re-runnable: it overwrites the
existing notebooks but does not touch executed outputs (those are written by
`jupyter nbconvert --execute`).
"""
from __future__ import annotations

import json
from pathlib import Path

NB_ROOT = Path(__file__).resolve().parents[1] / "notebooks"
NB_ROOT.mkdir(exist_ok=True)


def _nb(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


# --- 01_eda.ipynb ----------------------------------------------------------
EDA_CELLS = [
    md("# 01 — FAERS 2026 Q1 EDA\n\nLoads all seven ASCII tables, prints shape/columns/dtypes/head, and computes baseline\nquality metrics on `DEMO` + `DRUG`. Saves four figures and a summary CSV.\n"),
    code("""\
import sys, os
from pathlib import Path
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

from src.io.loaders import load_all, TABLES

FIG = Path('figures'); FIG.mkdir(exist_ok=True)
REP = Path('reports'); REP.mkdir(exist_ok=True)
sns.set_theme(style='whitegrid')
"""),
    md("## 1. Load all seven tables"),
    code("""\
tables = load_all('data/raw/faers_ascii_2026q1')
for t in TABLES:
    df = tables[t.lower()]
    print(f'== {t} ==  shape={df.shape}')
    print('columns:', list(df.columns))
    print('dtypes:'); print(df.dtypes.to_string())
    print('head(3):'); print(df.head(3).to_string())
    print()
"""),
    md("## 2. Quality metrics on DEMO + DRUG"),
    code("""\
demo = tables['demo']
drug = tables['drug']

# (a) % missing for key DEMO fields (empty strings count as missing)
key_cols = ['age', 'sex', 'occr_country', 'reporter_country', 'occp_cod', 'event_dt']
missing_pct = (demo[key_cols].replace('', np.nan).isna().mean() * 100).round(2)
print('Missing % (DEMO key fields):'); print(missing_pct.to_string())

# (b) Version-duplicate rate at caseid level
version_dup_rate = 1 - demo['caseid'].nunique() / len(demo)
print(f'\\nVersion-duplicate rate (caseid): {version_dup_rate:.4f}')

# (c) Drug-name uniqueness
drug_unique_ratio = drug['drugname'].fillna('').nunique() / len(drug)
print(f'Drug-name uniqueness (nunique / total rows): {drug_unique_ratio:.4f}')

# (d) Reporter type distribution
reporter_dist = demo['occp_cod'].fillna('UNKNOWN').value_counts()
print('\\nReporter type distribution:'); print(reporter_dist.head(10).to_string())

# (e) Top-20 drugs and reactions
top_drugs = drug['drugname'].fillna('').str.upper().value_counts().head(20)
top_reacs = tables['reac']['pt'].fillna('').str.upper().value_counts().head(20)
print('\\nTop 20 drugs:'); print(top_drugs.to_string())
print('\\nTop 20 reactions:'); print(top_reacs.to_string())
"""),
    md("## 3. Visualizations"),
    code("""\
# 1. Missingno matrix of DEMO (sample to 50k rows for speed)
sample = demo.replace('', np.nan).sample(min(50000, len(demo)), random_state=0)
fig = msno.matrix(sample, sparkline=False).get_figure()
fig.suptitle('DEMO — missingness matrix (50k sample)', y=1.02)
fig.savefig(FIG / '01_demo_missingno_matrix.png', dpi=120, bbox_inches='tight')
plt.close(fig)
print('saved 01_demo_missingno_matrix.png')

# 2. Missingno bar chart of DEMO
fig = msno.bar(demo.replace('', np.nan)).get_figure()
fig.suptitle('DEMO — column completeness', y=1.02)
fig.savefig(FIG / '01_demo_missingno_bar.png', dpi=120, bbox_inches='tight')
plt.close(fig)
print('saved 01_demo_missingno_bar.png')

# 3. Histogram of age (years only, 0-120)
age_yrs = pd.to_numeric(demo.loc[demo['age_cod'].fillna('YR') == 'YR', 'age'], errors='coerce')
age_yrs = age_yrs[(age_yrs >= 0) & (age_yrs <= 120)]
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(age_yrs, bins=40, color='steelblue', edgecolor='white')
ax.set_xlabel('Age (years)'); ax.set_ylabel('Count'); ax.set_title('FAERS 2026 Q1 — age distribution (years)')
fig.tight_layout(); fig.savefig(FIG / '01_demo_age_hist.png', dpi=120); plt.close(fig)
print('saved 01_demo_age_hist.png  ({} valid rows)'.format(len(age_yrs)))

# 4. Reporter type bar chart
codes_meaning = {'MD':'Physician','HP':'Health Professional','PH':'Pharmacist','CN':'Consumer','LW':'Lawyer','OT':'Other','RN':'Nurse'}
rd = reporter_dist.head(10).rename(lambda c: f'{c} ({codes_meaning.get(c, "?")})')
fig, ax = plt.subplots(figsize=(8, 4))
rd.plot.barh(ax=ax, color='teal'); ax.invert_yaxis()
ax.set_title('Reporter occupation (occp_cod) — top 10'); ax.set_xlabel('Reports')
fig.tight_layout(); fig.savefig(FIG / '01_demo_reporter_dist.png', dpi=120); plt.close(fig)
print('saved 01_demo_reporter_dist.png')
"""),
    md("## 4. Persist baseline metrics"),
    code("""\
rows = []
for col, pct in missing_pct.items():
    rows.append({'metric': f'missing_pct_{col}', 'value': float(pct)})
rows += [
    {'metric': 'version_dup_rate_caseid', 'value': round(float(version_dup_rate), 6)},
    {'metric': 'drug_name_uniqueness_ratio', 'value': round(float(drug_unique_ratio), 6)},
    {'metric': 'demo_rows', 'value': len(demo)},
    {'metric': 'demo_unique_caseids', 'value': demo['caseid'].nunique()},
    {'metric': 'drug_rows', 'value': len(drug)},
    {'metric': 'distinct_drug_names_raw', 'value': drug['drugname'].fillna('').nunique()},
    {'metric': 'distinct_reactions', 'value': tables['reac']['pt'].fillna('').nunique()},
]
for code, n in reporter_dist.head(10).items():
    rows.append({'metric': f'reporter_{code}_n', 'value': int(n)})
for name, n in top_drugs.head(20).items():
    rows.append({'metric': f'top_drug::{name}', 'value': int(n)})
for name, n in top_reacs.head(20).items():
    rows.append({'metric': f'top_reaction::{name}', 'value': int(n)})

baseline = pd.DataFrame(rows)
baseline.to_csv(REP / '01_baseline_metrics.csv', index=False)
print('wrote', REP / '01_baseline_metrics.csv', f'({len(baseline)} rows)')
baseline.head(15)
"""),
]

# --- 02_quality_profile.ipynb ---------------------------------------------
QP_CELLS = [
    md("# 02 — Six-dimension quality profile\n\nCalls `src.profiling.quality_dimensions.profile_dataset` and visualizes the\nresult: a bar chart of the six dimension scores, a per-column completeness\nheatmap, and two extra plots that surface concrete issues.\n"),
    code("""\
import sys, os
from pathlib import Path
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.profiling.quality_dimensions import profile_dataset
from src.io.loaders import load_all

FIG = Path('figures'); FIG.mkdir(exist_ok=True)
REP = Path('reports'); REP.mkdir(exist_ok=True)
sns.set_theme(style='whitegrid')
"""),
    md("## 1. Compute the six quality dimensions"),
    code("""\
profile = profile_dataset('data/raw/faers_ascii_2026q1')
print(json.dumps({k: v for k, v in profile.items() if k != '_meta'}, indent=2, default=str))
"""),
    code("""\
# Persist the full profile JSON for reuse.
out_json = REP / '02_quality_profile.json'
with out_json.open('w') as f:
    json.dump(profile, f, indent=2, default=str)
print('wrote', out_json)
"""),
    md("## 2. Bar chart — six dimension scores"),
    code("""\
dims = ['completeness', 'uniqueness', 'consistency', 'validity', 'accuracy', 'timeliness']
scores = [profile[d]['score'] for d in dims]

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(dims, scores, color=sns.color_palette('viridis', len(dims)))
for b, s in zip(bars, scores):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1, f'{s:.1f}', ha='center')
ax.set_ylim(0, 105); ax.set_ylabel('Score (0–100)'); ax.set_title('FAERS 2026 Q1 — quality dimensions')
fig.tight_layout(); fig.savefig(FIG / '02_quality_dimensions.png', dpi=120); plt.close(fig)
print('saved 02_quality_dimensions.png')
"""),
    md("## 3. Heatmap — completeness per column per table"),
    code("""\
per_col = profile['completeness']['per_column_pct']
# Pad to a rectangular frame for the heatmap.
all_cols = sorted({c for cols in per_col.values() for c in cols})
mat = pd.DataFrame(index=all_cols, columns=list(per_col.keys()), dtype=float)
for tname, cols in per_col.items():
    for c, pct in cols.items():
        mat.loc[c, tname] = pct

fig, ax = plt.subplots(figsize=(7, max(6, 0.22 * len(all_cols))))
sns.heatmap(mat.fillna(np.nan), annot=False, cmap='RdYlGn', vmin=0, vmax=100,
            cbar_kws={'label': '% non-null'}, ax=ax, mask=mat.isna())
ax.set_title('Completeness per column per table'); ax.set_xlabel('Table'); ax.set_ylabel('Column')
fig.tight_layout(); fig.savefig(FIG / '02_completeness_heatmap.png', dpi=120); plt.close(fig)
print('saved 02_completeness_heatmap.png')
"""),
    md("## 4. Extra plot 1 — event-to-FDA reporting lag"),
    code("""\
tables = load_all('data/raw/faers_ascii_2026q1')
demo = tables['demo']

def _to_dt(s):
    s = s.fillna('').astype(str).str.replace(r'\\D', '', regex=True)
    out = pd.to_datetime(s, format='%Y%m%d', errors='coerce')
    m6 = out.isna() & s.str.len().eq(6)
    out.loc[m6] = pd.to_datetime(s[m6], format='%Y%m', errors='coerce')
    m4 = out.isna() & s.str.len().eq(4)
    out.loc[m4] = pd.to_datetime(s[m4], format='%Y', errors='coerce')
    return out

gap = (_to_dt(demo['fda_dt']) - _to_dt(demo['event_dt'])).dt.days
gap = gap[(gap >= 0) & (gap < 365 * 5)]   # cap at 5 years for the plot
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(gap, bins=80, color='salmon', edgecolor='white')
ax.set_xlabel('Days from event to FDA receipt'); ax.set_ylabel('Reports')
ax.set_title(f'Reporting lag (median = {int(gap.median())} d, n = {len(gap):,})')
fig.tight_layout(); fig.savefig(FIG / '02_reporting_lag.png', dpi=120); plt.close(fig)
print('saved 02_reporting_lag.png')
"""),
    md("## 5. Extra plot 2 — drug-name normalization gap (top alias clusters)"),
    code("""\
import re
_PUNCT = re.compile(r'[^\\w\\s]'); _WS = re.compile(r'\\s+')
def norm(s):
    if not isinstance(s, str): return ''
    return _WS.sub(' ', _PUNCT.sub(' ', s.lower())).strip()

drug = tables['drug']
df = pd.DataFrame({
    'raw': drug['drugname'].fillna('').str.upper().str.strip(),
    'norm': drug['drugname'].fillna('').map(norm),
}).query("norm != ''")
clusters = df.groupby('norm')['raw'].nunique().sort_values(ascending=False)
top = clusters.head(15).iloc[::-1]

fig, ax = plt.subplots(figsize=(8, 5))
top.plot.barh(ax=ax, color='slateblue')
ax.set_xlabel('Distinct raw spellings collapsing to one normalized form')
ax.set_title('Top drug-name alias clusters (normalization gap)')
for i, (k, v) in enumerate(top.items()):
    ax.text(v + 0.3, i, str(int(v)), va='center')
fig.tight_layout(); fig.savefig(FIG / '02_drug_alias_clusters.png', dpi=120); plt.close(fig)
print('saved 02_drug_alias_clusters.png')
print('Top 5 clusters:'); print(clusters.head(5).to_string())
"""),
]

# --- 03_cleaning.ipynb -----------------------------------------------------
CLEAN_CELLS = [
    md("# 03 — Cleaning pipeline\n\nRuns `src.cleaning.pipeline.run_pipeline` end-to-end and displays the\nper-step audit log as a styled table."),
    code("""\
import sys, os
from pathlib import Path
PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.cleaning.pipeline import run_pipeline

cleaned = run_pipeline(
    data_dir='data/raw/faers_ascii_2026q1',
    out_dir='data/processed',
    audit_path='reports/cleaning_audit_log.csv',
)
print('Cleaned shapes:')
for t, df in cleaned.items():
    print(f'  {t:>6}  {df.shape}')
"""),
    md("## Audit log"),
    code("""\
audit = pd.read_csv('reports/cleaning_audit_log.csv')
audit
"""),
    code("""\
# Highlight rows where >0% rows were removed.
def _row_color(row):
    if row['rows_removed'] > 0:
        return ['background-color: #ffe4b5'] * len(row)
    return [''] * len(row)

audit.style.apply(_row_color, axis=1).format({'pct_change': '{:.4f}%'})
"""),
]


def main() -> None:
    nbs = {
        "01_eda.ipynb": EDA_CELLS,
        "02_quality_profile.ipynb": QP_CELLS,
        "03_cleaning.ipynb": CLEAN_CELLS,
    }
    for name, cells in nbs.items():
        path = NB_ROOT / name
        path.write_text(json.dumps(_nb(cells), indent=1))
        print(f"wrote {path}  ({len(cells)} cells)")


if __name__ == "__main__":
    main()
