"""
app.py — Decon AI | Market Intelligence Engine
Each department has its own custom tabs and UI.
Run with: python -m streamlit run app.py
"""

import os
import sys

# Windows' default console codepage (cp1252) can't encode ₹, ⭐, →, − and other
# characters used throughout the scraper/engine debug prints. Without this, any
# LIVE (non-cached) fetch that reaches one of those prints raises
# UnicodeEncodeError deep inside a try/except, gets silently swallowed, and the
# caller gets back {} — e.g. Review Intelligence showing "0 reviews" for any
# product it hadn't already cached. Force UTF-8 on stdout/stderr before any
# other module (which may print at import or call time) gets a chance to.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime
import json
import streamlit as st

# ── Streamlit Community Cloud: copy st.secrets → os.environ BEFORE importing
#    modules/llm (they read os.getenv at import time). No-op on Render/local,
#    where keys already come from environment variables / .env.
try:
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

from modules import MODULES
from llm import llm_available, DEMO_SAFE
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Decon AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

:root {
    --ink:      #0A0A0A;
    --ink-soft: #1A1A1A;
    --cream:    #F6F5F2;
    --card:     #FFFFFF;
    --line:     #ECEBE6;
    --line-2:   #E2E1DB;
    --muted:    #6B6B6B;
    --faint:    #9A9A96;
    --lime:     #C8F55A;
    --lime-ink: #0A0A0A;
    --salmon:   #F4A99A;
}

/* ── Base ─────────────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
#MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden; }
.stApp { background: var(--cream); color: var(--ink); }
.block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1240px; }

/* Headings + text in the main pane */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: var(--ink) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
.stApp h2 { font-size: 24px !important; margin-top: 8px !important; }
.stApp h3 { font-size: 19px !important; }
.stApp h4 { font-size: 17px !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #2E2E2E; line-height: 1.7; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
a, a:visited { color: #0A0A0A; text-decoration: underline; text-underline-offset: 2px; }

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--ink);
    border-right: 1px solid #191919;
}
section[data-testid="stSidebar"] * { color: #DCDCDC !important; }
section[data-testid="stSidebar"] hr { border-color: #242424 !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 4px 0; font-size: 14px; font-weight: 500;
}

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero {
    background: var(--ink);
    border: 1px solid #202020;
    border-radius: 18px;
    padding: 34px 40px;
    margin-bottom: 26px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.hero-logo { font-size: 34px; font-weight: 700; color: #fff; letter-spacing: -0.03em; }
.hero-logo span { color: var(--lime); }
.hero-sub { font-size: 13px; color: #8A8A8A; margin-top: 8px; letter-spacing: 0.01em; }
.hero-badge {
    background: rgba(200,245,90,0.10);
    border: 1px solid rgba(200,245,90,0.28);
    color: var(--lime);
    padding: 9px 18px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Metric cards ─────────────────────────────────────────────────────────── */
.metrics { display: flex; gap: 14px; margin-bottom: 26px; }
.metric {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 20px 24px;
    flex: 1;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.metric:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(10,10,10,0.06); border-color: var(--line-2); }
.metric-val { font-size: 34px; font-weight: 700; color: var(--ink); line-height: 1.05; letter-spacing: -0.03em; }
.metric-label { font-size: 11px; color: var(--muted); margin-top: 8px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-sub { font-size: 11px; color: var(--faint); margin-top: 3px; }

/* ── Department pill ──────────────────────────────────────────────────────── */
.dept-pill {
    display: inline-block; padding: 6px 15px; border-radius: 100px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.03em; margin-bottom: 18px;
    background: #EFEEE9; color: #3A3A3A; border: 1px solid var(--line-2);
}
.dept-supply, .dept-content, .dept-design { background: #EFEEE9; color: #3A3A3A; }

/* ── Cards ────────────────────────────────────────────────────────────────── */
.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 14px;
    transition: box-shadow .18s ease, border-color .18s ease;
}
.card:hover { box-shadow: 0 8px 24px rgba(10,10,10,0.06); border-color: var(--line-2); }
.card-rank { font-size: 10px; font-weight: 700; color: var(--faint); text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 6px; }
.card-title { font-size: 20px; font-weight: 600; color: var(--ink); margin-bottom: 12px; letter-spacing: -0.02em; }
.pill {
    display: inline-block; padding: 5px 13px; border-radius: 100px;
    font-size: 12px; font-weight: 600; margin-right: 6px;
}
.pill-score { background: var(--ink); color: var(--lime); }
.pill-cost, .pill-market { background: #F0EFEA; color: #4A4A4A; }
.pill-format { background: #FBE7E2; color: #B4503E; }
.competitor-box {
    background: #FBF3EF; border: 1px solid #F3D9D0; border-radius: 10px;
    padding: 10px 14px; font-size: 13px; color: #9A4B39; margin: 12px 0;
}
.why-text { font-size: 14px; color: #3E3E3E; line-height: 1.75; margin-top: 12px; }

/* ── Idea cards ───────────────────────────────────────────────────────────── */
.idea-card {
    background: var(--card); border: 1px solid var(--line);
    border-left: 3px solid var(--lime); border-radius: 14px;
    padding: 20px 24px; margin-bottom: 12px;
}
.idea-title { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.idea-meta { font-size: 12px; color: var(--faint); margin-bottom: 8px; }
.idea-desc { font-size: 14px; color: #3E3E3E; line-height: 1.65; }
.chatgpt-box {
    background: #F4FAE9; border: 1px solid #DCEFB5; border-radius: 10px;
    padding: 12px 16px; margin-top: 12px; font-size: 12px; color: #4C6B1F;
}

/* ── Trend cards ──────────────────────────────────────────────────────────── */
.trend-card {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 12px;
}
.trend-market-hdr {
    font-size: 15px; font-weight: 600; color: var(--ink);
    margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 1.5px solid var(--ink);
    display: flex; align-items: center; justify-content: space-between;
}
.trend-signal { font-size: 15px; font-weight: 600; color: var(--ink); }
.trend-note { font-size: 13px; color: var(--muted); margin-top: 5px; line-height: 1.65; }
.trend-opp {
    background: #F4FAE9; border: 1px solid #DCEFB5; border-radius: 8px;
    padding: 8px 14px; font-size: 13px; color: #4C6B1F; margin-top: 10px;
}

/* ── Status badges ────────────────────────────────────────────────────────── */
.badge {
    display: inline-block; padding: 3px 11px; border-radius: 100px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
}
.b-early { background: #EAF6D6; color: #4C6B1F; }
.b-emerging { background: #FBF1D6; color: #85601A; }
.b-mainstream { background: #FBE7DC; color: #99441F; }
.b-saturated { background: #FADFDA; color: #97362B; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #EBEAE4; padding: 5px; border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px; padding: 8px 20px; font-weight: 500; font-size: 13.5px; color: var(--muted);
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: var(--ink) !important; font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(10,10,10,0.10);
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
    background: var(--ink) !important; color: #fff !important;
    border: 1px solid var(--ink) !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 14px !important; padding: 10px 26px !important;
    transition: all .18s ease !important; letter-spacing: 0.01em !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--ink-soft) !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(10,10,10,0.16) !important;
}
.stButton > button[kind="primary"] { background: var(--ink) !important; }
.stButton > button[kind="secondary"] {
    background: #fff !important; color: var(--ink) !important; border: 1.5px solid var(--ink) !important;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border-radius: 10px !important; border: 1px solid var(--line-2) !important;
    background: #fff !important; color: var(--ink) !important; font-size: 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--ink) !important; box-shadow: 0 0 0 3px rgba(200,245,90,0.30) !important;
}
[data-baseweb="select"] > div {
    border-radius: 10px !important; border-color: var(--line-2) !important; background: #fff !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] { background: var(--ink) !important; }
.stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] { color: var(--faint) !important; }

/* Progress bar + spinner in brand lime */
.stProgress > div > div > div { background: var(--lime) !important; }

/* Expander */
div[data-testid="stExpander"] {
    background: #fff; border: 1px solid var(--line) !important; border-radius: 12px !important;
}
div[data-testid="stExpander"] summary { font-weight: 600; color: var(--ink); }

/* Section label helper */
.sec-label {
    font-size: 10px; font-weight: 700; color: var(--faint);
    text-transform: uppercase; letter-spacing: 0.16em; margin: 4px 0 10px;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def platform_metrics():
    """Headline platform stats — honest, no fabricated volumes."""
    tools = len(MODULES)
    keys = [os.getenv(k, "") for k in
            ("GROQ_API_KEY", "SERPAPI_KEY", "APIFY_KEY", "MAGNIFIC_API_KEY")]
    live_sources = sum(1 for k in keys if k)
    return tools, 6, 6, live_sources   # tools, competitor brands, markets, live sources


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 24px;">
        <div style="font-size:24px;font-weight:800;letter-spacing:-0.5px;">
            🧬 Decon <span style="color:#C8F55A;">AI</span>
        </div>
        <div style="font-size:11px;color:#555;margin-top:4px;">Market Intelligence Engine</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:10px;">Department</div>', unsafe_allow_html=True)
    choice = st.radio("", [m.label for m in MODULES], label_visibility="collapsed")
    module = next(m for m in MODULES if m.label == choice)

    dept_colors = {"Supply Chain": "dept-supply", "Content / Social": "dept-content", "Design / Creative": "dept-design"}
    st.markdown(f'<span class="dept-pill {dept_colors.get(module.department,"dept-supply")}">{module.department}</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:10px;">System</div>', unsafe_allow_html=True)

    if DEMO_SAFE:
        st.markdown('<div style="background:#0D2A0D;color:#C8F55A !important;padding:7px 12px;border-radius:8px;font-size:11px;font-weight:600;margin-bottom:12px;">⚡ DEMO SAFE MODE</div>', unsafe_allow_html=True)

    _engines = [
        ("Groq",     "Analysis & narrative generation", llm_available()),
        ("SerpAPI",  "Search · Amazon product + reviews", bool(os.getenv("SERPAPI_KEY", ""))),
        ("Apify",    "Deep review sampling",    bool(os.getenv("APIFY_KEY", ""))),
    ]
    _rows = ""
    for _name, _role, _ok in _engines:
        _dot = "#C8F55A" if _ok else "#3A3A3A"
        _glow = "box-shadow:0 0 7px rgba(200,245,90,0.65);" if _ok else ""
        _status = "LIVE" if _ok else "OFF"
        _stxt = "#C8F55A" if _ok else "#6A6A6A"
        _rows += (
            '<div style="display:flex;align-items:center;gap:9px;margin-bottom:11px;">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{_dot};{_glow}flex-shrink:0;"></span>'
            '<div style="flex:1;line-height:1.25;">'
            f'<div style="font-size:12px;font-weight:600;color:#ECECEC !important;">{_name}</div>'
            f'<div style="font-size:10px;color:#7C7C7C !important;">{_role}</div></div>'
            f'<span style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{_stxt} !important;">{_status}</span>'
            '</div>'
        )
    st.markdown(_rows, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:12px;">Scoring Model</div>', unsafe_allow_html=True)
    for k, v in module.weights.items():
        pct = int(v*100)
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:4px;">
                <span>{k.replace("_"," ").title()}</span>
                <span style="color:#C8F55A;font-weight:700;">{pct}%</span>
            </div>
            <div style="background:#222;border-radius:4px;height:4px;">
                <div style="background:linear-gradient(90deg,#C8F55A,#8BC34A);width:{min(pct*3,100)}%;height:4px;border-radius:4px;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── hero + metrics ────────────────────────────────────────────────────────────
tools_n, brands_n, markets_n, sources_n = platform_metrics()

st.markdown(f"""
<div class="hero">
    <div>
        <div class="hero-logo">Decon <span>AI</span></div>
        <div class="hero-sub">Market Intelligence Engine &nbsp;·&nbsp; {module.department} &nbsp;·&nbsp; {module.label}</div>
    </div>
    <div class="hero-badge">🧬 Science-driven decisions</div>
</div>
<div class="metrics">
    <div class="metric">
        <div class="metric-val">{tools_n}</div>
        <div class="metric-label">AI Tools Live</div>
        <div class="metric-sub">One engine, many teams</div>
    </div>
    <div class="metric">
        <div class="metric-val">{brands_n}</div>
        <div class="metric-label">Competitor Brands</div>
        <div class="metric-sub">India D2C skincare</div>
    </div>
    <div class="metric">
        <div class="metric-val">{sources_n}</div>
        <div class="metric-label">Live Data Sources</div>
        <div class="metric-sub">API keys connected</div>
    </div>
    <div class="metric">
        <div class="metric-val">{markets_n}</div>
        <div class="metric-label">Markets Monitored</div>
        <div class="metric-sub">🇰🇷 🇺🇸 🇨🇳 🇫🇷 🇬🇧 🇦🇪</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
if module.key == "product_intel":
    from amazon_scraper import run_analysis, to_excel, search_amazon, safe_number

    tab1, tab2 = st.tabs(["🔍  Competitor Analysis", "📊  Dashboard"])

    # store results in session state so both tabs can access
    if "pi_results" not in st.session_state:
        st.session_state["pi_results"] = []
    if "pi_keyword" not in st.session_state:
        st.session_state["pi_keyword"] = ""

    # ── Tab 1: Input + Analysis ───────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🔍 Amazon Competitor Analysis")
        st.caption("Enter a keyword or paste URLs — get brand, product, price, rating, reviews, claims, ranking, sentiment. Excel output.")

        # how it works
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:12px;">HOW IT WORKS</div>
            <div style="display:flex;gap:16px;">
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🔎</div>
                    <div style="font-size:11px;color:#CCC;">Keyword search or paste URLs</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🌐</div>
                    <div style="font-size:11px;color:#CCC;">Scrapes each product page</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🤖</div>
                    <div style="font-size:11px;color:#CCC;">AI extracts claims + sentiment</div>
                </div>
                <div style="flex:1;background:rgba(200,245,90,0.1);border:1px solid rgba(200,245,90,0.2);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">📊</div>
                    <div style="font-size:11px;color:#C8F55A;font-weight:600;">Ranked Excel + Dashboard</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # input mode toggle
        input_mode = st.radio(
            "Input method",
            ["🔎 Keyword Search", "🔗 Paste Product URLs"],
            horizontal=True,
            key="pi_mode"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if input_mode == "🔎 Keyword Search":
                keyword = st.text_input(
                    "Product keyword",
                    placeholder="e.g. gel sunscreen india, niacinamide serum, vitamin c face wash",
                    key="pi_keyword_input"
                )
                n_results = st.slider("Max products to analyse", 5, 20, 12, key="pi_n")
                pi_comp_only = st.checkbox(
                    "Only my tracked competitors (recommended)", value=True, key="pi_comp_only")
                from amazon_scraper import TARGET_COMPETITORS
                st.caption("Tracked: " + " · ".join(TARGET_COMPETITORS))
                urls_input = ""
            else:
                keyword = st.text_input(
                    "Label for this analysis",
                    placeholder="e.g. Gel Sunscreen Competitors",
                    key="pi_label"
                )
                urls_input = st.text_area(
                    "Paste Amazon URLs (one per line)",
                    placeholder="https://www.amazon.in/dp/ASIN1\nhttps://www.amazon.in/dp/ASIN2\nhttps://www.amazon.in/dp/ASIN3",
                    height=150,
                    key="pi_urls"
                )
                n_results = 10

        with col2:
            date_from = st.text_input(
                "Date / Timeline",
                value=datetime.now().strftime("%B %Y"),
                key="pi_date",
                help="e.g. June 2026, Q2 2026"
            )
            st.markdown("")
            st.markdown("")

            # SerpAPI key status
            serp_key = os.getenv("SERPAPI_KEY","")
            if serp_key:
                st.markdown('<div style="background:#DCFCE7;border-radius:8px;padding:8px 12px;font-size:12px;color:#166534;">✅ SerpAPI connected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:#FEF9C3;border-radius:8px;padding:8px 12px;font-size:12px;color:#854D0E;">⚠️ No SerpAPI key — using demo data.<br>Add SERPAPI_KEY to .env for live data.</div>', unsafe_allow_html=True)

        st.markdown("")
        if st.button("🚀 Run Analysis", type="primary", key="btn_pi_run", use_container_width=False):
            if not keyword:
                st.error("Enter a keyword or label first.")
            else:
                progress_bar = st.progress(0)
                status = st.empty()

                def update_progress(i, total, msg):
                    pct = int((i / max(total,1)) * 100)
                    progress_bar.progress(min(pct, 95))
                    status.markdown(f"⚙️ {msg}")

                urls = [u.strip() for u in urls_input.split("\n") if u.strip()] if urls_input else None

                with st.spinner(""):
                    results = run_analysis(
                        keyword=keyword,
                        urls=urls,
                        n_results=n_results,
                        date_from=date_from,
                        progress_cb=update_progress,
                        competitors_only=st.session_state.get("pi_comp_only", True),
                    )

                progress_bar.progress(100)
                status.markdown(f"✅ Analysed {len(results)} products")

                st.session_state["pi_results"] = results
                st.session_state["pi_keyword"] = keyword

                # AI decision layer: category state-of-play + launch/R&D brief
                try:
                    from product_strategy import strategy_briefs
                    with st.spinner("AI: building category state-of-play + launch brief…"):
                        st.session_state["pi_strategy"] = strategy_briefs(results, keyword)
                except Exception as _e:
                    st.session_state["pi_strategy"] = {}

                # quick summary
                def _safe(val, default=0):
                    import re as _re
                    try:
                        m = _re.search(r"[0-9]+\.?[0-9]*", str(val).replace(",",""))
                        return float(m.group()) if m else default
                    except Exception:
                        return default
                avg_rating = round(sum(_safe(r.get("rating",0)) for r in results) / max(len(results),1), 1)
                avg_price  = round(sum(_safe(r.get("price_inr",0)) for r in results) / max(len(results),1))

                st.markdown(f"""
                <div style="display:flex;gap:12px;margin:16px 0;">
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{len(results)}</div>
                        <div class="metric-label">Products Analysed</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{avg_rating}⭐</div>
                        <div class="metric-label">Avg Rating</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">₹{avg_price}</div>
                        <div class="metric-label">Avg Price</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{results[0].get('brand','') if results else '—'}</div>
                        <div class="metric-label">Top Ranked Brand</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # top 3 products preview
                st.markdown("### Top Competitors")
                for r in results[:3]:
                    sentiment_color = "#166534" if r.get("review_sentiment") == "Positive" else "#9A3412"
                    sentiment_bg = "#DCFCE7" if r.get("review_sentiment") == "Positive" else "#FFEDD5"
                    claims_html = "".join(f'<div style="font-size:12px;color:#555;">• {c}</div>' for c in r.get("top_claims",[])[:3])

                    mrp_v = safe_number(r.get('mrp', r.get('price_inr',0)))
                    sell_v = safe_number(r.get('price_inr',0))
                    disc_v = str(r.get('discount_pct',''))
                    price_html = (
                        f'<span style="text-decoration:line-through;color:#AAA;font-size:12px;">₹{int(mrp_v)}</span> '
                        f'<span style="color:#166534;font-weight:700;">₹{int(sell_v)}</span> '
                        f'<span style="background:#DCFCE7;color:#166534;padding:1px 6px;border-radius:6px;font-size:11px;">{disc_v}</span>'
                    ) if mrp_v and mrp_v != sell_v else f'<span style="font-weight:700;">₹{int(sell_v)}</span>'

                    about = r.get('about_product','')
                    about_html = f'<div style="font-size:12px;color:#555;margin:6px 0;line-height:1.5;">{about[:200]}...</div>' if about else ''

                    st.markdown(f"""
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="flex:1;">
                                <div class="card-rank">#{r.get('final_rank','')} · Amazon Rank #{r.get('keyword_rank','')}</div>
                                <div class="card-title">{r.get('product_name','')[:70]}</div>
                                <div style="font-size:13px;color:#888;margin-bottom:6px;">
                                    {r.get('brand','')} · {price_html} · ⭐{r.get('rating','')} · {r.get('review_count','')} reviews
                                </div>
                                <div style="font-size:12px;color:#555;margin-bottom:6px;">
                                    <b>Category rank:</b> {r.get('category_rank','Not found')}
                                </div>
                                {about_html}
                                <b style="font-size:12px;color:#333;">Key claims:</b>
                                {claims_html}
                            </div>
                            <div style="margin-left:16px;text-align:center;">
                                <span class="pill pill-score">{r.get('total_score',0)}/100</span><br><br>
                                <span style="background:{sentiment_bg};color:{sentiment_color};
                                            padding:3px 10px;border-radius:10px;font-size:11px;font-weight:600;">
                                    {r.get('review_sentiment','—')}
                                </span>
                                <div style="font-size:11px;color:#888;margin-top:8px;">
                                    {r.get('date_range','')}
                                </div>
                            </div>
                        </div>
                        <div style="margin-top:10px;border-top:1px solid #EEE;padding-top:8px;">
                            <div style="display:flex;gap:16px;">
                                <div style="flex:1;background:#F0FDF4;border-radius:8px;padding:10px;">
                                    <div style="font-size:10px;font-weight:700;color:#166534;margin-bottom:4px;text-transform:uppercase;">What Customers Love</div>
                                    <div style="font-size:12px;color:#166534;line-height:1.6;">
                                        {(r.get("key_positives","") if isinstance(r.get("key_positives",""), str) else " ".join(r.get("key_positives",[])))[:300]}...
                                    </div>
                                </div>
                                <div style="flex:1;background:#FEF2F2;border-radius:8px;padding:10px;">
                                    <div style="font-size:10px;font-weight:700;color:#991B1B;margin-bottom:4px;text-transform:uppercase;">What Customers Complain About</div>
                                    <div style="font-size:12px;color:#991B1B;line-height:1.6;">
                                        {(r.get("key_negatives","") if isinstance(r.get("key_negatives",""), str) else " ".join(r.get("key_negatives",[])))[:300]}...
                                    </div>
                                </div>
                            </div>
                            {f'<div style="margin-top:8px;font-size:12px;color:#666;"><b>Market gap:</b> {r.get("market_gap","")}</div>' if r.get("market_gap") else ""}
                            <div style="margin-top:8px;font-size:10px;color:#9A9A96;">
                                📊 Analysed <b>{r.get('reviews_sampled',0)}</b> sampled reviews (recent + critical) ·
                                aspect sentiment from Amazon across all <b>{r.get('review_count','?')}</b> reviews
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if len(results) > 3:
                    st.caption(f"+ {len(results)-3} more products in Excel download and Dashboard tab")

                # Excel download (includes the AI State-of-Play + Launch Brief sheets)
                st.markdown("")
                excel = to_excel(results, keyword, strategy=st.session_state.get("pi_strategy"))
                fname = f"decon_amazon_{keyword.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                st.download_button(
                    "📥 Download Full Analysis Excel",
                    data=excel,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

    # ── Tab 2: Dashboard ──────────────────────────────────────────────────────
    with tab2:
        results = st.session_state.get("pi_results", [])
        keyword = st.session_state.get("pi_keyword", "")

        st.markdown("#### 📊 Competitive Intelligence Dashboard")

        if not results:
            st.info("Run an analysis in the Competitor Analysis tab first — the dashboard will populate here.")
        else:
            st.caption(f"Keyword: **{keyword}** · {len(results)} products · {results[0].get('date_range','')}")

            # ── AI decision layer: category state-of-play + launch brief ──
            _strat = st.session_state.get("pi_strategy") or {}
            _sop = _strat.get("state_of_play", {}) or {}
            _lb = _strat.get("launch_brief", {}) or {}
            if _sop.get("summary"):
                st.markdown("### 🧠 Category State of Play")
                st.caption("AI synthesis across all analysed products — grounded in the scraped prices, "
                           "ratings, demand and Amazon's counted complaint aspects.")
                st.markdown(f"> {_sop.get('summary','')}")
                cA, cB = st.columns(2)
                with cA:
                    if _sop.get("biggest_gaps"):
                        st.markdown("**Biggest gaps**")
                        for g in _sop.get("biggest_gaps", [])[:5]:
                            st.markdown(f"- {g}")
                with cB:
                    if _sop.get("strategic_moves"):
                        st.markdown("**Strategic moves for Deconstruct**")
                        for m in _sop.get("strategic_moves", [])[:6]:
                            st.markdown(f"- {m}")
                for _lab, _key in [("Market structure", "market_structure"),
                                   ("Price dynamics", "price_dynamics"),
                                   ("Deconstruct's position", "deconstruct_position")]:
                    if _sop.get(_key):
                        st.markdown(f"**{_lab}:** {_sop[_key]}")
            if _lb.get("concept"):
                st.markdown("### 🚀 Launch / R&D Brief — what to build next")
                st.markdown(
                    f'<div class="card" style="border-left:4px solid #C8F55A;">'
                    f'<div class="card-title" style="margin-bottom:6px;">{_lb.get("concept","")}</div>'
                    f'<div style="font-size:13px;color:#555;line-height:1.7;">'
                    f'<b>Opportunity:</b> {_lb.get("opportunity","")}<br>'
                    f'<b>Hero ingredient:</b> {_lb.get("hero_ingredient","")} &nbsp;·&nbsp; '
                    f'<b>Format:</b> {_lb.get("format","")} &nbsp;·&nbsp; '
                    f'<b>Target skin:</b> {_lb.get("target_skin","")}<br>'
                    f'<b>Target price:</b> {_lb.get("target_price_inr","")} — {_lb.get("price_rationale","")}<br>'
                    f'<b>Positioning:</b> {_lb.get("positioning","")}</div>'
                    f'<div style="margin-top:8px;"><b style="font-size:12px;">Key claims:</b> '
                    + " · ".join(f'<span class="pill pill-format">{c}</span>' for c in _lb.get("key_claims", [])[:6])
                    + f'</div><div style="margin-top:8px;font-size:12px;color:#888;">'
                    f'💡 Name ideas: {", ".join(_lb.get("name_ideas", []))} &nbsp;|&nbsp; '
                    f'Why now: {_lb.get("why_now","")}</div></div>',
                    unsafe_allow_html=True)
            st.divider()

            # ── Category Intelligence: pricing bands, demand, whitespace ──
            from product_analytics import category_analytics, opportunity_cards
            from amazon_scraper import load_snapshots
            pi_an = category_analytics(results)
            _ps = pi_an.get("price_stats", {})
            _pm = pi_an.get("per_ml_stats", {})
            _top = (pi_an.get("demand") or [{}])[0]
            st.markdown(f"""
            <div class="metrics" style="margin-top:6px;">
                <div class="metric"><div class="metric-val">₹{_ps.get('median','—')}</div>
                    <div class="metric-label">Median Price</div><div class="metric-sub">₹{_ps.get('min','?')}–₹{_ps.get('max','?')} range</div></div>
                <div class="metric"><div class="metric-val">₹{_pm.get('median','—')}</div>
                    <div class="metric-label">Median ₹/ml</div><div class="metric-sub">₹{_pm.get('min','?')}–₹{_pm.get('max','?')}</div></div>
                <div class="metric"><div class="metric-val" style="font-size:19px;">{_top.get('brand','—')}</div>
                    <div class="metric-label">Top Seller</div><div class="metric-sub">~{_top.get('bought',0):,}/mo bought</div></div>
                <div class="metric"><div class="metric-val">{pi_an.get('ratings_avg') or '—'}★</div>
                    <div class="metric-label">Avg Rating</div><div class="metric-sub">{pi_an.get('n',0)} products</div></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("##### 🎯 Opportunities & Whitespace")
            _oc = opportunity_cards(pi_an)
            _ocols = st.columns(2)
            for _i, _c in enumerate(_oc):
                _ocols[_i % 2].markdown(
                    f'<div style="background:#fff;border:1px solid #ECEBE6;border-left:3px solid #C8F55A;'
                    f'border-radius:12px;padding:12px 16px;margin-bottom:10px;min-height:96px;">'
                    f'<div style="font-size:10px;font-weight:700;color:#9A9A96;text-transform:uppercase;letter-spacing:0.08em;">{_c["type"]}</div>'
                    f'<div style="font-size:14px;font-weight:600;color:#0A0A0A;margin:3px 0 5px;">{_c["title"]}</div>'
                    f'<div style="font-size:12px;color:#555;line-height:1.55;">{_c["detail"]}</div></div>',
                    unsafe_allow_html=True)

            # free "history": median competitor price across past runs
            _hist = load_snapshots(keyword)
            if len(_hist) >= 2:
                try:
                    import plotly.graph_objects as _go
                    def _medprice(h):
                        pr = sorted(p.get("price_inr") for p in h.get("products", [])
                                    if isinstance(p.get("price_inr"), (int, float)))
                        return round(pr[len(pr)//2]) if pr else None
                    _rev = list(reversed(_hist))
                    _ft = _go.Figure(_go.Scatter(
                        x=[h.get("generated_at", "")[:10] for h in _rev],
                        y=[_medprice(h) for h in _rev],
                        mode="lines+markers", line_color="#0A0A0A",
                        marker=dict(color="#C8F55A", size=9)))
                    _ft.update_layout(title="Median competitor price over past runs (₹)", height=300,
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font=dict(family="DM Sans", color="#0A0A0A"))
                    st.plotly_chart(_ft, use_container_width=True)
                except Exception:
                    pass

            st.divider()

            # radar chart using plotly
            try:
                import plotly.graph_objects as go
                import plotly.express as px

                # ── Score breakdown radar for top 5 ──
                top5 = results[:5]
                categories = ["Rating", "Reviews", "Price Value", "Claims", "Rank"]

                fig_radar = go.Figure()
                colors = ["#C8F55A","#F4A99A","#60A5FA","#A78BFA","#FB923C"]

                for i, r in enumerate(top5):
                    sp = r.get("score_parts", {})
                    vals = [
                        sp.get("rating_score", 0),
                        sp.get("review_volume", 0),
                        sp.get("price_value", 0),
                        sp.get("claim_strength", 0),
                        sp.get("rank_position", 0),
                    ]
                    name = f"{r.get('brand','')} ({r.get('total_score',0)})"
                    fig_radar.add_trace(go.Scatterpolar(
                        r=vals + [vals[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name=name,
                        line_color=colors[i % len(colors)],
                        opacity=0.7
                    ))

                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                    showlegend=True,
                    title=f"Competitive Radar — Top 5 for '{keyword}'",
                    height=450,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="DM Sans", size=12),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    # Price vs Rating scatter
                    brands = [r.get("brand","")[:15] for r in results]
                    import re as _re2
                    def _sf(v):
                        try:
                            m = _re2.search(r"[0-9]+\.?[0-9]*", str(v).replace(",",""))
                            return float(m.group()) if m else 0
                        except: return 0
                    prices  = [_sf(r.get("price_inr", 0)) for r in results]
                    ratings = [_sf(r.get("rating", 0)) for r in results]
                    scores = [r.get("total_score",0) for r in results]

                    fig_scatter = px.scatter(
                        x=prices, y=ratings,
                        text=brands,
                        size=scores,
                        color=scores,
                        color_continuous_scale=["#FEE2E2","#FEF9C3","#DCFCE7"],
                        labels={"x":"Price (₹)","y":"Rating","color":"Score"},
                        title="Price vs Rating (bubble size = total score)"
                    )
                    fig_scatter.update_traces(textposition='top center', textfont_size=9)
                    fig_scatter.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_scatter, use_container_width=True)

                with col_c2:
                    # Claims strength bar
                    claim_scores = [r.get("claim_strength", r.get("score_parts",{}).get("claim_strength",0)) for r in results]
                    fig_bar = px.bar(
                        x=[r.get("brand","")[:12] for r in results],
                        y=claim_scores,
                        color=claim_scores,
                        color_continuous_scale=["#FEE2E2","#FEF9C3","#DCFCE7"],
                        labels={"x":"Brand","y":"Claim Strength","color":""},
                        title="Claim Strength by Brand"
                    )
                    fig_bar.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)',
                                          showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

                # sentiment summary
                st.markdown("#### Review Sentiment Summary")
                scols = st.columns(len(results[:6]))
                for i, (r, col) in enumerate(zip(results[:6], scols)):
                    sentiment = r.get("review_sentiment","—")
                    s_color = "#166534" if sentiment=="Positive" else "#9A3412" if sentiment=="Negative" else "#854D0E"
                    s_bg = "#DCFCE7" if sentiment=="Positive" else "#FEE2E2" if sentiment=="Negative" else "#FEF9C3"
                    col.markdown(f"""
                    <div style="background:{s_bg};border-radius:10px;padding:10px;text-align:center;">
                        <div style="font-size:11px;font-weight:700;color:{s_color};">{r.get('brand','')[:12]}</div>
                        <div style="font-size:10px;color:{s_color};margin-top:3px;">{sentiment}</div>
                        <div style="font-size:13px;font-weight:800;color:#0A0A0A;margin-top:2px;">⭐{r.get('rating','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except ImportError:
                st.warning("Install plotly for visualisations: `pip install plotly`")
                # fallback table
                for r in results:
                    st.markdown(f"**#{r.get('final_rank')}** {r.get('brand')} — {r.get('product_name','')[:50]} | Score: {r.get('total_score')}/100 | ₹{r.get('price_inr')} | ⭐{r.get('rating')}")



# ══════════════════════════════════════════════════════════════════════════════
# REVIEW INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
elif module.key == "review_intel":
    from review_intel import deep_review_report, to_excel as ri_to_excel

    st.markdown("#### 🗣️ Review Intelligence — Deep Dive")
    st.caption("Paste one Amazon product URL — get a long-form, descriptive read of what its "
               "reviews actually say, with a multi-tab Excel report you can share with the team.")

    st.markdown("""
    <div style="background:#0A0A0A;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
        <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:12px;">HOW IT WORKS</div>
        <div style="display:flex;gap:16px;">
            <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:20px;margin-bottom:4px;">🔗</div>
                <div style="font-size:11px;color:#CCC;">Paste one product URL</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:20px;margin-bottom:4px;">📖</div>
                <div style="font-size:11px;color:#CCC;">Reads its full review base</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:20px;margin-bottom:4px;">🤖</div>
                <div style="font-size:11px;color:#CCC;">AI writes a narrative report</div>
            </div>
            <div style="flex:1;background:rgba(200,245,90,0.1);border:1px solid rgba(200,245,90,0.2);border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:20px;margin-bottom:4px;">📝</div>
                <div style="font-size:11px;color:#C8F55A;font-weight:600;">Themes, quotes, Excel export</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "ri_report" not in st.session_state:
        st.session_state["ri_report"] = None

    ri_url = st.text_input(
        "Amazon product URL",
        placeholder="https://www.amazon.in/dp/ASIN",
        key="ri_url",
    )

    if st.button("🚀 Generate Review Deep-Dive", type="primary", key="btn_ri_run"):
        if not ri_url.strip().startswith("http"):
            st.error("Paste a full Amazon product URL (starts with http).")
        else:
            progress_bar = st.progress(0)
            status = st.empty()

            def _ri_progress(i, total, msg):
                progress_bar.progress(min(int((i / max(total, 1)) * 100), 95))
                status.markdown(f"⚙️ {msg}")

            try:
                with st.spinner(""):
                    st.session_state["ri_report"] = deep_review_report(ri_url.strip(), progress_cb=_ri_progress)
                progress_bar.progress(100)
                status.markdown("✅ Report ready")
            except Exception as e:
                st.session_state["ri_report"] = None
                st.error(f"Couldn't generate the report: {e}")

    rep = st.session_state.get("ri_report")
    if rep:
        p = rep.get("product", {})
        r = rep.get("report", {})
        stars = rep.get("star_distribution", {})

        st.divider()
        st.markdown(f"""
        <div class="card">
            <div class="card-rank">REVIEW DEEP-DIVE · SCANNED {rep.get('scanned_at', '')}</div>
            <div class="card-title">{p.get('title', '')[:90]}</div>
            <div style="font-size:13px;color:#888;">
                {p.get('brand', '')} · ⭐{p.get('rating', '')} · {p.get('review_count', 0):,} reviews on Amazon ·
                {rep.get('reviews_sampled', 0)} read for this report
                ({rep.get('positive_sampled', 0)} positive · {rep.get('critical_sampled', 0)} critical)
            </div>
        </div>
        """, unsafe_allow_html=True)

        excel_bytes = ri_to_excel(rep)
        fname = f"decon_review_intel_{(p.get('brand','') + '_' + p.get('title',''))[:40].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        st.download_button(
            "📥 Download Full Review Intelligence Excel",
            data=excel_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        if r.get("headline"):
            st.markdown(f"> ### {r['headline']}")

        # star distribution
        pct = stars.get("pct", {})
        if stars.get("sampled"):
            try:
                import plotly.graph_objects as go
                fig = go.Figure(go.Bar(
                    x=[f"{k}★" for k in ["5", "4", "3", "2", "1"]],
                    y=[pct.get(k, 0) for k in ["5", "4", "3", "2", "1"]],
                    marker_color="#C8F55A",
                ))
                fig.update_layout(height=260, title="Sampled star distribution (%)",
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="DM Sans", color="#0A0A0A"))
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass

        if r.get("voice_of_customer"):
            st.markdown("### 🗣️ Voice of the Customer")
            st.markdown(f'<div class="why-text">{r["voice_of_customer"]}</div>', unsafe_allow_html=True)

        themes = r.get("themes", [])
        if themes:
            st.markdown("### 🎭 Themes in the Reviews")
            for t in themes:
                sentiment = t.get("sentiment", "—")
                s_color = "#166534" if sentiment == "Positive" else "#9A3412" if sentiment == "Negative" else "#854D0E"
                s_bg = "#DCFCE7" if sentiment == "Positive" else "#FEE2E2" if sentiment == "Negative" else "#FEF9C3"
                quotes_html = "".join(
                    f'<div style="font-size:12px;color:#555;font-style:italic;margin-top:6px;">"{q}"</div>'
                    for q in t.get("quotes", [])[:3]
                )
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div class="card-title" style="margin-bottom:0;font-size:17px;">{t.get('name', '')}</div>
                        <span style="background:{s_bg};color:{s_color};padding:3px 10px;border-radius:10px;
                                     font-size:11px;font-weight:600;">{sentiment}</span>
                    </div>
                    <div class="why-text">{t.get('narrative', '')}</div>
                    {quotes_html}
                </div>
                """, unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            if r.get("who_its_for"):
                st.markdown("##### ✅ Who It's For")
                st.markdown(f'<div class="why-text">{r["who_its_for"]}</div>', unsafe_allow_html=True)
            if r.get("purchase_journey"):
                st.markdown("##### 🛒 Why People Buy It")
                st.markdown(f'<div class="why-text">{r["purchase_journey"]}</div>', unsafe_allow_html=True)
        with colB:
            if r.get("who_should_avoid"):
                st.markdown("##### ⚠️ Who Should Avoid It")
                st.markdown(f'<div class="why-text">{r["who_should_avoid"]}</div>', unsafe_allow_html=True)
            if r.get("sentiment_arc"):
                st.markdown("##### 📈 Sentiment Over Time")
                st.markdown(f'<div class="why-text">{r["sentiment_arc"]}</div>', unsafe_allow_html=True)

        if r.get("friction_points"):
            st.markdown("### 🔧 Friction Points")
            st.markdown(f'<div class="why-text">{r["friction_points"]}</div>', unsafe_allow_html=True)

        if r.get("verdict"):
            st.markdown("### 🏁 Verdict")
            st.markdown(f'<div class="why-text" style="font-weight:600;">{r["verdict"]}</div>', unsafe_allow_html=True)
