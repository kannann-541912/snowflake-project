"""
Mastech Brand-Aligned Streamlit Theme
Dark Mode | Enterprise AI UI | Snowflake Warehouse Runtime
"""

import streamlit as st


_PRIMARY_BLUE = "#0d558b"
_ACCENT_BLUE = "#01b8fb"
_DARK_BG = "#000000"
_DARK_BG_ALT = "#0A4672"
_LIGHT_ACCENT = "#ecf6fd"
_MUTED_BLUE = "#8ec9f5"
_BORDER = "rgba(255,255,255,0.1)"

_TEXT_PRIMARY = _LIGHT_ACCENT
_TEXT_SECONDARY = _MUTED_BLUE

_SUCCESS = _ACCENT_BLUE
_WARNING = "#009bd9"


CHART_COLORS = {
    "productive": "#1abc9c",
    "idle": "#f39c12",
    "line": "#74b9ff",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#ffffff', size=13),
    title_font=dict(color='#74b9ff', size=15),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    ),
    xaxis=dict(
        gridcolor='#2d3250',
        tickfont=dict(color='#a8d8f0')
    ),
    yaxis=dict(
        gridcolor='#2d3250',
        tickfont=dict(color='#a8d8f0')
    )
)


THEME_CSS = f"""
<style>
  .stApp {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif,
                 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji';
    background-color: {_DARK_BG} !important;
    color: {_TEXT_PRIMARY} !important;
  }}

  .block-container {{
    max-width: 100% !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
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
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff !important;
  }}

  .app-header p {{
    color: {_TEXT_SECONDARY};
    font-size: 1.15rem;
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
    font-size: 1.0rem;
    color: {_TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}

  .kpi-value {{
    font-size: 2.2rem;
    font-weight: 700;
  }}

  .kpi-delta-up {{
    color: {_ACCENT_BLUE};
  }}

  .kpi-delta-down {{
    color: {_WARNING};
  }}

  /* ---------- TABS (stable data-testid selector) ---------- */
  [data-testid="stTabs"] button {{
    background: transparent !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 8px !important;
    color: {_TEXT_SECONDARY} !important;
    padding: 8px 18px !important;
  }}

  [data-testid="stTabs"] button[aria-selected="true"] {{
    background: rgba(1,184,251,0.1) !important;
    border-color: {_ACCENT_BLUE} !important;
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- EXPANDER ---------- */
  [data-testid="stExpander"] {{
    margin-bottom: 12px;
  }}

  [data-testid="stExpander"] summary {{
    color: #ffffff !important;
  }}

  /* ---------- MARKDOWN CONTENT ---------- */
  [data-testid="stMarkdownContainer"] p {{
    line-height: 1.8;
    margin-bottom: 0.4rem;
    color: #ffffff !important;
  }}
  [data-testid="stMarkdownContainer"] li {{
    line-height: 1.8;
    color: #ffffff !important;
  }}
  [data-testid="stMarkdownContainer"] strong {{
    color: #ffffff !important;
  }}
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {{
    color: #ffffff !important;
  }}

  /* ---------- TEXT SELECTION HIGHLIGHT ---------- */
  ::selection {{
    background: rgba(1,184,251,0.4) !important;
    color: #ffffff !important;
  }}

  /* ---------- INPUTS (stable data-testid selectors) ---------- */
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"],
  [data-testid="stTextInput"] {{
    color: {_TEXT_PRIMARY} !important;
  }}

  /* ---------- CAPTIONS / LABELS ---------- */
  [data-testid="stCaption"] {{
    color: #8ec9f5 !important;
  }}
  [data-testid="stWidgetLabel"] {{
    color: #8ec9f5 !important;
  }}

  /* ---------- INFO / ALERT BOXES ---------- */
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

  /* ---------- STATUS BANNER ---------- */
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

  /* ---------- METRIC CARD ---------- */
  .metric-card {{
    background: linear-gradient(180deg, #0d1424 0%, #131c30 100%);
    border-top: 3px solid {_ACCENT_BLUE};
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 4px 16px rgba(1,184,251,0.15);
    height: 100%;
    min-height: 90px;
  }}
  .metric-card .mc-label {{
    color: {_TEXT_SECONDARY};
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .metric-card .mc-icon {{
    font-size: 1.05rem;
  }}
  .metric-card .mc-value {{
    color: #ffffff;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .metric-card .mc-sub {{
    color: #6b7a90;
    font-size: 0.95rem;
    margin-top: 2px;
  }}

  /* ---------- INFO CARD ---------- */
  .info-card {{
    background: linear-gradient(180deg, #0d1424 0%, #131c30 100%);
    border-top: 3px solid {_ACCENT_BLUE};
    border-radius: 10px;
    padding: 10px 14px;
    box-shadow: 0 4px 16px rgba(1,184,251,0.15);
    margin-bottom: 8px;
  }}
  .info-card .ic-title {{
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 6px;
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
    padding: 4px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }}
  .info-card .ic-row:last-child {{ border-bottom: none; }}
  .info-card .ic-left {{
    display: flex;
    align-items: center;
    gap: 6px;
    color: {_TEXT_SECONDARY};
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
  }}
  .info-card .ic-left .ic-emoji {{
    font-size: 1rem;
  }}
  .info-card .ic-value {{
    color: #ffffff;
    font-size: 1.0rem;
    font-weight: 600;
    text-align: right;
  }}
  .info-card .ic-pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 700;
    letter-spacing: 0.03em;
  }}
  .info-card .ic-pill-neutral  {{ background: rgba(13,85,139,0.35); color: #cfe6ff; }}
  .info-card .ic-pill-success  {{ background: rgba(46,204,113,0.18); color: #5be39a; }}
  .info-card .ic-pill-warning  {{ background: rgba(245,166,35,0.18); color: #ffc566; }}
  .info-card .ic-pill-critical {{ background: rgba(246,173,85,0.20);  color: #f6ad55; }}
  .info-card .ic-pill-muted    {{ background: rgba(255,255,255,0.06); color: #8593a8; }}

  /* ---------- BUTTONS ---------- */
  [data-testid="stButton"] button {{
    background-color: {_ACCENT_BLUE} !important;
    color: #ffffff !important;
    border: 1px solid {_ACCENT_BLUE} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: background-color 0.2s ease !important;
  }}

  [data-testid="stButton"] button:hover {{
    background-color: #009bd9 !important;
    border-color: #009bd9 !important;
    color: #ffffff !important;
  }}

  [data-testid="stButton"] button:active {{
    background-color: {_PRIMARY_BLUE} !important;
  }}

  /* ---------- CHAT INPUT ---------- */
  [data-testid="stChatInput"] {{
    background-color: #1e2130 !important;
    border-radius: 10px !important;
  }}

  [data-testid="stChatInput"] textarea {{
    background-color: #1e2130 !important;
    color: #ffffff !important;
    border: 1px solid {_ACCENT_BLUE} !important;
    border-radius: 8px !important;
    caret-color: #ffffff !important;
  }}

  [data-testid="stChatInput"] textarea::placeholder {{
    color: #a8d8f0 !important;
    opacity: 1 !important;
  }}

  [data-testid="stChatInput"] button {{
    color: {_ACCENT_BLUE} !important;
  }}

  /* ---------- CHAT MESSAGES ---------- */
  [data-testid="stChatMessage"] {{
    background-color: #0d1424 !important;
    border-radius: 10px !important;
    border: 1px solid {_BORDER} !important;
  }}

  [data-testid="stChatMessage"] p,
  [data-testid="stChatMessage"] span,
  [data-testid="stChatMessage"] div {{
    color: #ffffff !important;
  }}

  /* ---------- DATAFRAME ---------- */
  [data-testid="stDataFrame"] {{
    background-color: #0d1424 !important;
    border-radius: 8px !important;
  }}

  [data-testid="stDataFrame"] th,
  [data-testid="stDataFrame"] td {{
    color: #ffffff !important;
  }}

</style>
"""


def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


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
        f'border-radius:10px;padding:20px 24px;font-family:monospace;font-size:1.0rem;'
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
        f'clear:both;font-size:1.05rem;color:{_TEXT_PRIMARY};line-height:1.5">{content}</div>',
        unsafe_allow_html=True,
    )


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
