"""Promptica: a multi-agent research assistant (Streamlit UI).

Run locally:   python -m streamlit run streamlit_app.py
Deploy:        see the Render start command at the bottom of this file

This file only imports run_research_agent from your pipeline.py. It works with your
original pipeline.py AND with the updated one that has a `progress` callback
(the updated one gives you live step-by-step status in the thinking panel).
"""

import html
import inspect
import re
import time
import traceback

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()  # local .env  (on Render use Environment Variables, on Streamlit Cloud use Secrets)
except ImportError:
    pass

from pipeline import run_research_agent

APP_NAME = "Promptica-AI"

# ---------------------------------------------------------------- page setup
st.set_page_config(page_title=f"{APP_NAME} · Multi-Agent Research", page_icon="🧭", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Newsreader:opsz,wght@6..72,400;6..72,600&display=swap');

    :root { --q: #0d8a72; --q-soft: rgba(13, 138, 114, 0.12); --line: rgba(128, 128, 128, 0.28); }

    html, body, [class*="st-"], .stMarkdown, button, input, textarea {
        font-family: "Manrope", system-ui, -apple-system, "Segoe UI", sans-serif;
    }

    /* soft glow behind the page (transparent, so it works in light and dark) */
    .stApp {
        background-image:
            radial-gradient(800px 360px at 15% -60px, rgba(13, 138, 114, 0.20), transparent 70%),
            radial-gradient(700px 320px at 95% -40px, rgba(58, 111, 216, 0.16), transparent 70%);
        background-repeat: no-repeat;
    }

    /* Streamlit's own header is fixed at the top (about 60px). Keep it transparent and push our content below it. */
    [data-testid="stHeader"] { background: transparent; }
    footer, [data-testid="stToolbar"] { visibility: hidden; height: 0; }
    .block-container, [data-testid="stMainBlockContainer"] {
        max-width: 840px; padding-top: 5.5rem; padding-bottom: 4rem;
    }

    /* ---------- top bar ---------- */
    .topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 2.4rem; }
    .brand { display: flex; align-items: center; gap: 10px; }
    .logo {
        display: grid; grid-template-columns: 1fr 1fr; gap: 3px;
        width: 28px; height: 28px; padding: 5px; border-radius: 9px;
        background: linear-gradient(135deg, #0d8a72, #3a6fd8);
    }
    .logo i { background: #fff; border-radius: 50%; opacity: 0.95; }
    .brand-name { font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em; }
    .ready {
        display: inline-flex; align-items: center; gap: 8px;
        border: 1px solid var(--line); border-radius: 999px;
        padding: 5px 12px; font-size: 0.8rem; font-weight: 600; opacity: 0.85;
    }
    .ready-dot { width: 8px; height: 8px; border-radius: 50%; background: #25c27a; box-shadow: 0 0 0 3px rgba(37, 194, 122, 0.2); }

    /* ---------- hero ---------- */
    .hero-title {
        font-size: clamp(2rem, 6.4vw, 3.3rem); font-weight: 800;
        line-height: 1.08; letter-spacing: -0.035em; margin: 0 0 0.8rem; max-width: 16ch;
    }
    .hero-sub { opacity: 0.72; font-size: 1.08rem; line-height: 1.55; margin-bottom: 1.8rem; max-width: 54ch; }

    /* ---------- input card ---------- */
    [data-testid="stForm"] {
        border: 1px solid var(--line); border-radius: 20px; padding: 16px;
        background: rgba(128, 128, 128, 0.05);
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.07);
    }
    [data-testid="stForm"] input { font-size: 1.05rem; }
    .field-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 700; margin: 6px 0 2px; opacity: 0.85; }
    .badge {
        font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 999px;
        background: var(--q-soft); color: var(--q);
    }
    .stButton > button, [data-testid="stFormSubmitButton"] button, .stDownloadButton > button {
        border-radius: 12px; font-weight: 700; min-height: 2.9rem;
    }
    .chips .stButton > button { font-weight: 500; font-size: 0.82rem; border-radius: 999px; min-height: 2.4rem; opacity: 0.9; }

    /* ---------- agent cards (how it works + thinking) ---------- */
    .agents { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 18px; }
    .agent {
        position: relative; display: flex; flex-direction: column; gap: 2px;
        border: 1px solid var(--line); border-radius: 14px; padding: 12px 12px 10px;
        transition: opacity 0.3s, box-shadow 0.3s, border-color 0.3s;
    }
    .agent b { font-size: 0.95rem; }
    .agent small { opacity: 0.7; font-size: 0.78rem; line-height: 1.3; }
    .agent em { font-style: normal; font-size: 0.75rem; font-weight: 700; margin-top: 6px; }
    .agent-dot { position: absolute; top: 12px; right: 12px; width: 9px; height: 9px; border-radius: 50%; background: rgba(128, 128, 128, 0.5); }
    .agent.pending { opacity: 0.55; }
    .agent.running { border-color: var(--q); box-shadow: 0 0 0 4px var(--q-soft); }
    .agent.running .agent-dot { background: var(--q); animation: pulse 1.2s ease-in-out infinite; }
    .agent.running em, .agent.done em { color: var(--q); }
    .agent.done .agent-dot { background: var(--q); }
    .how { margin-top: 28px; }
    .how .agent { padding-right: 28px; }

    /* ---------- thinking panel ---------- */
    .think {
        border: 1px solid var(--line); border-radius: 22px; padding: 22px;
        background: linear-gradient(180deg, rgba(13, 138, 114, 0.09), transparent 70%);
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.07);
    }
    .think-head { display: flex; align-items: center; gap: 16px; }
    .orb {
        position: relative; flex: none; width: 40px; height: 40px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #8be9d2, var(--q) 60%, #0a5c4d);
        animation: float 2.4s ease-in-out infinite;
    }
    .orb::after {
        content: ""; position: absolute; inset: -6px; border-radius: 50%;
        border: 2px solid var(--q); opacity: 0.5; animation: ping 1.8s ease-out infinite;
    }
    .think-title { font-weight: 800; font-size: 1.15rem; letter-spacing: -0.01em; }
    .think-sub { opacity: 0.65; font-size: 0.9rem; overflow-wrap: anywhere; }
    .dots::after { content: ""; animation: dots 1.4s steps(4, end) infinite; }

    .bar { height: 6px; border-radius: 999px; background: rgba(128, 128, 128, 0.22); overflow: hidden; margin-top: 18px; }
    .bar span {
        position: relative; display: block; height: 100%; border-radius: 999px;
        background: linear-gradient(90deg, #0d8a72, #3a6fd8); overflow: hidden;
    }
    .bar span::after {
        content: ""; position: absolute; inset: 0;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
        animation: shimmer 1.4s linear infinite;
    }
    .bar.indeterminate span { width: 38% !important; animation: slide 1.4s ease-in-out infinite; }

    @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.5); opacity: 0.6; } }
    @keyframes ping { 0% { transform: scale(0.85); opacity: 0.6; } 100% { transform: scale(1.5); opacity: 0; } }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
    @keyframes shimmer { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
    @keyframes slide { 0% { margin-left: -38%; } 100% { margin-left: 100%; } }
    @keyframes dots { 0% { content: ""; } 25% { content: "."; } 50% { content: ".."; } 75%, 100% { content: "..."; } }

    /* ---------- result ---------- */
    .result-title { font-weight: 800; font-size: 1.25rem; letter-spacing: -0.02em; margin: 6px 0 14px; }
    .check {
        display: inline-grid; place-items: center; width: 24px; height: 24px; margin-right: 8px;
        border-radius: 50%; background: var(--q); color: #fff; font-size: 0.8rem;
    }
    .muted { font-weight: 500; opacity: 0.6; font-size: 1rem; overflow-wrap: anywhere; }
    [data-testid="stMetric"] { border: 1px solid var(--line); border-radius: 14px; padding: 12px 16px; background: rgba(128, 128, 128, 0.05); }

    div[data-baseweb="tab-panel"] { padding-top: 1.2rem; }
    div[data-baseweb="tab-panel"] [data-testid="stMarkdownContainer"] p,
    div[data-baseweb="tab-panel"] [data-testid="stMarkdownContainer"] li {
        font-family: "Newsreader", Georgia, serif; font-size: 1.12rem; line-height: 1.75;
    }

    /* ---------- small screens ---------- */
    @media (max-width: 700px) {
        .block-container, [data-testid="stMainBlockContainer"] { padding-top: 4.5rem; padding-left: 1rem; padding-right: 1rem; }
        .agents { grid-template-columns: repeat(2, 1fr); }
        .topbar { margin-bottom: 1.6rem; }
        .think { padding: 18px; }
    }
    @media (max-width: 380px) { .agents { grid-template-columns: 1fr; } }

    @media (prefers-reduced-motion: reduce) {
        .orb, .orb::after, .bar span::after, .bar.indeterminate span, .dots::after, .agent-dot { animation: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- content
STEPS = [
    ("search", "Search agent", "Finds recent, reliable sources"),
    ("reader", "Reader agent", "Opens the best page and reads it"),
    ("writer", "Writer agent", "Drafts the full report"),
    ("critic", "Critic", "Reviews the draft"),
]
LABELS = {"pending": "Waiting", "running": "Working", "done": "Done"}
THINKING = {
    "search": "Searching the web",
    "reader": "Reading the best source",
    "writer": "Writing your report",
    "critic": "Reviewing the draft",
}

# DEMO ONLY: these are not connected to the pipeline. Your pipeline uses the model set in multi_agents.py.
MODEL_OPTIONS = ["Gemini-3.5-flash-lite", "Gemini-3.8-flash-lite", "Mistral", "Groq"]
DEFAULT_MODEL = "Gemini-3.8-flash-lite"

EXAMPLES = [
    "Latest trends in small language models",
    "Impact of solar power on rural Bangladesh",
    "How does retrieval-augmented generation work?",
]


# ---------------------------------------------------------------- helpers
def as_text(value) -> str:
    """Turn a chain/agent output into a plain string."""
    value = getattr(value, "content", value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return "" if value is None else str(value)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "report"


def format_time(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{secs}s"


def count_sources(text: str) -> int:
    return len(set(re.findall(r"https?://[^\s)\]>\"']+", text or "")))


def set_topic(text: str):
    st.session_state["topic"] = text


def how_it_works_html() -> str:
    cards = "".join(
        f'<div class="agent"><span class="agent-dot"></span><b>{name}</b><small>{desc}</small></div>'
        for _, name, desc in STEPS
    )
    return f'<div class="how"><div class="agents">{cards}</div></div>'


def thinking_html(topic: str, states: dict, indeterminate: bool = False) -> str:
    done = sum(1 for s in states.values() if s == "done")
    active = next((k for k, s in states.items() if s == "running"), None)
    title = "The agents are working" if indeterminate else THINKING.get(active, "Getting the agents ready")
    percent = done * 25 + (12 if active else 0)
    bar_class = "bar indeterminate" if indeterminate else "bar"

    cards_html = ""
    if not indeterminate:
        cards_html = '<div class="agents">' + "".join(
            f'<div class="agent {states[key]}"><span class="agent-dot"></span>'
            f"<b>{name}</b><small>{desc}</small><em>{LABELS[states[key]]}</em></div>"
            for key, name, desc in STEPS
        ) + "</div>"

    return (
        '<div class="think"><div class="think-head"><span class="orb"></span><div>'
        f'<div class="think-title">{title}<span class="dots"></span></div>'
        f'<div class="think-sub">{html.escape(topic)}</div></div></div>'
        f'<div class="{bar_class}"><span style="width:{percent}%"></span></div>'
        f"{cards_html}</div>"
    )


# ---------------------------------------------------------------- research run
def run_research(topic: str):
    st.session_state.pop("result", None)

    states = {key: "pending" for key, _, _ in STEPS}
    can_report_progress = "progress" in inspect.signature(run_research_agent).parameters

    panel = st.empty()
    panel.markdown(thinking_html(topic, states, indeterminate=not can_report_progress), unsafe_allow_html=True)

    def on_progress(step, status, payload=None):
        states[step] = status
        panel.markdown(thinking_html(topic, states), unsafe_allow_html=True)

    started = time.time()
    try:
        if can_report_progress:
            state = run_research_agent(topic, progress=on_progress)
        else:
            state = run_research_agent(topic)
    except Exception as exc:  # friendly message for users, details for you
        panel.empty()
        st.error("The research did not finish. Please try again in a moment.")
        with st.expander("Technical details"):
            st.code("".join(traceback.format_exception(exc)), language="text")
        return

    panel.empty()
    st.session_state["result"] = {
        "topic": topic,
        "seconds": time.time() - started,
        "report": as_text(state.get("report")),
        "feedback": as_text(state.get("feedback")),
        "search_results": as_text(state.get("search_results")),
        "scraped_content": as_text(state.get("scraped_content")),
    }


def show_result(result: dict):
    st.markdown(
        f'<div class="result-title"><span class="check">✓</span>Research complete'
        f'<span class="muted"> · {html.escape(result["topic"])}</span></div>',
        unsafe_allow_html=True,
    )

    col_time, col_words, col_sources = st.columns(3)
    col_time.metric("Time", format_time(result["seconds"]))
    col_words.metric("Report length", f"{len(result['report'].split()):,} words")
    col_sources.metric("Sources found", count_sources(result["search_results"]))

    with st.container(border=True):
        report_tab, feedback_tab, sources_tab = st.tabs(["Report", "Critic review", "Sources"])

        with report_tab:
            st.markdown(result["report"] or "_Nothing to show._")
            st.download_button(
                "Download report (.md)",
                data=result["report"],
                file_name=f"{slugify(result['topic'])}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with feedback_tab:
            st.markdown(result["feedback"] or "_Nothing to show._")

        with sources_tab:
            with st.expander("Search results", expanded=True):
                st.markdown(result["search_results"] or "_Nothing to show._")
            with st.expander("Page content the reader agent used"):
                st.markdown(result["scraped_content"] or "_Nothing to show._")


# ---------------------------------------------------------------- page
st.markdown(
    f"""
    <div class="topbar">
      <div class="brand"><span class="logo"><i></i><i></i><i></i><i></i></span><span class="brand-name">{APP_NAME}</span></div>
      <span class="ready"><span class="ready-dot"></span>Agents ready</span>
    </div>
    <h1 class="hero-title">Ask once. Four agents do the research.</h1>
    <p class="hero-sub">{APP_NAME} searches the web, reads the best source, writes a report and has a critic review it.</p>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("topic", "")

with st.form("ask", border=False):
    topic_input = st.text_input(
        "Research topic",
        key="topic",
        placeholder="e.g. How is AI changing healthcare in Bangladesh?",
        label_visibility="collapsed",
        max_chars=300,
    )

    st.markdown('<div class="field-label">Model <span class="badge">Demo</span></div>', unsafe_allow_html=True)
    if hasattr(st, "pills"):
        st.pills(
            "Model",
            MODEL_OPTIONS,
            default=DEFAULT_MODEL,
            key="model_demo",
            label_visibility="collapsed",
            help="Demo only. The research uses the model configured in multi_agents.py.",
        )
    else:  # older Streamlit versions
        st.radio("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(DEFAULT_MODEL), horizontal=True, key="model_demo", label_visibility="collapsed")

    submitted = st.form_submit_button("Start research", type="primary", use_container_width=True)

st.markdown('<div class="chips">', unsafe_allow_html=True)
chip_columns = st.columns(len(EXAMPLES))
for column, example in zip(chip_columns, EXAMPLES):
    column.button(example, key=f"chip-{example}", use_container_width=True, on_click=set_topic, args=(example,))
st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    cleaned = topic_input.strip()
    if len(cleaned) < 3:
        st.warning("Please enter a topic with at least 3 characters.")
    else:
        run_research(cleaned)

if "result" in st.session_state:
    show_result(st.session_state["result"])
elif not submitted:
    st.markdown(how_it_works_html(), unsafe_allow_html=True)

st.caption("AI-generated research. Check important facts against the original sources.")

# Render start command:
#   streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0