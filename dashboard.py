"""
dashboard.py — Real-Time Environmental Risk Monitor
=====================================================
UPGRADED UI: Professional hackathon-grade dashboard
Design: Dark industrial HUD — inspired by mission control stations

HOW IT WORKS:
- Reads processed_data.jsonl (written by monitoring_pipeline.py)
- Parses the latest sensor readings into a pandas DataFrame
- Renders live metrics, charts, alerts, and status banners
- Auto-refreshes every 3 seconds via st.rerun()

STREAMLIT COMPONENTS USED:
- st.set_page_config()       → tab title, icon, layout
- st.markdown()              → custom HTML/CSS styling
- st.columns()               → responsive multi-column layout
- st.metric()                → KPI cards with delta indicators
- st.line_chart()            → live trend charts
- st.dataframe()             → live data table with column config
- st.download_button()       → CSV export
- st.expander()              → collapsible sections
- st.code()                  → syntax-highlighted code blocks
- st.rerun()                 → auto-refresh loop
- time.sleep()               → refresh interval control

RUN COMMAND:
    streamlit run dashboard.py

PREREQUISITES:
    pip install streamlit pandas
    (Also run: python data_stream.py + python monitoring_pipeline.py)
"""

# ── Imports ───────────────────────────────────────────────────────────
import streamlit as st   # Web dashboard framework
import pandas as pd      # Data manipulation
import json              # Parse JSONL file
import os                # Check if files exist
import time              # Sleep for auto-refresh

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG — Must be the VERY FIRST Streamlit call in the file
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="ENV-MONITOR | Live Risk Dashboard",
    page_icon="🌍",
    layout="wide",                   # Use full browser width
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════
# CUSTOM CSS — The entire visual identity of the dashboard
# Injected via st.markdown() with unsafe_allow_html=True
# Design: Dark industrial HUD with neon accent system
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Fonts: Rajdhani (display) + DM Mono (data) ── */
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── CSS Variables: full color & spacing system ── */
:root {
    --bg-base:       #080c10;
    --bg-panel:      #0d1117;
    --bg-card:       #111823;
    --bg-hover:      #16202d;
    --border:        #1e2d3d;
    --border-bright: #2a3f54;

    --text-primary:  #e2eaf4;
    --text-secondary:#7a9ab8;
    --text-muted:    #3d5470;

    --neon-blue:     #00d4ff;
    --neon-green:    #00ff9d;
    --neon-amber:    #ffb800;
    --neon-red:      #ff3b5c;

    --safe-bg:       rgba(0, 255, 157, 0.06);
    --safe-border:   #00ff9d;
    --warn-bg:       rgba(255, 184, 0, 0.06);
    --warn-border:   #ffb800;
    --danger-bg:     rgba(255, 59, 92, 0.07);
    --danger-border: #ff3b5c;

    --font-display:  'Rajdhani', sans-serif;
    --font-mono:     'DM Mono', monospace;
    --radius:        6px;
    --radius-lg:     10px;
    --transition:    0.2s ease;
}

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-display) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stDecoration"],
[data-testid="stToolbar"] { display: none !important; }

/* ── Main content area ── */
.main .block-container {
    padding: 0 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

/* ══════════════════════════════════════════════════════
   TOP HEADER BAR
══════════════════════════════════════════════════════ */
.top-header {
    background: var(--bg-panel);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    margin: 0 -2rem 2rem -2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-logo {
    font-family: var(--font-display);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: var(--neon-blue);
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 10px;
}
.header-logo span {
    color: var(--text-secondary);
    font-weight: 400;
    letter-spacing: 0.05em;
    font-size: 0.85rem;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 20px;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-secondary);
}
.live-dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: var(--neon-green);
    border-radius: 50%;
    animation: pulse-dot 1.5s infinite;
    margin-right: 5px;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1;   box-shadow: 0 0 0 0   rgba(0,255,157,0.6); }
    50%       { opacity: 0.7; box-shadow: 0 0 0 4px rgba(0,255,157,0); }
}

/* ══════════════════════════════════════════════════════
   STATUS BANNER
══════════════════════════════════════════════════════ */
.status-banner {
    border-radius: var(--radius-lg);
    padding: 20px 28px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid;
    position: relative;
    overflow: hidden;
}
.status-banner::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 60%);
    pointer-events: none;
}
.status-safe   { background: var(--safe-bg);   border-color: var(--safe-border); }
.status-warn   { background: var(--warn-bg);   border-color: var(--warn-border); }
.status-danger { background: var(--danger-bg); border-color: var(--danger-border);
                 animation: danger-pulse 2s ease-in-out infinite; }

@keyframes danger-pulse {
    0%, 100% { box-shadow: 0 0 0 0   rgba(255, 59, 92, 0); }
    50%       { box-shadow: 0 0 20px 2px rgba(255, 59, 92, 0.15); }
}

.banner-left { display: flex; align-items: center; gap: 18px; }
.banner-icon { font-size: 2.2rem; }
.banner-title {
    font-family: var(--font-display);
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    line-height: 1;
}
.banner-subtitle {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 4px;
    letter-spacing: 0.05em;
}
.banner-safe-color   { color: var(--neon-green); }
.banner-warn-color   { color: var(--neon-amber); }
.banner-danger-color { color: var(--neon-red);   }
.banner-right {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-secondary);
    text-align: right;
    line-height: 1.7;
}

/* ══════════════════════════════════════════════════════
   METRIC CARDS
══════════════════════════════════════════════════════ */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color var(--transition), transform var(--transition);
    height: 100%;
}
.metric-card:hover { border-color: var(--border-bright); transform: translateY(-1px); }
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.card-blue::after        { background: linear-gradient(90deg, transparent, var(--neon-blue),  transparent); }
.card-orange::after      { background: linear-gradient(90deg, transparent, var(--neon-amber), transparent); }
.card-teal::after        { background: linear-gradient(90deg, transparent, var(--neon-green), transparent); }
.card-alert-red::after   { background: var(--neon-red); }
.card-alert-amber::after { background: var(--neon-amber); }
.card-alert-green::after { background: var(--neon-green); }

.card-label {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 10px;
}
.card-value {
    font-family: var(--font-display);
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 8px;
    letter-spacing: -0.01em;
}
.val-blue   { color: var(--neon-blue);  }
.val-orange { color: var(--neon-amber); }
.val-teal   { color: var(--neon-green); }
.val-red    { color: var(--neon-red);   }

.card-sub {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    padding: 4px 10px;
    border-radius: 4px;
    display: inline-block;
    font-weight: 500;
}
.sub-safe   { background: rgba(0,255,157,0.1); color: var(--neon-green); }
.sub-warn   { background: rgba(255,184,0,0.1); color: var(--neon-amber); }
.sub-danger { background: rgba(255,59,92,0.1); color: var(--neon-red);   }

/* ══════════════════════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════════════════════ */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.8rem 0 1rem 0;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.section-header-title {
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-secondary);
}
.section-header-line { flex: 1; height: 1px; background: var(--border); }

/* ══════════════════════════════════════════════════════
   ALERT PANEL
══════════════════════════════════════════════════════ */
.alert-item {
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 3px solid;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.alert-danger { background: rgba(255,59,92,0.07); border-color: var(--neon-red); }
.alert-warn   { background: rgba(255,184,0,0.07); border-color: var(--neon-amber); }
.alert-safe   { background: rgba(0,255,157,0.07); border-color: var(--neon-green); }

.alert-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 1px; }
.alert-title {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    margin-bottom: 3px;
}
.alert-title-danger { color: var(--neon-red);   }
.alert-title-warn   { color: var(--neon-amber); }
.alert-title-safe   { color: var(--neon-green); }
.alert-advice {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ══════════════════════════════════════════════════════
   INFO STRIP
══════════════════════════════════════════════════════ */
.info-strip {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 20px;
    display: flex;
    align-items: center;
    gap: 30px;
    font-family: var(--font-mono);
    font-size: 0.73rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.info-item { display: flex; align-items: center; gap: 6px; }
.info-key  { color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }
.info-val  { color: var(--text-primary); font-weight: 500; }

/* ══════════════════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
══════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
}
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
    border-radius: var(--radius) !important;
    padding: 6px 16px !important;
    transition: all var(--transition) !important;
}
.stDownloadButton > button:hover {
    border-color: var(--neon-blue) !important;
    color: var(--neon-blue) !important;
    background: rgba(0,212,255,0.05) !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden;
}
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════
PROCESSED_FILE = "processed_data.jsonl"  # Written by monitoring_pipeline.py
REFRESH_SECS   = 3                       # Auto-refresh interval in seconds
MAX_ROWS       = 60                      # Keep last N readings in memory

# ══════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ══════════════════════════════════════════════════════════════════════

def load_data() -> pd.DataFrame:
    """
    Read processed JSONL output from monitoring_pipeline.py.
    Returns the latest MAX_ROWS rows as a sorted DataFrame.
    Returns an empty DataFrame if the file doesn't exist yet.
    """
    if not os.path.exists(PROCESSED_FILE):
        return pd.DataFrame()

    rows = []
    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines silently
    except Exception:
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp").tail(MAX_ROWS).reset_index(drop=True)
    return df


def get_risk_level(aqi: int, temp: float, humid: int) -> str:
    """
    Compute overall risk level.
    Returns: 'danger', 'warn', or 'safe'
    Mirrors the same thresholds used in monitoring_pipeline.py.
    """
    if aqi > 150 or temp > 40 or humid > 80:
        return "danger"
    elif aqi > 100 or temp > 35 or humid > 60:
        return "warn"
    return "safe"


def status_config(level: str) -> dict:
    """Returns display config dict for the given risk level."""
    return {
        "safe": {
            "icon": "✅", "label": "ALL SYSTEMS SAFE",
            "subtitle": "All environmental conditions within normal thresholds",
            "banner_css": "status-safe", "color_css": "banner-safe-color",
        },
        "warn": {
            "icon": "⚠️", "label": "CAUTION ADVISORY",
            "subtitle": "One or more conditions approaching unsafe thresholds",
            "banner_css": "status-warn", "color_css": "banner-warn-color",
        },
        "danger": {
            "icon": "🚨", "label": "RISK DETECTED",
            "subtitle": "Immediate attention required — unsafe conditions active",
            "banner_css": "status-danger", "color_css": "banner-danger-color",
        },
    }.get(level, {"icon": "⏳", "label": "LOADING", "subtitle": "",
                  "banner_css": "status-safe", "color_css": "banner-safe-color"})


def aqi_badge(aqi: int):
    if aqi > 150: return "sub-danger", "UNSAFE AIR"
    if aqi > 100: return "sub-warn",   "MODERATE"
    return "sub-safe", "GOOD"

def temp_badge(temp: float):
    if temp > 40: return "sub-danger", "HEAT RISK"
    if temp > 35: return "sub-warn",   "WARM"
    return "sub-safe", "NORMAL"

def humid_badge(humid: int):
    if humid > 80: return "sub-danger", "HIGH MOISTURE"
    if humid > 60: return "sub-warn",   "ELEVATED"
    return "sub-safe", "NORMAL"


def build_alerts(aqi: int, temp: float, humid: int) -> list:
    """Build the list of active alert messages with type, icon, title, advice."""
    alerts = []

    # AQI alerts
    if aqi > 150:
        alerts.append({"type": "danger", "icon": "💨",
            "title": f"UNSAFE AIR QUALITY  —  AQI {aqi}",
            "advice": "Avoid all outdoor activity. Wear N95 mask if you must go outside. Close windows and use air purifiers indoors."})
    elif aqi > 100:
        alerts.append({"type": "warn", "icon": "💨",
            "title": f"MODERATE AIR QUALITY  —  AQI {aqi}",
            "advice": "Sensitive groups (elderly, children, asthma patients) should limit outdoor exposure."})

    # Temperature alerts
    if temp > 40:
        alerts.append({"type": "danger", "icon": "🌡️",
            "title": f"EXTREME HEAT RISK  —  {temp:.1f}°C",
            "advice": "Drink water every 20 minutes. Stay in shade or air-conditioned spaces. Avoid strenuous activity outdoors."})
    elif temp > 35:
        alerts.append({"type": "warn", "icon": "🌡️",
            "title": f"ELEVATED TEMPERATURE  —  {temp:.1f}°C",
            "advice": "Stay hydrated. Wear light clothing. Check on vulnerable individuals."})

    # Humidity alerts
    if humid > 80:
        alerts.append({"type": "danger", "icon": "💧",
            "title": f"HIGH MOISTURE ALERT  —  {humid}%",
            "advice": "Risk of mold growth and heat stress. Use dehumidifiers. Ensure adequate ventilation."})
    elif humid > 60:
        alerts.append({"type": "warn", "icon": "💧",
            "title": f"ELEVATED HUMIDITY  —  {humid}%",
            "advice": "Monitor for discomfort. Ensure good airflow. Stay hydrated."})

    # All clear
    if not alerts:
        alerts.append({"type": "safe", "icon": "✅",
            "title": "ALL CLEAR — No active risks detected",
            "advice": "All readings are within safe thresholds. Continue routine monitoring."})

    return alerts


# ══════════════════════════════════════════════════════════════════════
# UI RENDERING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def render_top_bar(last_ts: str, total_rows: int):
    """Sticky top header with logo and live status info."""
    st.markdown(f"""
    <div class="top-header">
        <div class="header-logo">
            🌍 ENV-MONITOR
            <span>/ Real-Time Environmental Risk System</span>
        </div>
        <div class="header-right">
            <span><span class="live-dot"></span> LIVE STREAM</span>
            <span>READINGS: {total_rows}</span>
            <span>LAST UPDATE: {last_ts}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_info_strip(df: pd.DataFrame):
    """Compact info bar showing location, sensor, timestamp, status."""
    latest   = df.iloc[-1]
    sensor   = latest.get("sensor_id", "—")
    ts_str   = str(latest.get("timestamp", ""))[:19]
    location = latest.get("location", latest.get("sensor_id", "LOCAL NODE"))
    overall  = latest.get("overall_status", "—")

    st.markdown(f"""
    <div class="info-strip">
        <div class="info-item">
            <span class="info-key">📍 Location</span>
            <span class="info-val">{location}</span>
        </div>
        <div class="info-item">
            <span class="info-key">📡 Sensor</span>
            <span class="info-val">{sensor}</span>
        </div>
        <div class="info-item">
            <span class="info-key">🕐 Last Update</span>
            <span class="info-val">{ts_str}</span>
        </div>
        <div class="info-item">
            <span class="info-key">📊 Pipeline Status</span>
            <span class="info-val">{overall}</span>
        </div>
        <div class="info-item">
            <span class="info-key">⏱ Refresh Rate</span>
            <span class="info-val">Every {REFRESH_SECS}s</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_banner(level: str, aqi: int, temp: float, humid: int):
    """Full-width status banner coloured by current risk level."""
    cfg = status_config(level)
    ts  = pd.Timestamp.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="status-banner {cfg['banner_css']}">
        <div class="banner-left">
            <div class="banner-icon">{cfg['icon']}</div>
            <div>
                <div class="banner-title {cfg['color_css']}">{cfg['label']}</div>
                <div class="banner-subtitle">{cfg['subtitle']}</div>
            </div>
        </div>
        <div class="banner-right">
            <div>AQI <strong>{aqi}</strong> &nbsp;|&nbsp;
                 TEMP <strong>{temp:.1f}°C</strong> &nbsp;|&nbsp;
                 HUMIDITY <strong>{humid}%</strong></div>
            <div>Evaluated at {ts}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(icon: str, title: str):
    """Labelled section divider with horizontal rule."""
    st.markdown(f"""
    <div class="section-header">
        <span style="font-size:1rem">{icon}</span>
        <span class="section-header-title">{title}</span>
        <div class="section-header-line"></div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_cards(aqi: int, temp: float, humid: int):
    """Three custom metric cards — AQI, Temperature, Humidity."""
    aqi_cls,  aqi_lbl  = aqi_badge(aqi)
    tmp_cls,  tmp_lbl  = temp_badge(temp)
    hum_cls,  hum_lbl  = humid_badge(humid)

    # Card top-border accent color based on risk
    aqi_accent  = "card-alert-red"   if aqi  > 150 else ("card-alert-amber" if aqi  > 100 else "card-blue")
    temp_accent = "card-alert-red"   if temp > 40  else ("card-alert-amber" if temp > 35  else "card-orange")
    hum_accent  = "card-alert-red"   if humid > 80 else ("card-alert-amber" if humid > 60 else "card-teal")

    # Value color based on risk
    aqi_vc  = "val-red"    if aqi  > 150 else ("val-orange" if aqi  > 100 else "val-blue")
    temp_vc = "val-red"    if temp > 40  else ("val-orange" if temp > 35  else "val-orange")
    hum_vc  = "val-red"    if humid > 80 else ("val-orange" if humid > 60 else "val-teal")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card {aqi_accent}">
            <div class="card-label">💨 Air Quality Index</div>
            <div class="card-value {aqi_vc}">{aqi}</div>
            <span class="card-sub {aqi_cls}">{aqi_lbl}</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card {temp_accent}">
            <div class="card-label">🌡️ Temperature</div>
            <div class="card-value {temp_vc}">{temp:.1f}<small style="font-size:1.2rem"> °C</small></div>
            <span class="card-sub {tmp_cls}">{tmp_lbl}</span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card {hum_accent}">
            <div class="card-label">💧 Humidity</div>
            <div class="card-value {hum_vc}">{humid}<small style="font-size:1.2rem"> %</small></div>
            <span class="card-sub {hum_cls}">{hum_lbl}</span>
        </div>
        """, unsafe_allow_html=True)


def render_alert_panel(aqi: int, temp: float, humid: int):
    """Colour-coded alert cards with safety advice text."""
    alerts = build_alerts(aqi, temp, humid)
    for alert in alerts:
        t    = alert["type"]
        tcls = f"alert-title-{t}"
        st.markdown(f"""
        <div class="alert-item alert-{t}">
            <div class="alert-icon">{alert['icon']}</div>
            <div>
                <div class="alert-title {tcls}">{alert['title']}</div>
                <div class="alert-advice">ℹ️ {alert['advice']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_trend_charts(df: pd.DataFrame):
    """
    Three side-by-side line charts showing historical sensor trends.
    Uses st.line_chart() — simplest Streamlit charting component.
    Requires at least 2 data points to draw a line.
    """
    if len(df) < 2:
        st.info("📈 Collecting data — trend charts appear after 2+ readings.")
        return

    chart_df = df.set_index("timestamp")
    col1, col2, col3 = st.columns(3)

    with col1:
        render_section_header("💨", "AQI Trend")
        st.line_chart(
            chart_df[["aqi"]].rename(columns={"aqi": "AQI"}),
            height=200, color="#00d4ff"
        )

    with col2:
        render_section_header("🌡️", "Temperature Trend")
        st.line_chart(
            chart_df[["temperature_c"]].rename(columns={"temperature_c": "Temp °C"}),
            height=200, color="#ffb800"
        )

    with col3:
        render_section_header("💧", "Humidity Trend")
        st.line_chart(
            chart_df[["humidity_pct"]].rename(columns={"humidity_pct": "Humidity %"}),
            height=200, color="#00ff9d"
        )


def render_data_table(df: pd.DataFrame):
    """
    Live data table showing last 20 readings.
    Includes a CSV download button for data export.
    """
    display_cols = ["timestamp", "sensor_id", "aqi", "temperature_c",
                    "humidity_pct", "overall_status"]
    available    = [c for c in display_cols if c in df.columns]
    table_df     = df[available].tail(20).sort_values("timestamp", ascending=False)

    col_left, col_right = st.columns([4, 1])
    with col_left:
        render_section_header("📋", "Live Data Stream (Last 20 Readings)")
    with col_right:
        st.download_button(
            label="⬇ Export CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="env_monitor_export.csv",
            mime="text/csv",
            help="Download all current session data as a CSV file"
        )

    # st.dataframe with column_config gives nice labels and formatting
    st.dataframe(
        table_df.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp":      st.column_config.DatetimeColumn("Timestamp",   format="HH:mm:ss"),
            "sensor_id":      st.column_config.TextColumn("Sensor"),
            "aqi":            st.column_config.NumberColumn("AQI",           format="%d"),
            "temperature_c":  st.column_config.NumberColumn("Temp °C",       format="%.1f"),
            "humidity_pct":   st.column_config.NumberColumn("Humidity %",    format="%d%%"),
            "overall_status": st.column_config.TextColumn("Status"),
        }
    )


def render_waiting_screen():
    """Full-screen waiting state shown before data starts flowing."""
    st.markdown("""
    <div style="
        text-align: center; padding: 80px 40px;
        border: 1px dashed #1e2d3d; border-radius: 10px;
        background: #0d1117; margin: 40px 0;
    ">
        <div style="font-size: 3rem; margin-bottom: 16px;">⏳</div>
        <div style="font-family: 'Rajdhani', sans-serif; font-size: 1.4rem;
                    font-weight: 700; color: #00d4ff; letter-spacing: 0.1em; margin-bottom: 8px;">
            WAITING FOR DATA STREAM
        </div>
        <div style="font-family: 'DM Mono', monospace; font-size: 0.8rem;
                    color: #7a9ab8; margin-bottom: 28px; line-height: 1.7;">
            No data detected yet. Open two more terminals and start the pipeline.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("▶  HOW TO START THE SYSTEM", expanded=True):
        st.code(
            "# Terminal 1 — Start sensor data generator\n"
            "python data_stream.py\n\n"
            "# Terminal 2 — Start Pathway streaming pipeline\n"
            "python monitoring_pipeline.py\n\n"
            "# Terminal 3 — This dashboard (already running)\n"
            "streamlit run dashboard.py",
            language="bash"
        )


# ══════════════════════════════════════════════════════════════════════
# MAIN — Entry point, called every refresh cycle
# ══════════════════════════════════════════════════════════════════════

def main():

    # ── 1. Load data from pipeline output file ──────────────────────
    df = load_data()

    # ── 2. Show waiting screen if no data yet ──────────────────────
    if df.empty:
        render_top_bar("—", 0)
        render_waiting_screen()
        time.sleep(REFRESH_SECS)
        st.rerun()
        return

    # ── 3. Extract latest reading values ───────────────────────────
    latest = df.iloc[-1]
    aqi    = int(latest.get("aqi", 0))
    temp   = float(latest.get("temperature_c", 0))
    humid  = int(latest.get("humidity_pct", 0))
    ts_str = str(latest.get("timestamp", ""))[:19]
    level  = get_risk_level(aqi, temp, humid)

    # ── 4. Header bar ──────────────────────────────────────────────
    render_top_bar(ts_str, len(df))

    # ── 5. Info strip (location, sensor, timestamp) ────────────────
    render_info_strip(df)

    # ── 6. Status banner ───────────────────────────────────────────
    render_status_banner(level, aqi, temp, humid)

    # ── 7. Metric cards (left 2/3) + Alert panel (right 1/3) ───────
    metrics_col, alerts_col = st.columns([2, 1], gap="large")

    with metrics_col:
        render_section_header("📡", "Current Sensor Readings")
        render_metric_cards(aqi, temp, humid)

    with alerts_col:
        render_section_header("🚨", "Active Alerts & Safety Advice")
        render_alert_panel(aqi, temp, humid)

    # ── 8. Trend charts ────────────────────────────────────────────
    render_trend_charts(df)

    # ── 9. Data table + export button ─────────────────────────────
    render_data_table(df)

    # ── 10. System info collapsible ────────────────────────────────
    with st.expander("⚡  SYSTEM INFO — Pathway Streaming Architecture"):
        st.markdown("""
**How data flows through the system:**
```
data_stream.py → sensor_data.jsonl → monitoring_pipeline.py → processed_data.jsonl → dashboard.py
  [Producer]       [Stream Buffer]      [Stream Processor]        [Output Sink]        [Consumer]
```
This mirrors Apache Kafka architecture. Upgrade to Kafka by replacing one line:
```python
# Current (file mode):
pw.io.jsonlines.read(INPUT_FILE, schema=SensorSchema, mode="streaming")
# Production (Kafka mode):
pw.io.kafka.read(rdkafka_settings, topic="env-sensors", schema=SensorSchema)
```
        """)

    # ── 11. Auto-refresh ───────────────────────────────────────────
    # Sleep for REFRESH_SECS, then reload the entire page with new data
    time.sleep(REFRESH_SECS)
    st.rerun()


# ── Script entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    main()
