"""Shared Centrica brand styles for Streamlit."""

CENTRICA_CSS = """
<style>
    /* Brand font and base */
    html, body, [class*="css"] {
        font-family: 'Calibri', 'Arial', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F2067 0%, #1a3080 100%);
    }
    [data-testid="stSidebar"] * {
        color: #DECFFF !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #85DB9C !important;
    }

    /* Main header */
    h1 { color: #0F2067 !important; font-family: 'Arial', sans-serif !important; font-weight: 700 !important; }
    h2 { color: #0F2067 !important; font-family: 'Arial', sans-serif !important; font-weight: 700 !important; }
    h3 { color: #9B2BF7 !important; font-family: 'Arial', sans-serif !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #DECFFF;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #0F2067;
    }
    [data-testid="stMetricLabel"] { color: #0F2067 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #0F2067 !important; }

    /* Buttons */
    .stButton > button {
        background-color: #0F2067;
        color: white;
        border: none;
        border-radius: 6px;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        padding: 0.5rem 1.5rem;
    }
    .stButton > button:hover {
        background-color: #9B2BF7;
        color: white;
    }

    /* Success / info messages */
    .stAlert[data-baseweb="notification"] { border-radius: 6px; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #DECFFF;
        border-radius: 8px 8px 0 0;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #0F2067;
        font-weight: 600;
        font-family: 'Arial', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0F2067 !important;
        color: white !important;
        border-radius: 6px;
    }

    /* Risk badges */
    .risk-high { color: #9B2BF7; font-weight: bold; }
    .risk-medium { color: #B999F6; font-weight: bold; }
    .risk-low { color: #85DB9C; font-weight: bold; }

    /* Dataframe */
    .stDataFrame { border: 1px solid #DECFFF; border-radius: 6px; }

    /* Chat messages */
    .stChatMessage { border-radius: 8px; }
</style>
"""


def header_html(title: str, subtitle: str = "") -> str:
    return f"""
    <div style="background:linear-gradient(90deg,#0F2067 60%,#9B2BF7 100%);
                padding:1.2rem 1.8rem; border-radius:10px; margin-bottom:1rem;">
        <h1 style="color:white;margin:0;font-family:Arial,sans-serif;font-size:1.6rem;">{title}</h1>
        {'<p style="color:#85DB9C;margin:0.3rem 0 0;font-size:0.9rem;">' + subtitle + '</p>' if subtitle else ''}
    </div>
    """


def risk_badge(severity: str) -> str:
    colors = {"High": "#9B2BF7", "Medium": "#B999F6", "Low": "#85DB9C"}
    color = colors.get(severity, "#DECFFF")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;font-weight:bold;">{severity}</span>'
