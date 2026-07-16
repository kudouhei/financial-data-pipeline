from __future__ import annotations

from html import escape

import streamlit as st


STYLES = """
<style>
:root {
  --ink:#102A43; --muted:#627D98; --teal:#087F8C;
  --amber:#F0A202; --line:#D9E2EC;
}
.stApp { background:linear-gradient(180deg,#F6F9FC 0,#FFFFFF 32rem); }
[data-testid="stHeader"] { display:none; }
[data-testid="stAppHeader"] { display:none; }
[data-testid="stToolbar"] { display:none; }
[data-testid="stDecoration"] { display:none; }
[data-testid="stStatusWidget"] { display:none; }
.stAppHeader { display:none; }
div[class*="stAppHeader"] { display:none; }
.stAppToolbar { display:none; }
div[class*="stAppToolbar"] { display:none; }
.block-container { max-width:1440px; padding-top:1rem; padding-bottom:4rem; }
h1,h2,h3 { color:var(--ink); letter-spacing:-.025em; }
h1 { font-size:2.15rem !important; margin-bottom:.2rem !important; }
h2 { margin-top:1.6rem !important; }
[data-testid="stMetric"] {
  background:#FFF; border:1px solid var(--line); border-radius:14px;
  padding:1rem 1.1rem; box-shadow:0 8px 24px rgba(16,42,67,.055);
}
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--ink); font-weight:650; }
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap:1.5rem; border-bottom:1px solid var(--line);
}
[data-testid="stTabs"] button { padding-left:0; padding-right:0; }
.eyebrow {
  color:var(--teal); font-size:.78rem; font-weight:700;
  letter-spacing:.13em; text-transform:uppercase; margin-bottom:.35rem;
}
.lede { color:var(--muted); font-size:1.05rem; max-width:850px; margin:0 0 1.2rem; }
.question {
  background:linear-gradient(120deg,#12375F,#087F8C); color:#FFF;
  border-radius:16px; padding:1.15rem 1.35rem; margin:.8rem 0 1.4rem;
  box-shadow:0 12px 30px rgba(18,55,95,.16);
}
.question small { opacity:.76; text-transform:uppercase; letter-spacing:.12em; }
.question strong { display:block; font-size:1.12rem; margin-top:.3rem; }
.section-note { color:var(--muted); margin-top:-.65rem; margin-bottom:1rem; }
.insight {
  border-left:4px solid var(--amber); background:#FFF8E8; color:var(--ink);
  border-radius:0 10px 10px 0; padding:.85rem 1rem; margin:.35rem 0 1rem;
}
.status-dot {
  display:inline-block; width:.55rem; height:.55rem; border-radius:50%;
  background:#27AE60; margin-right:.45rem;
}
div[data-testid="stDataFrame"] {
  border:1px solid var(--line); border-radius:12px; overflow:hidden;
}
.lineage {
  display:grid; grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;
  align-items:center; gap:.75rem; margin:.4rem 0 1.5rem;
}
.lineage div { border:1px solid var(--line); border-radius:12px; padding:1rem; background:#FFF; }
.lineage small,.lineage span { display:block; color:var(--muted); }
.lineage strong { display:block; color:var(--ink); margin:.25rem 0; }
.lineage b { color:var(--teal); font-weight:400; }
footer { visibility:hidden; }
@media(max-width:700px) {
  .block-container { padding-top:1.2rem; }
  h1 { font-size:1.75rem !important; }
  .lineage { grid-template-columns:1fr; }
  .lineage b { transform:rotate(90deg); text-align:center; }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(STYLES, unsafe_allow_html=True)


def format_eur(value: float) -> str:
    return f"€{value or 0:,.0f}"


def section(title: str, note: str) -> None:
    st.subheader(title)
    st.markdown(
        f'<div class="section-note">{escape(note)}</div>',
        unsafe_allow_html=True,
    )


def priority_note(check_name: str, amount: float, owner: str) -> None:
    st.markdown(
        '<div class="insight"><strong>Priority:</strong> '
        f'{escape(check_name)} affects {format_eur(amount)}. '
        f'Owner: <strong>{escape(owner)}</strong>.</div>',
        unsafe_allow_html=True,
    )


def footer() -> None:
    st.markdown(
        '<p style="color:#829AB1;font-size:.78rem;margin-top:2rem">'
        '<span class="status-dot"></span>Latest processed dataset · '
        "Values normalized to EUR</p>",
        unsafe_allow_html=True,
    )


def pipeline_lineage() -> None:
    st.markdown(
        """
        <div class="lineage" aria-label="Pipeline processing stages">
          <div><small>01 · Source</small><strong>CSV inputs</strong><span>Schema and row metadata</span></div>
          <b>→</b>
          <div><small>02 · Validate</small><strong>Quality controls</strong><span>Completeness · uniqueness · validity · consistency</span></div>
          <b>→</b>
          <div><small>03 · Transform</small><strong>Trusted facts</strong><span>Normalized values and relationships</span></div>
          <b>→</b>
          <div><small>04 · Publish</small><strong>Reporting marts</strong><span>KPIs with traceable impact</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
