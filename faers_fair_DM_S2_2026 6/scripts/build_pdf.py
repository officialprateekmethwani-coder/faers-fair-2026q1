"""Convert reports/joint_report.md -> reports/joint_report.pdf.

Pandoc is available but no LaTeX engine (xelatex/pdflatex) is installed,
so we cannot use the pandoc PDF path. WeasyPrint requires system libpango
and libcairo which are not installed. We fall back to ``markdown-pdf``
(pure Python; uses reportlab) — the trade-off is slightly less polished
typography but no system-library dependency.

Re-run with:  python scripts/build_pdf.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_MD = ROOT / "reports" / "joint_report.md"
DST_PDF = ROOT / "reports" / "joint_report.pdf"


def _resolve_image_paths(md: str) -> str:
    """Convert relative ../figures/foo.png references to absolute paths so
    markdown-pdf can locate them. Also rewrite the bare links our section
    files use into proper ![](...) image embeds.
    """
    # Convert "[figures/foo.png](../figures/foo.png)" — these are *links* not
    # image embeds, so we leave them as links. The actual image embeds we
    # add now, inserted at the section-level Figure references.
    return md


_IMG_RE = re.compile(r"\[(figures/[^\]]+\.png)\]\(\.\./(figures/[^\)]+)\)")


def _add_image_embeds(md: str) -> str:
    """For each markdown link to a figure file, also insert a real image
    embed below the paragraph so the PDF actually renders the picture.

    We do this for the headline figures (1-6) only, to avoid duplicating
    images in the appendix.
    """
    # Map of figure-file -> caption.
    captions = {
        "figures/01_demo_missingno_matrix.png": "Figure 1 — DEMO missingness matrix (50,000-row sample). Each column is a DEMO field; black indicates non-null, white indicates null. The blocks of consistent missingness highlight `event_dt`, `age` and `occp_cod` as the columns with the largest gaps.",
        "figures/02_completeness_heatmap.png": "Figure 2 — Per-column completeness heatmap, all 7 tables. Green = high non-null rate; red = low. Hot-spots in the DEMO and THER columns drive the 78.93 % completeness headline.",
        "figures/02_reporting_lag.png": "Figure 3 — Reporting-lag distribution (event_dt → fda_dt, in days). Median = 125 days; the FDA's 15-day expedited window captures only 12.6 % of valid-gap reports.",
        "figures/01_demo_reporter_dist.png": "Figure 4 — Reporter-occupation (`occp_cod`) distribution, top 10. The mix is dominated by consumers (CN), physicians (MD) and health-professionals (HP); the 35 % \"unknown\"/empty share dominates the bar chart and is the principal driver of the age-stratification bias discussed in the body.",
        "figures/03_degree_distribution.png": "Figure 5 — Drug-Reaction bipartite projection: weighted-degree distribution on a log-log scale, drugs (left) vs reactions (right). Both panels are approximately scale-free, consistent with the standard biomedical KG shape (Bean 2017).",
        "figures/03_drug_communities_hd.png": "Figure 6 — Drug-Drug co-prescription communities, top 200 drugs by weighted degree, coloured by Louvain partition (modularity = 0.2941). Four head communities visible: blue (mixed polypharmacy / CV), orange (RA regimen), green (oncology), red (respiratory / CNS).",
    }
    for img, cap in captions.items():
        marker = f"]({{}})".format("../" + img)
        if img not in md:
            continue
        # Insert a centered image and caption block right after the first
        # paragraph that links to this image.
        # Use a unique placeholder by file basename to avoid duplicates.
        name = os.path.basename(img).split(".")[0]
        block = (
            f"\n\n<div class=\"figure\">\n\n"
            f"![]({img})\n\n"
            f"*{cap}*\n\n"
            f"</div>\n\n"
        )
        # Append the figure block to the first occurrence of the link.
        # Heuristic: insert after the paragraph containing the first match.
        idx = md.find(img)
        # Walk forward to the next blank line — that's the paragraph end.
        para_end = md.find("\n\n", idx)
        if para_end == -1:
            para_end = len(md)
        md = md[:para_end] + block + md[para_end:]
    return md


def main() -> int:
    if not SRC_MD.exists():
        print(f"ERROR: {SRC_MD} does not exist; run scripts/build_joint_report.py first.")
        return 2

    md_raw = SRC_MD.read_text()
    md = _add_image_embeds(md_raw)

    from markdown_pdf import MarkdownPdf, Section

    pdf = MarkdownPdf(toc_level=2, optimize=True)
    css = """
    body { font-family: Helvetica, Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; }
    h1 { font-size: 18pt; margin-top: 1em; }
    h2 { font-size: 14pt; margin-top: 0.9em; border-bottom: 1px solid #888; padding-bottom: 4px;}
    h3 { font-size: 12pt; margin-top: 0.7em; }
    p { text-align: justify; }
    code { background: #f3f3f3; padding: 1px 3px; border-radius: 2px; font-size: 9.5pt; }
    img { max-width: 95%; display: block; margin: 12px auto; }
    .figure { text-align: center; margin: 12px 0; }
    .figure em { color: #555; font-size: 9.5pt; display: block; margin-top: 4px; }
    table { border-collapse: collapse; margin: 8px 0; }
    th, td { border: 1px solid #ccc; padding: 4px 8px; }
    blockquote { border-left: 3px solid #888; padding-left: 8px; color: #555; }
    """
    pdf.add_section(Section(md, root=str(ROOT)), user_css=css)
    pdf.meta["title"] = "FAERS-FAIR — Joint Report"
    pdf.meta["author"] = "Prateek Methwani, Chandana, Dhyan"
    pdf.save(str(DST_PDF))

    size = DST_PDF.stat().st_size
    print(f"wrote {DST_PDF}  ({size:,} bytes, {size/1024:.0f} KB)")

    # Quick sanity: count pages by inspecting the PDF.
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(DST_PDF)).pages)
        print(f"  pages: {n}")
    except ImportError:
        # Fallback: count "Pages" in the PDF stream — unreliable but better
        # than nothing.
        with DST_PDF.open("rb") as f:
            data = f.read()
        n = data.count(b"/Type /Page\n") + data.count(b"/Type /Page ")
        print(f"  pages (rough): {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
