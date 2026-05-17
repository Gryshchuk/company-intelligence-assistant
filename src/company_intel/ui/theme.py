"""Claude-inspired CSS — call inject() once at app start."""
import streamlit as st

_CSS = """
<style>
  :root {
    --c-accent: #D97757;
    --c-border: #3A3936;
    --c-muted: #8C8A83;
    --c-bg-soft: #2E2D2A;
  }
  html, body, [class*="css"] { font-feature-settings: "ss01", "cv11"; }
  h1, h2, h3 { letter-spacing: -0.01em; }
  h1 { font-weight: 600; }
  .stButton > button {
    border-radius: 10px;
    border: 1px solid var(--c-border);
    font-weight: 500;
    transition: all 120ms ease;
  }
  .stButton > button:hover {
    border-color: var(--c-accent);
    color: var(--c-accent);
  }
  [data-testid="stChatInput"] { border-radius: 14px; }
  [data-testid="stExpander"] {
    border: 1px solid var(--c-border);
    border-radius: 10px;
    background: var(--c-bg-soft);
    margin-bottom: 6px;
  }
  [data-testid="stExpander"] summary { font-size: 0.92rem; }
  [data-testid="stMetric"] { background: transparent; padding: 0; }
  [data-testid="stMetricValue"] { font-size: 1.2rem; font-weight: 600; }
  [data-testid="stMetricLabel"] { color: var(--c-muted); }
  [data-testid="stSidebar"] { border-right: 1px solid var(--c-border); }
  hr { border-color: var(--c-border) !important; opacity: 0.6; }
  [data-testid="stChatMessage"] { padding: 8px 0; }
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
