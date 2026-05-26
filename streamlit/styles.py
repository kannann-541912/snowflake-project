"""
Reusable Streamlit dark theme — Mastech Digital branding.

Usage:
    from styles import apply_theme, app_header, section_card, status_banner, badge

    st.set_page_config(...)
    apply_theme()
    app_header("My App", "Subtitle here")

Brand Colors:
  Primary: #01b8fb, #0d558b
  Secondary/Background: #030c25
  Accent: #ecf6fd, #8ec9f5
  Gradient: #009bd9 → #0c5285, #0a4672 → #0092ff → #0A4672
  Text: #ecf6fd (light), #333333 (dark contexts)
  Font: DM Sans
"""
import streamlit as st

_PRIMARY = "#01b8fb"
_PRIMARY_DARK = "#0d558b"
_SECONDARY_BG = "#030c25"
_ACCENT_LIGHT = "#ecf6fd"
_ACCENT_MID = "#8ec9f5"
_SURFACE = "#0a1a3a"
_SURFACE_BORDER = "#1a3a5c"
_TEXT = "#ecf6fd"
_TEXT_MUTED = "#8ec9f5"
_SUCCESS = "#4ade80"
_WARNING = "#fbbf24"

_SELECTORS = {
    "app":       '[data-testid="stAppViewContainer"]',
    "sidebar":   '[data-testid="stSidebar"]',
    "metric":    '[data-testid="stMetric"]',
    "label":     '[data-testid="stMetricLabel"]',
    "value":     '[data-testid="stMetricValue"]',
    "frame":     '[data-testid="stDataFrame"]',
    "button":    '[data-testid="stButton"]>button',
    "expander":  '[data-testid="stExpander"]',
    "tabs":      '[data-testid="stTabs"] [data-baseweb="tab"]',
    "tab_sel":   '[data-testid="stTabs"] [aria-selected="true"]',
    "text_in":   '[data-testid="stTextInput"] input',
    "select":    '[data-testid="stSelectbox"]>div',
}

THEME_CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

* {{ font-family: 'DM Sans', sans-serif !important; }}

{_SELECTORS["app"]}{{background:{_SECONDARY_BG};color:{_TEXT}}}
{_SELECTORS["sidebar"]}{{background:rgba(10,26,58,0.95)}}
.app-header{{background:linear-gradient(-45deg,#0a4672,#0092ff,#0A4672);border-radius:12px;padding:24px 32px;margin-bottom:24px;border-left:5px solid {_PRIMARY};box-shadow:0 4px 24px rgba(1,184,251,0.2)}}
.app-header h1{{font-size:2rem;font-weight:800;color:#fff;margin:0 0 4px 0;letter-spacing:-0.5px;font-family:'DM Sans',sans-serif}}
.app-header p{{color:{_ACCENT_MID};font-size:0.9rem;margin:0}}
{_SELECTORS["metric"]}{{background:linear-gradient(135deg,{_SURFACE},{_PRIMARY_DARK});border-radius:12px;padding:20px;border:1px solid {_SURFACE_BORDER};box-shadow:0 2px 12px rgba(0,0,0,0.3)}}
{_SELECTORS["label"]}{{font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{_ACCENT_MID} !important}}
{_SELECTORS["value"]}{{font-size:1.8rem;font-weight:800;color:#fff !important}}
{_SELECTORS["frame"]}{{border-radius:10px;overflow:hidden;border:1px solid {_SURFACE_BORDER}}}
{_SELECTORS["button"]}{{background:linear-gradient(90deg,{_PRIMARY},{_PRIMARY_DARK});color:#fff;border:none;border-radius:8px;font-weight:700;font-size:0.9rem;padding:10px 24px;letter-spacing:0.03em;transition:all .2s ease;box-shadow:0 2px 12px rgba(1,184,251,0.3)}}
{_SELECTORS["button"]}:hover{{transform:translateY(-1px);box-shadow:0 4px 20px rgba(1,184,251,0.5)}}
{_SELECTORS["expander"]}{{background:rgba(10,26,58,0.6);border-radius:10px;border:1px solid {_SURFACE_BORDER}}}
.section-card{{background:linear-gradient(135deg,rgba(10,26,58,0.8),rgba(13,85,139,0.3));border-radius:12px;padding:20px 24px;border:1px solid {_SURFACE_BORDER};margin-bottom:16px;box-shadow:0 2px 16px rgba(0,0,0,0.2)}}
.badge-blue{{background:linear-gradient(90deg,{_PRIMARY},{_PRIMARY_DARK});color:#fff;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block}}
.badge-amber{{background:linear-gradient(90deg,#f39c12,#e67e22);color:#fff;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block}}
.badge-green{{background:linear-gradient(90deg,#27ae60,#2ecc71);color:#fff;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block}}
.status-banner{{color:#fff;padding:10px 16px;border-radius:8px;font-weight:700;font-size:0.85rem;text-align:center;margin-bottom:16px;letter-spacing:0.05em}}
.status-banner.danger{{background:linear-gradient(90deg,{_PRIMARY_DARK},#0a4672)}}
.status-banner.warning{{background:linear-gradient(90deg,#e67e22,#f39c12)}}
.status-banner.success{{background:linear-gradient(90deg,#27ae60,#2ecc71)}}
.status-banner.info{{background:linear-gradient(90deg,{_PRIMARY},{_PRIMARY_DARK})}}
.mono-box{{background:rgba(1,184,251,0.08);border:2px solid {_PRIMARY};border-radius:10px;padding:20px 24px;font-family:'DM Sans',monospace;font-size:0.85rem;line-height:1.7;color:{_TEXT};white-space:pre-wrap}}
{_SELECTORS["tabs"]}{{font-weight:700;font-size:0.9rem;letter-spacing:0.03em;color:{_ACCENT_MID}}}
{_SELECTORS["tab_sel"]}{{color:{_PRIMARY} !important;border-bottom:2px solid {_PRIMARY} !important}}
hr{{border-color:{_SURFACE_BORDER} !important}}
{_SELECTORS["text_in"]},{_SELECTORS["select"]}{{background:rgba(10,26,58,0.8) !important;border:1px solid {_SURFACE_BORDER} !important;border-radius:8px !important;color:{_TEXT} !important}}
</style>"""


def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def app_header(title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="app-header"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def section_card(html_content: str):
    st.markdown(f'<div class="section-card">{html_content}</div>', unsafe_allow_html=True)


def status_banner(text: str, level: str = "danger"):
    st.markdown(f'<div class="status-banner {level}">{text}</div>', unsafe_allow_html=True)


def mono_box(text: str):
    st.markdown(f'<div class="mono-box">{text}</div>', unsafe_allow_html=True)


def badge(text: str, color: str = "blue") -> str:
    return f'<span class="badge-{color}">{text}</span>'
