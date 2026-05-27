"""
Mastech Brand-Aligned Streamlit Theme
Dark Mode | Enterprise AI UI | Snowflake-ready
"""

import streamlit as st


# =========================
# BRAND COLOR TOKENS (STRICTLY ALIGNED)
# =========================

_PRIMARY_BLUE = "#0d558b"      # Core brand blue
_ACCENT_BLUE = "#01b8fb"       # Primary CTA / highlight
_DARK_BG = "#030c25"           # Main background
_DARK_BG_ALT = "#0A4672"       # Elevated surfaces
_LIGHT_ACCENT = "#ecf6fd"      # Text / highlights
_MUTED_BLUE = "#8ec9f5"        # Secondary text
_BORDER = "rgba(255,255,255,0.1)"

_TEXT_PRIMARY = _LIGHT_ACCENT
_TEXT_SECONDARY = _MUTED_BLUE

# Status (mapped to brand palette)
_SUCCESS = _ACCENT_BLUE
_WARNING = "#009bd9"


# =========================
# THEME CSS
# =========================

THEME_CSS = f"""
<style>
  * {{
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif,
                 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji' !important;
  }}

  /* ---------- ICON FONT FIX ----------
     Streamlit renders built-in icons (sidebar collapse, expander chevron,
     selectbox caret, etc.) as Material Symbols ligatures. The universal
     * rule above overrides the icon font. Re-apply for Streamlit internals. */
  [data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons' !important;
    text-transform: none !important;
  }}

  /* ---------- GLOBAL BACKGROUND ---------- */
  html, body, .stApp {{
    background-color: {_DARK_BG} !important;
    color: {_TEXT_PRIMARY} !important;
  }}

  .block-container {{
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
  }}

  header[data-testid="stHeader"],
  [data-testid="stToolbar"] {{
    display: none !important;
  }}

  /* ---------- HIDE STREAMLIT HINTS / DECORATIONS ---------- */
  [data-testid="InputInstructions"],
  [data-testid="stWidgetLabel"] .caption,
  .viewerBadge_container__r5tak,
  footer,
  #MainMenu {{
    display: none !important;
  }}

  /* ---------- HEADER ---------- */
  .app-header {{
    background: linear-gradient(90deg, {_DARK_BG_ALT}, {_PRIMARY_BLUE});
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    border-left: 4px solid {_ACCENT_BLUE};
    box-shadow: 0 4px 24px rgba(1,184,251,0.25);
  }}

  .app-header h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
  }}

  .app-header p {{
    color: {_TEXT_SECONDARY};
    font-size: 0.9rem;
    margin-top: 4px;
  }}

  /* ---------- SECTION CARD ---------- */
  .section-card {{
    background: linear-gradient(135deg, rgba(10,70,114,0.8), rgba(3,12,37,0.9));
    border-radius: 12px;
    padding: 20px;
    border: 1px solid {_BORDER};
    margin-bottom: 16px;
  }}

  /* ---------- KPI ---------- */
  .kpi-card {{
    background: rgba(3,12,37,0.8);
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 10px 14px;
  }}

  .kpi-label {{
    font-size: 0.7rem;
    color: {_TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}

  .kpi-value {{
    font-size: 1.4rem;
    font-weight: 700;
  }}

  .kpi-delta-up {{
    color: {_ACCENT_BLUE};
  }}

  .kpi-delta-down {{
    color: {_WARNING};
  }}

  /* ---------- BUTTONS ---------- */

  /* PRIMARY */
  [data-testid="stButton"] button[kind="primary"] {{
    background: linear-gradient(90deg, {_ACCENT_BLUE}, #009bd9) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
  }}

  [data-testid="stButton"] button[kind="primary"]:hover {{
    background: linear-gradient(90deg, #009bd9, {_DARK_BG_ALT}) !important;
  }}

  /* SECONDARY */
  [data-testid="stButton"] button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid {_PRIMARY_BLUE} !important;
    color: {_TEXT_SECONDARY} !important;
  }}

  [data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: {_ACCENT_BLUE} !important;
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- TABS ---------- */
  button[data-baseweb="tab"] {{
    background: transparent !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 8px !important;
    color: {_TEXT_SECONDARY} !important;
    padding: 8px 18px !important;
  }}

  button[data-baseweb="tab"][aria-selected="true"] {{
    background: rgba(1,184,251,0.1) !important;
    border-color: {_ACCENT_BLUE} !important;
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- SUGGESTION CHIPS ---------- */
  .suggestion-chips {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}

  .suggestion-chips button {{
    background: rgba(13,85,139,0.2) !important;
    border: 1px solid {_BORDER} !important;
    color: {_TEXT_SECONDARY} !important;
    border-radius: 16px !important;
    padding: 4px 12px !important;
  }}

  .suggestion-chips button:hover {{
    border-color: {_ACCENT_BLUE} !important;
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- SIDEBAR ---------- */
  [data-testid="stSidebar"] {{
    overflow: visible !important;
  }}

  [data-testid="stSidebar"] [data-baseweb="select"] {{
    overflow: visible !important;
  }}

  [data-testid="stSidebar"] [data-baseweb="popover"] {{
    z-index: 9999 !important;
  }}

  /* ---------- POPOVER / DROPDOWN (global) ----------
     BaseWeb popovers render as DOM portals at <body> level, outside
     stApp and stSidebar — sidebar-scoped rules above cannot reach them.
     These global rules apply the dark theme to all select/multiselect
     dropdowns including the Governance tab filter widgets. */
  [data-baseweb="popover"] {{
    background: {_DARK_BG_ALT} !important;
    border: 1px solid {_ACCENT_BLUE} !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(1,184,251,0.25) !important;
    z-index: 9999 !important;
  }}
  [data-baseweb="menu"] {{
    background: {_DARK_BG_ALT} !important;
    border-radius: 8px !important;
  }}
  [data-baseweb="option"] {{
    background: transparent !important;
    color: {_TEXT_PRIMARY} !important;
  }}
  [data-baseweb="option"]:hover,
  [data-baseweb="option"][aria-selected="true"] {{
    background: rgba(1,184,251,0.15) !important;
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- EXPANDER ---------- */
  [data-testid="stExpander"] {{
    margin-bottom: 12px;
  }}

  /* ---------- MARKDOWN CONTENT ----------
     Restores line spacing lost when DM Sans + emoji fallback fonts mix
     on the same line (tool chain cards use emoji status icons). Without
     an explicit line-height the browser default ~1.2 is too tight and
     adjacent tool-card lines visually overlap. */
  [data-testid="stMarkdownContainer"] p {{
    line-height: 1.8;
    margin-bottom: 0.4rem;
  }}
  [data-testid="stMarkdownContainer"] li {{
    line-height: 1.8;
  }}

  /* ---------- STATUS ---------- */
  .status-banner {{
    padding: 10px;
    border-radius: 8px;
    font-weight: 600;
    text-align: center;
  }}

  .status-banner.success {{
    background: linear-gradient(90deg, {_ACCENT_BLUE}, #009bd9);
  }}

  .status-banner.warning {{
    background: linear-gradient(90deg, #009bd9, {_PRIMARY_BLUE});
  }}

  .status-banner.info {{
    background: linear-gradient(90deg, {_PRIMARY_BLUE}, {_DARK_BG_ALT});
  }}

  /* ---------- METRIC CARD (blue-accent KPI tile) ----------
     Used by metric_card() in streamlit_app.py investigation tab.
     REVERT: delete this rule + the .metric-card helper below to fall back
             to plain st.metric() calls. */
  .metric-card {{
    background: linear-gradient(180deg, #0d1424 0%, #131c30 100%);
    border-top: 3px solid {_ACCENT_BLUE};
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 4px 16px rgba(1,184,251,0.15);
    transition: transform .15s ease, box-shadow .15s ease;
    height: 100%;
  }}
  .metric-card:hover {{
    box-shadow: 0 6px 22px rgba(1,184,251,0.35);
  }}
  .metric-card .mc-label {{
    color: {_TEXT_SECONDARY};
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .metric-card .mc-icon {{
    font-size: 1.05rem;
  }}
  .metric-card .mc-value {{
    color: #ffffff;
    font-size: 1.75rem;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 6px;
  }}
  .metric-card .mc-sub {{
    color: #6b7a90;
    font-size: 0.78rem;
    margin-top: 2px;
  }}
  [data-testid="stColumn"] [data-testid="stMarkdownContainer"] {{
    height: 100%;
  }}

  /* ---------- INFO / TOAST BOXES ----------
     Fix default blue-on-blue readability in dark theme. */
  [data-testid="stAlert"] {{
    background: rgba(236,246,253,0.95) !important;
    border: 1px solid {_ACCENT_BLUE} !important;
    border-left: 4px solid {_ACCENT_BLUE} !important;
    border-radius: 8px !important;
    color: {_DARK_BG} !important;
  }}
  [data-testid="stAlert"] p,
  [data-testid="stAlert"] span {{
    color: {_DARK_BG} !important;
  }}
  [data-testid="stAlert"] svg {{
    fill: {_ACCENT_BLUE} !important;
  }}

  /* ---------- INFO CARD (alert context / customer profile) ----------
     Used by info_card() in streamlit_app.py.
     REVERT: delete this rule + the info_card helper to fall back
             to plain bulleted markdown lists. */
  .info-card {{
    background: linear-gradient(180deg, #0d1424 0%, #131c30 100%);
    border-top: 3px solid {_ACCENT_BLUE};
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 4px 16px rgba(1,184,251,0.15);
    margin-bottom: 12px;
  }}
  .info-card .ic-title {{
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .info-card .ic-title .ic-emoji {{
    font-size: 1.1rem;
  }}
  .info-card .ic-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }}
  .info-card .ic-row:last-child {{ border-bottom: none; }}
  .info-card .ic-left {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: {_TEXT_SECONDARY};
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }}
  .info-card .ic-left .ic-emoji {{
    font-size: 1rem;
  }}
  .info-card .ic-value {{
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 600;
    text-align: right;
  }}
  .info-card .ic-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
  }}
  .info-card .ic-pill-neutral  {{ background: rgba(13,85,139,0.35); color: #cfe6ff; }}
  .info-card .ic-pill-success  {{ background: rgba(46,204,113,0.18); color: #5be39a; }}
  .info-card .ic-pill-warning  {{ background: rgba(245,166,35,0.18); color: #ffc566; }}
  .info-card .ic-pill-critical {{ background: rgba(231,76,60,0.20);  color: #ff8a7a; }}
  .info-card .ic-pill-muted    {{ background: rgba(255,255,255,0.06); color: #8593a8; }}

</style>
"""


# =========================
# APPLY THEME
# =========================

def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


# =========================
# COMPONENTS
# =========================

def app_header(title, subtitle=""):
    st.markdown(
        f'<div class="app-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True
    )


def section_card(content):
    st.markdown(
        f'<div class="section-card">{content}</div>',
        unsafe_allow_html=True
    )


def kpi_card(label, value, delta="", direction="up"):
    delta_class = "kpi-delta-up" if direction == "up" else "kpi-delta-down"
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def status_banner(text, level="info"):
    st.markdown(
        f'<div class="status-banner {level}">{text}</div>',
        unsafe_allow_html=True
    )


def badge(text: str, color: str = "teal") -> str:
    colors = {
        "teal": f"background:{_ACCENT_BLUE};color:#fff;",
        "orange": f"background:{_WARNING};color:#fff;",
        "green": f"background:{_SUCCESS};color:#fff;",
        "blue": f"background:{_PRIMARY_BLUE};color:#fff;",
        "gray": "background:#6B7280;color:#fff;",
    }
    style = colors.get(color, colors["teal"])
    return f'<span style="{style}padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;display:inline-block">{text}</span>'


def mono_box(text: str):
    st.markdown(
        f'<div style="background:rgba(10,70,114,0.3);border:2px solid {_ACCENT_BLUE};'
        f'border-radius:10px;padding:20px 24px;font-family:monospace;font-size:0.85rem;'
        f'line-height:1.7;color:{_TEXT_PRIMARY};white-space:pre-wrap">{text}</div>',
        unsafe_allow_html=True,
    )


def governance_bar(title: str, content: str):
    st.markdown(
        f'<div style="background:{_DARK_BG};border:1px solid rgba(255,255,255,0.1);'
        f'border-radius:6px;padding:10px 14px;margin-top:16px">'
        f'<span style="color:{_ACCENT_BLUE};font-weight:700;font-size:0.78rem">{title}</span> '
        f'<span style="color:{_TEXT_SECONDARY};font-size:0.82rem">{content}</span></div>',
        unsafe_allow_html=True,
    )


def agent_answer_box(content: str):
    st.markdown(
        f'<div style="background:{_DARK_BG};border-left:4px solid {_ACCENT_BLUE};'
        f'padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0;'
        f'clear:both;font-size:0.85rem;color:{_TEXT_PRIMARY};line-height:1.5">{content}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# METRIC CARD — blue-accent KPI tile used on the Investigation tab
# REVERT: delete this function (and the .metric-card CSS rules above) to
#         fall back to plain st.metric() calls in streamlit_app.py.
# ---------------------------------------------------------------------------
_ICON_MAP = {
    "gpp_maybe": "\u26A0\uFE0F",
    "event_available": "\U0001F4C5",
    "flag": "\U0001F6A9",
    "payments": "\U0001F4B3",
    "model_training": "\U0001F916",
    "check_circle": "\u2705",
    "fact_check": "\U0001F4CB",
    "description": "\U0001F4C4",
    "shield": "\U0001F6E1\uFE0F",
    "person": "\U0001F464",
    "gavel": "\u2696\uFE0F",
    "circle": "\u26AB",
    "schedule": "\u23F0",
    "history": "\U0001F4C8",
    "account_balance": "\U0001F3E6",
    "verified_user": "\u2705",
    "report": "\U0001F4CA",
    "storefront": "\U0001F6D2",
}


def _resolve_icon(icon: str) -> str:
    return _ICON_MAP.get(icon, icon)


def metric_card(label: str, value: str, *, sub: str = "", icon: str = ""):
    icon_html = (
        f'<span class="mc-icon">{_resolve_icon(icon)}</span>'
        if icon else ""
    )
    sub_html = f'<div class="mc-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="mc-label">{icon_html}<span>{label}</span></div>'
        f'<div class="mc-value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# INFO CARD — titled card with key/value rows and tone-colored pills
# Used for "Alert context" and "Customer profile" sections.
# rows = list of (icon_name, label, value, tone) tuples.
#   tone in {"neutral", "success", "warning", "critical", "muted"}
#   - if tone is empty/"plain" the value is rendered as bold text (no pill).
# REVERT: delete this function (and the .info-card CSS rules above) to
#         fall back to plain markdown bulleted lists in streamlit_app.py.
# ---------------------------------------------------------------------------
def info_card(title: str, rows: list, *, title_icon: str = ""):
    title_icon_html = (
        f'<span class="ic-emoji">{_resolve_icon(title_icon)}</span>'
        if title_icon else ""
    )
    row_html_parts = []
    for icon, label, value, tone in rows:
        icon_html = (
            f'<span class="ic-emoji">{_resolve_icon(icon)}</span>'
            if icon else ""
        )
        if tone in ("neutral", "success", "warning", "critical", "muted"):
            value_html = (
                f'<span class="ic-pill ic-pill-{tone}">{value}</span>'
            )
        else:
            value_html = f'<span class="ic-value">{value}</span>'
        row_html_parts.append(
            f'<div class="ic-row">'
            f'<div class="ic-left">{icon_html}<span>{label}</span></div>'
            f'<div class="ic-value">{value_html}</div>'
            f'</div>'
        )
    rows_html = "".join(row_html_parts)
    st.markdown(
        f'<div class="info-card">'
        f'<div class="ic-title">{title_icon_html}<span>{title}</span></div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )