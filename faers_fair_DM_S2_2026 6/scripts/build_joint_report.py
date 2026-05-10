"""Assemble the joint group report from individual section markdown files.

The joint report is the single submission deliverable that pulls intro,
three component sections, the graph section, and the conclusion into one
~4000-word document. References and the AI-usage appendix are appended.

Section files demote their H1 headings to H2 inside the joint report, so
each file remains a standalone artefact while the joint report has a
single H1 (the title).

Re-run with:  python scripts/build_joint_report.py
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT_MD = REPORTS / "joint_report.md"

TITLE = "FAERS-FAIR: A FAIR Audit, Quality Profile, and Property-Graph Benchmark of the FDA Adverse Event Reporting System (2026 Q1)"
AUTHORS = "Prateek Methwani, Chandana, Dhyan — SRH Hochschule München (SRH Munich), Data Management course"
SUBMISSION_DATE = "2026-05-07"

ABSTRACT = """\
The FDA Adverse Event Reporting System (FAERS) is the principal post-marketing
pharmacovigilance database in the United States, but its quarterly extracts
are published without machine-readable metadata, persistent identifiers, or
formal FAIR self-assessment. We audit the 2026 Q1 release against the FAIR
Guiding Principles using F-UJI v3.5.1 (baseline score 3 / 26 = 11.5 %, "initial"
maturity), and show that **eleven of seventeen failed metrics collapse to a
single root cause** — the absence of schema.org / Dublin Core / DCAT markup on
the FDA dashboard page. We profile the same release across six data-quality
dimensions and identify the median 125-day reporting lag — not missingness — as
the dominant quality issue. We implement a reproducible cleaning pipeline whose
Banda 8-criteria fingerprint deduplication removes **8.36 %** of cases hidden
behind multi-source re-reporting. We model the cleaned derivative as a
70,743-node, 572,253-edge property graph and report a Louvain modularity of
**0.2941** across 71 drug-co-prescription communities. The integrated benchmark
reframes FAERS as FAIR-aware infrastructure for downstream pharmacovigilance
science, with three sidecar metadata records and a derivative-DOI strategy
delivered."""

REFERENCES = """\
1. Banda JM, Evans L, Vanguri RS, Tatonetti NP, Ryan PB, Shah NH (2016).
   *A curated and standardized adverse drug event resource to accelerate drug
   safety research.* Scientific Data 3:160026.
   https://doi.org/10.1038/sdata.2016.26

2. Bean DM, Wu H, Iqbal E, Dzahini O, Ibrahim ZM, Broadbent M, Stewart R,
   Dobson RJB (2017). *Knowledge graph prediction of unknown adverse drug
   reactions and validation in electronic health records.* Scientific Reports
   7:16416. https://doi.org/10.1038/s41598-017-16674-x

3. Devaraju A, Huber R (2021). *F-UJI – An automated tool to assess the
   FAIRness of research data objects (software).* Zenodo.
   https://doi.org/10.5281/zenodo.4683989

4. Khaleel MA, Khan AH, Ghadzi SMS, Adnan AS, Abdallah QM (2022).
   *A standardized dataset of a spontaneous adverse event reporting system.*
   Healthcare (Basel) 10(3):420.

5. Kleiber W et al. (2024). *FAIR data assessment in the life sciences:
   evaluating tooling and gaps.* (As cited per project Phase-2 spec.)

6. Kreimeyer K, Foster M, Pacanowski M, et al. (2025). *Graph-based
   pharmacovigilance signal stratification on FAERS.* Journal of Biomedical
   Informatics 165:104824. https://doi.org/10.1016/j.jbi.2025.104824
   (PubMed PMID 40185299).

7. Liu R, Wei L, Zhang P (2019). *Building a FAERS-based pharmacovigilance
   knowledge graph.* PMC6309066.

8. Newman MEJ (2018). *Networks* (2nd ed.). Oxford University Press.

9. Wilkinson MD, Dumontier M, Aalbersberg IJJ, Appleton G, Axton M, Baak A,
   et al. (2016). *The FAIR Guiding Principles for scientific data management
   and stewardship.* Scientific Data 3:160018.
   https://doi.org/10.1038/sdata.2016.18
"""

# Files that contribute to the body word-count (the 4000-word limit).
BODY_FILES = [
    ("group_report_intro.md", "1. Introduction", "intro"),
    ("component_A_FAIR_assessment.md", "2. Component A — FAIR Assessment & Metadata Design", "compA"),
    ("component_B_quality_profiling.md", "3. Component B — Data Quality & Profiling", "compB"),
    ("component_C_cleaning_pipeline.md", "4. Component C — Cleaning Pipeline", "compC"),
    ("component_graph_section.md", "5. Property Graph & Analytics", "graph"),
    ("group_report_conclusion.md", "6. Conclusion", "conc"),
]

# Files that DO NOT contribute to the 4000-word body cap (per assignment guideline).
EXCLUDED_FROM_CAP = ["abstract", "references", "appendix"]


def demote_h1_strip(md: str) -> str:
    """Demote the leading H1 in a section file (we replace it with our heading)."""
    lines = md.splitlines()
    out = []
    found_h1 = False
    for ln in lines:
        if not found_h1 and ln.startswith("# "):
            found_h1 = True
            continue  # skip — replaced by our numbered section heading
        out.append(ln)
    text = "\n".join(out).lstrip("\n")
    return text


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def main() -> None:
    parts: list[str] = []

    parts.append(f"# {TITLE}\n")
    parts.append(f"**Authors:** {AUTHORS}  ")
    parts.append(f"**Date:** {SUBMISSION_DATE}\n")
    parts.append("---\n")

    parts.append("## Abstract\n")
    parts.append(ABSTRACT.strip() + "\n")
    parts.append("\n---\n")

    body_word_total = 0
    body_breakdown: list[tuple[str, int]] = []

    for fname, heading, key in BODY_FILES:
        src = (REPORTS / fname).read_text()
        cleaned = demote_h1_strip(src)
        wc = count_words(cleaned)
        body_breakdown.append((heading, wc))
        body_word_total += wc
        parts.append(f"## {heading}\n")
        parts.append(cleaned.strip() + "\n")
        parts.append("\n")

    parts.append("---\n")
    parts.append("## References\n")
    parts.append(REFERENCES.strip() + "\n")
    parts.append("\n---\n")

    parts.append("## Appendix A — AI Usage Declaration\n")
    appendix = (REPORTS / "ai_usage_declaration.md").read_text()
    parts.append(demote_h1_strip(appendix).strip() + "\n")
    parts.append("\n---\n")

    parts.append("## Appendix B — Supplementary Figures\n")
    parts.append(textwrap.dedent("""\
    **Figure 6b — Drug-community visualisation, Gephi rendering** (cross-validation of the
    Python rendering used as Figure 6 in the main body).
    See [figures/03_gephi_drug_communities.png](../figures/03_gephi_drug_communities.png).

    **Figure 7 — F-UJI baseline results screenshot.** Available at
    [figures/fuji_baseline.png](../figures/fuji_baseline.png) (1808 × 1240 px). The F-UJI
    web tool was run on 2026-05-06 against
    `https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html`; the JSON record is
    preserved at [reports/fuji_baseline.json](fuji_baseline.json) and parsed into
    [reports/fuji_baseline_summary.csv](fuji_baseline_summary.csv). The screenshot is the
    visual cross-reference for the per-metric table reported in Component A.

    ![](../figures/fuji_baseline.png)
    """))

    OUT_MD.write_text("\n".join(parts))

    # Word-count diagnostics
    full_text = "\n".join(parts)
    full_wc = count_words(full_text)
    print(f"wrote {OUT_MD}")
    print(f"  full document: {full_wc} words")
    print(f"  body (intro + 4 components + graph + conclusion): {body_word_total} words "
          f"(cap = 4000)")
    print()
    print("  per-section breakdown:")
    for heading, wc in body_breakdown:
        bar = "#" * (wc // 25)
        print(f"    {wc:>4}w  {heading:<55}  {bar}")
    print()
    if body_word_total > 4000:
        print(f"  WARNING: body exceeds 4000-word cap by {body_word_total - 4000} words.")
    else:
        print(f"  body word count: PASS  ({4000 - body_word_total} words headroom)")


if __name__ == "__main__":
    main()
