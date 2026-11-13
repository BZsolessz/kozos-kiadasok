import re
import time
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Közös pénzügyek 🍂", page_icon="🍂", layout="wide")

if st.session_state.pop("reset_uj_tetel", False):
    st.session_state["uj_tetel_osszeg"] = ""
if st.session_state.pop("reset_uj_hitel", False):
    for k in ["uj_hitel_teljes", "uj_hitel_jelenlegi", "uj_hitel_havi"]:
        st.session_state[k] = ""

st.markdown(
    """<style>
    :root { color-scheme: dark !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior-y: contain !important;
        touch-action: pan-y !important;
        color: #f8fafc !important;
        scroll-behavior: smooth !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #080d0c !important;
        background-image:
            radial-gradient(ellipse at 12% 10%, rgba(245, 158, 11, 0.24) 0%, transparent 48%),
            radial-gradient(ellipse at 88% 20%, rgba(16, 185, 129, 0.22) 0%, transparent 50%),
            radial-gradient(ellipse at 25% 88%, rgba(217, 119, 6, 0.20) 0%, transparent 52%),
            radial-gradient(ellipse at 82% 85%, rgba(5, 150, 105, 0.18) 0%, transparent 50%),
            linear-gradient(155deg, #070c0b 0%, #0e1917 48%, #16120d 100%) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image:
            radial-gradient(2.5px 2.5px at 40px 80px, rgba(251, 191, 36, 0.65) 45%, transparent 100%),
            radial-gradient(2px 2px at 140px 210px, rgba(52, 211, 153, 0.50) 45%, transparent 100%),
            radial-gradient(3px 3px at 230px 120px, rgba(245, 158, 11, 0.55) 45%, transparent 100%),
            radial-gradient(1.5px 1.5px at 310px 270px, rgba(254, 243, 199, 0.60) 45%, transparent 100%);
        background-size: 340px 340px;
        animation: autumnGlow 18s linear infinite;
    }
    @keyframes autumnGlow {
        0% { background-position: 0px 340px, 0px 340px, 0px 340px, 0px 340px; opacity: 0.75; }
        50% { opacity: 1; }
        100% { background-position: 45px 0px, -35px 0px, 25px 0px, -20px 0px; opacity: 0.75; }
    }

    [data-testid="stHeader"] {
        background: transparent !important;
        height: 0.4rem !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Automatikus PC vs Mobil konténer méretezés */
    .block-container {
        max-width: 1120px !important;
        padding-top: 1.0rem !important;
        padding-left: 1.6rem !important;
        padding-right: 1.6rem !important;
        padding-bottom: 2.2rem !important;
        margin: 0 auto !important;
    }
    @media (max-width: 899px) {
        .block-container {
            max-width: 100% !important;
            padding-top: 0.7rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-bottom: 1.8rem !important;
        }
        /* Mobilon az oszlopok egymás alá rendeződnek a kényelmes érintéshez */
        [data-testid="stHorizontalBlock"].pc-split {
            flex-direction: column !important;
        }
    }

    .top-nav-hero {
        background: linear-gradient(135deg, rgba(16, 28, 25, 0.86) 0%, rgba(24, 20, 15, 0.84) 100%);
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 18px;
        padding: 12px 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }
    .top-nav-title {
        font-size: 1.24rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .top-nav-sub {
        font-size: 0.76rem;
        color: #cbd5e1;
        margin-top: 2px;
    }
    .top-nav-right {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .device-pill {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 999px;
        padding: 5px 11px;
        font-size: 0.72rem;
        color: #cbd5e1;
    }
    .device-pill::after { content: "💻 PC nézet"; }
    @media (max-width: 899px) {
        .device-pill::after { content: "📱 Mobil nézet"; }
        .top-nav-hero { padding: 10px 14px; }
        .top-nav-title { font-size: 1.12rem; }
    }

    .top-nav-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(52, 211, 153, 0.42);
        border-radius: 999px;
        padding: 6px 14px;
        text-align: right;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.16);
    }
    .top-nav-badge-neg {
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(251, 191, 36, 0.45);
        border-radius: 999px;
        padding: 6px 14px;
        text-align: right;
    }
    .top-nav-badge-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        display: block;
    }
    .top-nav-badge-val {
        font-size: 0.95rem;
        font-weight: 700;
        color: #6ee7b7;
    }
    .top-nav-badge-neg .top-nav-badge-val {
        color: #fcd34d;
    }

    [data-testid="stTabs"] [role="tablist"] {
        background: rgba(11, 19, 17, 0.78) !important;
        border: 1px solid rgba(251, 191, 36, 0.22) !important;
        border-radius: 15px !important;
        padding: 4px !important;
        gap: 4px !important;
        backdrop-filter: blur(14px) !important;
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        border-radius: 11px !important;
        padding: 8px 4px !important;
        margin: 0 !important;
        justify-content: center !important;
        color: #cbd5e1 !important;
        background: transparent !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stTabs"] [role="tab"] p {
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        margin: 0 !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.42), rgba(5, 150, 105, 0.42)) !important;
        border: 1px solid rgba(251, 191, 36, 0.58) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.24) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    button, input, [data-testid="stMetric"], [data-baseweb="tab"] {
        transition: all 0.20s cubic-bezier(0.22, 1, 0.36, 1) !important;
    }
    button:active { transform: scale(0.97) !important; }

    button[kind="secondary"] {
        background: rgba(14, 24, 22, 0.82) !important;
        border: 1px solid rgba(255, 255, 255, 0.11) !important;
        border-radius: 13px !important;
        color: #e2e8f0 !important;
        min-height: 44px !important;
        padding: 7px 10px !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.18) !important;
    }
    button[kind="secondary"]:hover {
        border-color: rgba(251, 191, 36, 0.45) !important;
        background: rgba(22, 36, 33, 0.90) !important;
        color: #ffffff !important;
    }
    button[kind="secondary"] p {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    .kat-selected-banner {
        background: linear-gradient(90deg, rgba(217, 119, 6, 0.22), rgba(16, 185, 129, 0.20));
        border: 1px solid rgba(251, 191, 36, 0.45);
        border-radius: 12px;
        padding: 7px 13px;
        margin: 4px 0 10px 0;
        font-size: 0.84rem;
        color: #fef3c7;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stPills"] button span {
        background: rgba(14, 23, 21, 0.82) !important;
        color: #f1f5f9 !important;
        border-color: rgba(245, 158, 11, 0.30) !important;
        border-radius: 999px !important;
    }
    [data-testid="stPills"] button[aria-pressed="true"],
    [data-testid="stPills"] button[aria-pressed="true"] p,
    [data-testid="stPills"] button[aria-pressed="true"] span {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.75), rgba(5, 150, 105, 0.75)) !important;
        border-color: #fbbf24 !important;
        color: #ffffff !important;
        box-shadow: 0 0 14px rgba(245, 158, 11, 0.32) !important;
    }

    [data-testid="stMetric"] {
        background: rgba(13, 22, 20, 0.68) !important;
        border: 1px solid rgba(251, 191, 36, 0.24) !important;
        border-radius: 15px !important;
        padding: 11px 14px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
    }

    /* Új kompakt Statisztika kártyák */
    .stat-glass-card {
        background: linear-gradient(145deg, rgba(15, 25, 23, 0.82), rgba(11, 18, 16, 0.78));
        border: 1px solid rgba(251, 191, 36, 0.22);
        border-radius: 18px;
        padding: 14px 16px;
        margin-bottom: 12px;
        backdrop-filter: blur(14px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
    }
    .stat-card-header {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #fbbf24;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .stat-kpi-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
    }
    @media (max-width: 540px) {
        .stat-kpi-grid { grid-template-columns: 1fr; }
    }
    .stat-kpi-box {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 13px;
        padding: 10px 12px;
    }
    .stat-kpi-lbl {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-bottom: 3px;
    }
    .stat-kpi-num {
        font-size: 1.12rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .split-bar-wrap {
        width: 100%;
        height: 10px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        overflow: hidden;
        display: flex;
        margin: 8px 0 6px 0;
    }
    .split-bar-zsolt {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        height: 100%;
    }
    .split-bar-vivien {
        background: linear-gradient(90deg, #10b981, #34d399);
        height: 100%;
    }
    .compact-cat-row {
        padding: 7px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .compact-cat-row:last-child { border-bottom: none; }
    .compact-cat-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.86rem;
        margin-bottom: 4px;
    }
    .compact-cat-bar-bg {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.07);
        border-radius: 999px;
        overflow: hidden;
    }
    .compact-cat-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #f59e0b, #10b981);
    }
    .kat-arany-szazalek {
        background: rgba(245, 158, 11, 0.20);
        border: 1px solid rgba(251, 191, 36, 0.42);
        color: #fcd34d;
        font-weight: 700;
        font-size: 0.74rem;
        padding: 1px 7px;
        border-radius: 999px;
        margin-left: 5px;
    }

    /* Modern előzmény kártyák */
    .tx-summary-bar {
        background: rgba(13, 22, 20, 0.65);
        border: 1px solid rgba(251, 191, 36, 0.20);
        border-radius: 14px;
        padding: 8px 14px;
        margin: 6px 0 10px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.83rem;
        color: #cbd5e1;
    }
    .tx-card {
        background: linear-gradient(135deg, rgba(16, 26, 24, 0.82), rgba(12, 20, 18, 0.76));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #f59e0b;
        border-radius: 14px;
        padding: 10px 13px;
        margin-bottom: 4px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.22);
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
    }
    .tx-card-bev { border-left-color: #10b981; }
    .tx-card-hitel { border-left-color: #38bdf8; }
    .tx-card-tart { border-left-color: #f43f5e; }
    .tx-card-del {
        background: rgba(127, 29, 29, 0.42);
        border: 1px solid rgba(248, 113, 113, 0.65);
        border-left: 4px solid #ef4444;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.25);
    }
    .tx-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f8fafc;
        line-height: 1.25;
    }
    .tx-meta {
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 3px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
    }
    .tx-pill {
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.10);
        color: #e2e8f0;
        padding: 1px 8px;
        border-radius: 999px;
        font-size: 0.70rem;
    }
    .tx-amount {
        font-size: 0.98rem;
        font-weight: 700;
        white-space: nowrap;
        text-align: right;
    }
    .tx-amt-ki { color: #fbbf24; }
    .tx-amt-bev { color: #34d399; }
    .tx-amt-hitel { color: #7dd3fc; }
    .tx-amt-tart { color: #fda4af; }

    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"] {
        max-height: 55vh !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: pan-y !important;
        background-color: #0e1917 !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

def hangeffekt(tipus="siker"):
    components.html(
        f"""<script>try {{
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime, t = "{tipus}";
            function p(f, s, d, y='sine', v=0.20) {{
                const o = ctx.createOscillator(), g = ctx.createGain();
                o.type = y; o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(v, s); g.gain.exponentialRampToValueAtTime(0.001, s + d);
                o.connect(g); g.connect(ctx.destination); o.start(s); o.stop(s + d);
            }}
            if (t==="siker") {{
                p(349.23, now, 0.45, 'sine', 0.18);
                p(440.00, now+0.09, 0.45, 'sine', 0.18);
                p(523.25, now+0.18, 0.50, 'sine', 0.20);
                p(659.25, now+0.27, 0.65, 'sine', 0.22);
            }}
            else if (t==="torles") {{
                p(293.66, now, 0.28, 'sine', 0.18);
                p(220.00, now+0.13, 0.42, 'sine', 0.18);
            }}
            else if (t==="frissites") {{
                p(659.25, now, 0.12, 'sine', 0.15);
                p(987.77, now+0.08, 0.22, 'sine', 0.16);
            }}
            else if (t==="hiba") {{
                p(196.00, now, 0.15, 'triangle', 0.20);
                p(196.00, now+0.17, 0.20, 'triangle', 0.20);
            }}
        }} catch (e) {{}}</script>""",
        height=0,
    )

def fmt_ft(ertek):
    return f"{int(ertek):,}".replace(",", ".")

def osszeg_mezo(cimke, key, alap_ertek=0):
    if key not in st.session_state:
        st.session_state[key] = fmt_ft(alap_ertek) if alap_ertek > 0 else ""

    def formaz():
        szamjegyek = re.sub(r"\D", "", st.session_state[key])
        st.session_state[key] = fmt_ft(int(szamjegyek)) if szamjegyek else ""

    nyers = st.text_input(cimke, key=key, placeholder="pl. 15.000", on_change=formaz)
    szamjegyek = re.sub(r"\D", "", nyers)
    ertek = int(szamjegyek) if szamjegyek else 0
    if ertek > 0:
        st.caption(f"💰 Rögzítendő összeg: **{fmt_ft(ertek)} Ft**")
    return ertek

def kategoria_racs_valaszto(opciok_lista, state_key):
    if state_key not in st.session_state or st.session_state[state_key] not in [o[0] for o in opciok_lista]:
        st.session_state[state_key] = opciok_lista[0][0]

    aktualis = st.session_state[state_key]
    for i in range(0, len(opciok_lista), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(opciok_lista):
                valos_nev, rovid_cimke = opciok_lista[i + j]
                kivalasztva = (valos_nev == aktualis)
                gomb_felirat = f"✓ {rovid_cimke}" if kivalasztva else rovid_cimke
                if cols[j].button(
                    gomb_felirat,
                    key=f"{state_key}_btn_{i+j}",
                    use_container_width=True,
                    type="primary" if kivalasztva else "secondary",
                ):
                    st.session_state[state_key] = valos_nev
                    st.rerun()

    kivalasztott_rovid = next((r for v, r in opciok_lista if v == st.session_state[state_key]), st.session_state[state_key])
    st.markdown(
        f"""<div class="kat-selected-banner">
            <span>Kiválasztott kategória:</span>
            <b>{kivalasztott_rovid}</b>
        </div>""",
        unsafe_allow_html=True,
    )
    return st.session_state[state_key]

def parse_datum(datum_ertek):
    tisztitott = re.sub(r"[.\s/]+", "-", str(datum_ertek).strip()).strip("-")
    return pd.to_datetime(tisztitott, errors="coerce")

def datum_e_honapban_van_e(datum_ertek, ev, honap):
    dt = parse_datum(datum_ertek)
    if pd.isna(dt):
        return False
    return dt.year == ev and dt.month == honap

HONAP_NEVEK = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember", "október", "november", "december"]

def honap_cimke(ym_str):
    try:
        ev, ho = ym_str.split("-")
        return f"{ev}. {HONAP_NEVEK[int(ho) - 1]}"
    except Exception:
        return ym_str

@st.cache_resource
def csatlakozas_sheetshez():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    except Exception:
        creds = Credentials.from_service_account_file("kulcs.json", scopes=scopes)
    return gspread.authorize(creds).open("Kozos_Kiadasok").sheet1

try:
    sheet = csatlakozas_sheetshez()
except Exception as e:
    st.error(f"Csatlakozási hiba: {e}")
    st.stop()

@st.cache_data(ttl=60, show_spinner=False)
def adatok_betoltese():
    rekordok = sheet.get_all_records()
    if not rekordok:
        return pd.DataFrame(columns=["Sheet_Row", "Dátum", "Ki", "Kategória", "Megnevezés", "Összeg", "Ev_Honap"])
    df = pd.DataFrame(rekordok)
    df["Sheet_Row"] = range(2, len(df) + 2)
    df["Összeg"] = pd.to_numeric(df["Összeg"], errors="coerce").fillna(0).astype(int)
    dt_sorozat = df["Dátum"].apply(parse_datum)
    df["Ev_Honap"] = dt_sorozat.apply(lambda d: f"{d.year}-{d.month:02d}" if pd.notna(d) else "Ismeretlen")
    return df

df = adatok_betoltese()

if not df.empty:
    _bev = df[df["Kategória"].str.startswith("Bevétel:", na=False)]["Összeg"].sum()
    _ki = df[(~df["Kategória"].str.startswith("Bevétel:", na=False)) & (~df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))]["Összeg"].sum()
    aktualis_egyenleg = int(_bev - _ki)
else:
    aktualis_egyenleg = 0

ma_fejlec = date.today()
badge_osztaly = "top-nav-badge" if aktualis_egyenleg >= 0 else "top-nav-badge-neg"

st.markdown(
    f"""<div class="top-nav-hero">
        <div>
            <div class="top-nav-title">🍂 Közös pénzügyek</div>
            <div class="top-nav-sub">Zsolt &amp; Vivien • {ma_fejlec.year}. {HONAP_NEVEK[ma_fejlec.month - 1]} {ma_fejlec.day}.</div>
        </div>
        <div class="top-nav-right">
            <span class="device-pill"></span>
            <div class="{badge_osztaly}">
                <span class="top-nav-badge-label">Kassza egyenleg</span>
                <span class="top-nav-badge-val">{fmt_ft(aktualis_egyenleg)} Ft</span>
            </div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

tab_uj, tab_stat, tab_hitel, tab_lista = st.tabs(["🍁 Új tétel", "📊 Statisztika", "🏦 Hitel", "📜 Előzmények"])

with tab_uj:
    col_uj_bal, col_uj_jobb = st.columns([1.25, 1], gap="large")
    with col_uj_bal:
        tipus = st.radio("Művelet típusa", ["➖ Kiadás", "➕ Bevétel"], horizontal=True)

        if tipus == "➕ Bevétel":
            bevetel_opciok = [
                ("Közös kasszába befizetés", "💰 Kassza befizetés"),
                ("Ajándék / Támogatás", "🎁 Ajándék / Támogatás"),
                ("Eladás / Visszatérítés", "🔄 Eladás / Visszatérítés"),
                ("Egyéb bevétel", "✨ Egyéb bevétel"),
            ]
            kategoria_valasztott = kategoria_racs_valaszto(bevetel_opciok, "valasztott_bev_kat")
            kategoria = f"Bevétel: {kategoria_valasztott}"
        else:
            kiadas_opciok = [
                ("Élelmiszer & Háztartás", "🛒 Élelmiszer"),
                ("Gyógyszertár", "💊 Gyógyszertár"),
                ("Dohánybolt", "🚬 Dohánybolt"),
                ("Étterem & Randi", "🍽️ Étterem & Randi"),
                ("Üzemanyag & Autó", "⛽ Autó & Üzemanyag"),
                ("Lakhatás & Rezsi", "🏠 Lakhatás & Rezsi"),
                ("Előfizetés", "📱 Előfizetés"),
                ("Ajándékozás", "🎁 Ajándékozás"),
                ("Tech & Vásárlás", "💻 Tech & Vásárlás"),
                ("Tartozás", "💸 Tartozás"),
                ("Egyéb", "📦 Egyéb"),
            ]
            kategoria = kategoria_racs_valaszto(kiadas_opciok, "valasztott_ki_kat")

    with col_uj_jobb:
        if tipus == "➕ Bevétel":
            ki = st.text_input("Kitől kaptuk / Ki tette bele?", placeholder="pl. Zsolt, Vivien, Szülők").strip()
            megnevezes = st.text_input("Megnevezés (pl. Havi keret, Visszatérítés)")
        else:
            if kategoria == "Tartozás":
                st.info("💸 **Tartozás rögzítése**")
                c1, c2 = st.columns(2)
                ki_tartozik = c1.text_input("Ki tartozik?", placeholder="pl. Zsolt").strip()
                kinek_tartozik = c2.text_input("Kinek tartozik?", placeholder="pl. Vivien").strip()
                ki = ki_tartozik
            else:
                ki = st.radio("Ki fizette?", ["Zsolt", "Vivien"], horizontal=True)

            placeholder_szoveg = {
                "Gyógyszertár": "Mit vettetek? (pl. Gyógyszer, Vitamin, Patika)",
                "Tartozás": "Mire vonatkozik?",
                "Előfizetés": "Melyik előfizetés? (pl. Netflix, Apple Music, Internet)",
                "Dohánybolt": "Mit vettetek? (pl. Trafik, Üdítő)",
                "Ajándékozás": "Kinek és mit? (pl. Szülinapi ajándék)",
            }.get(kategoria, "Mit vettetek? (pl. Lidl, Kávézó)")
            megnevezes = st.text_input(placeholder_szoveg)

        osszeg = osszeg_mezo("Összeg (Ft)", key="uj_tetel_osszeg")
        datum = st.date_input("Dátum", value=date.today())

        if st.button("🍂 Rögzítés a felhőbe", use_container_width=True, type="primary"):
            if tipus == "➕ Bevétel" and not ki:
                hangeffekt("hiba")
                st.warning("Add meg, kitől származik a bevétel!")
            elif tipus == "➖ Kiadás" and kategoria == "Tartozás" and (not ki_tartozik or not kinek_tartozik):
                hangeffekt("hiba")
                st.warning("Írd be mindkét fél nevét a tartozásnál!")
            elif not megnevezes or osszeg <= 0:
                hangeffekt("hiba")
                st.warning("Írd be a megnevezést és egy 0-nál nagyobb összeget!")
            else:
                vegleges_nev = f"{megnevezes} ({ki_tartozik} → {kinek_tartozik})" if (tipus == "➖ Kiadás" and kategoria == "Tartozás") else megnevezes
                with st.spinner("Mentés..."):
                    sheet.append_row([str(datum), ki, kategoria, vegleges_nev, int(osszeg)])
                st.session_state["reset_uj_tetel"] = True
                adatok_betoltese.clear()
                hangeffekt("siker")
                st.toast(f"Mentve: {vegleges_nev} ({fmt_ft(osszeg)} Ft)!", icon="🍂")
                time.sleep(0.9)
                st.rerun()

with tab_stat:
    if df.empty:
        st.info("Még nincs rögzített tétel.")
    else:
        nem_hitel_df = df[~df["Kategória"].isin(["Hitel: Keret", "Hitel: Törlesztés"])]
        elerheto_honapok = sorted([h for h in nem_hitel_df["Ev_Honap"].unique() if h != "Ismeretlen"], reverse=True)

        if len(elerheto_honapok) > 1:
            opciok_map = {h: f"📅 {honap_cimke(h)}" for h in elerheto_honapok}
            opciok_map["OSSZES"] = "♾️ Összesített"
            valasztott_idoszak = st.pills(
                "Időszak",
                options=list(opciok_map.keys()),
                format_func=lambda x: opciok_map[x],
                default=elerheto_honapok[0],
                key="stat_idoszak_valaszto",
                label_visibility="collapsed",
            ) or elerheto_honapok[0]
            stat_df = df if valasztott_idoszak == "OSSZES" else df[df["Ev_Honap"] == valasztott_idoszak].copy()
            idoszak_cim = honap_cimke(valasztott_idoszak) if valasztott_idoszak != "OSSZES" else "Minden hónap"
        else:
            stat_df = df.copy()
            idoszak_cim = honap_cimke(elerheto_honapok[0]) if elerheto_honapok else "Aktuális"

        bevetelek = stat_df[stat_df["Kategória"].str.startswith("Bevétel:", na=False)].copy()
        tartozasok = stat_df[stat_df["Kategória"] == "Tartozás"].copy()
        kiadasok = stat_df[(~stat_df["Kategória"].str.startswith("Bevétel:", na=False)) & (~stat_df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))].copy()

        ossz_bevetel = int(bevetelek["Összeg"].sum()) if not bevetelek.empty else 0
        ossz_kiadas = int(kiadasok["Összeg"].sum()) if not kiadasok.empty else 0
        egyenleg = ossz_bevetel - ossz_kiadas
        egyenleg_szin = "#34d399" if egyenleg >= 0 else "#fbbf24"

        # Kompakt összesítő kártya
        st.markdown(
            f"""<div class="stat-glass-card">
                <div class="stat-card-header">
                    <span>📌 Pénzügyi mérleg</span>
                    <span style="color:#94a3b8; font-weight:500;">{idoszak_cim}</span>
                </div>
                <div class="stat-kpi-grid">
                    <div class="stat-kpi-box">
                        <div class="stat-kpi-lbl">💵 Egyenleg</div>
                        <div class="stat-kpi-num" style="color:{egyenleg_szin};">{fmt_ft(egyenleg)} Ft</div>
                    </div>
                    <div class="stat-kpi-box">
                        <div class="stat-kpi-lbl">➕ Bevétel</div>
                        <div class="stat-kpi-num" style="color:#6ee7b7;">{fmt_ft(ossz_bevetel)} Ft</div>
                    </div>
                    <div class="stat-kpi-box">
                        <div class="stat-kpi-lbl">➖ Kiadás</div>
                        <div class="stat-kpi-num" style="color:#fcd34d;">{fmt_ft(ossz_kiadas)} Ft</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Kompakt nézetválasztó a Statisztikán belül
        stat_nezet = st.pills(
            "Részletek",
            ["📤 Kiadások", "📥 Bevételek", "💸 Tartozások"],
            default="📤 Kiadások",
            key="stat_al_nezet",
            label_visibility="collapsed",
        ) or "📤 Kiadások"

        if stat_nezet == "📤 Kiadások":
            if kiadasok.empty:
                st.info("Ebben az időszakban nincs rögzített kiadás.")
            else:
                zsolt_ki = int(kiadasok[kiadasok["Ki"] == "Zsolt"]["Összeg"].sum())
                vivien_ki = int(kiadasok[kiadasok["Ki"] == "Vivien"]["Összeg"].sum())
                zsolt_pct = round(zsolt_ki / ossz_kiadas * 100, 1) if ossz_kiadas > 0 else 50.0
                vivien_pct = round(100.0 - zsolt_pct, 1) if ossz_kiadas > 0 else 50.0

                kat_osszesites = (
                    kiadasok.groupby("Kategória", as_index=False)
                    .agg(Összeg=("Összeg", "sum"), Darab=("Összeg", "count"))
                    .sort_values("Összeg", ascending=False)
                )
                kat_osszesites["Arány"] = (kat_osszesites["Összeg"] / ossz_kiadas * 100) if ossz_kiadas > 0 else 0.0

                # PC-n 2 hasábos elrendezés, mobilon egymás alatt kompakt módon
                col_s_bal, col_s_jobb = st.columns([1.05, 1.15], gap="medium")

                with col_s_bal:
                    st.markdown(
                        f"""<div class="stat-glass-card">
                            <div class="stat-card-header"><span>👥 Ki mennyit fizetett</span></div>
                            <div style="display:flex; justify-content:space-between; font-size:0.86rem;">
                                <span>🟡 <b>Zsolt:</b> {fmt_ft(zsolt_ki)} Ft ({str(zsolt_pct).replace('.', ',')}%)</span>
                                <span>🟢 <b>Vivien:</b> {fmt_ft(vivien_ki)} Ft ({str(vivien_pct).replace('.', ',')}%)</span>
                            </div>
                            <div class="split-bar-wrap">
                                <div class="split-bar-zsolt" style="width:{zsolt_pct}%;"></div>
                                <div class="split-bar-vivien" style="width:{vivien_pct}%;"></div>
                            </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    fig_ki = px.pie(
                        kat_osszesites,
                        values="Összeg",
                        names="Kategória",
                        hole=0.58,
                        color_discrete_sequence=["#f59e0b", "#10b981", "#ea580c", "#0d9488", "#eab308", "#e11d48", "#3b82f6", "#a855f7", "#14b8a6", "#ec4899"],
                    )
                    fig_ki.update_traces(textposition="inside", textinfo="percent", insidetextorientation="horizontal")
                    fig_ki.update_layout(
                        height=235,
                        margin=dict(t=8, b=8, l=4, r=4),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#f8fafc",
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=11)),
                    )
                    st.plotly_chart(fig_ki, use_container_width=True, config={"displayModeBar": False})

                with col_s_jobb:
                    sorok_html = ""
                    for _, k_sor in kat_osszesites.iterrows():
                        arany_szazalek = float(k_sor["Arány"])
                        arany_szoveg = f"{arany_szazalek:.1f}".replace(".", ",")
                        sorok_html += f"""
                        <div class="compact-cat-row">
                            <div class="compact-cat-top">
                                <div><b>{k_sor['Kategória']}</b> <span class="kat-arany-szazalek">{arany_szoveg}%</span></div>
                                <div style="color:#e2e8f0;"><b>{fmt_ft(k_sor['Összeg'])} Ft</b> <span style="color:#94a3b8; font-size:0.76rem;">({int(k_sor['Darab'])} db)</span></div>
                            </div>
                            <div class="compact-cat-bar-bg">
                                <div class="compact-cat-bar-fill" style="width:{min(100.0, arany_szazalek):.1f}%;"></div>
                            </div>
                        </div>"""

                    st.markdown(
                        f"""<div class="stat-glass-card">
                            <div class="stat-card-header">
                                <span>📊 Kategóriák aránya</span>
                                <span style="color:#94a3b8; font-weight:500;">{len(kat_osszesites)} kategória</span>
                            </div>
                            {sorok_html}
                        </div>""",
                        unsafe_allow_html=True,
                    )

        elif stat_nezet == "📥 Bevételek":
            if bevetelek.empty:
                st.info("Ebben az időszakban nincs rögzített bevétel.")
            else:
                col_b1, col_b2 = st.columns(2, gap="medium")
                with col_b1:
                    bev_forras_html = ""
                    for _, sor in bevetelek.groupby("Ki", as_index=False)["Összeg"].sum().sort_values("Összeg", ascending=False).iterrows():
                        pct = (sor["Összeg"] / ossz_bevetel * 100) if ossz_bevetel > 0 else 0.0
                        bev_forras_html += f"""
                        <div class="compact-cat-row">
                            <div class="compact-cat-top">
                                <div><b>👤 {sor['Ki']}</b> <span class="kat-arany-szazalek">{pct:.1f}%</span></div>
                                <div style="color:#6ee7b7;"><b>{fmt_ft(sor['Összeg'])} Ft</b></div>
                            </div>
                            <div class="compact-cat-bar-bg">
                                <div class="compact-cat-bar-fill" style="width:{min(100.0, pct):.1f}%;"></div>
                            </div>
                        </div>"""
                    st.markdown(
                        f"""<div class="stat-glass-card">
                            <div class="stat-card-header"><span>💰 Befizetők aránya</span></div>
                            {bev_forras_html}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with col_b2:
                    bevetelek["Típus"] = bevetelek["Kategória"].str.replace("Bevétel: ", "", regex=False)
                    fig_bev = px.pie(
                        bevetelek.groupby("Típus", as_index=False)["Összeg"].sum(),
                        values="Összeg",
                        names="Típus",
                        hole=0.58,
                        color_discrete_sequence=["#10b981", "#f59e0b", "#0ea5e9", "#d97706"],
                    )
                    fig_bev.update_traces(textposition="inside", textinfo="percent")
                    fig_bev.update_layout(
                        height=220,
                        margin=dict(t=8, b=8, l=4, r=4),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#f8fafc",
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=11)),
                    )
                    st.plotly_chart(fig_bev, use_container_width=True, config={"displayModeBar": False})

        elif stat_nezet == "💸 Tartozások":
            if tartozasok.empty:
                st.info("Ebben az időszakban nincs rögzített tartozás.")
            else:
                tartozasok["Irány"] = tartozasok["Megnevezés"].str.extract(r"\(([^)]+→[^)]+)\)")[0].fillna(tartozasok["Ki"])
                tart_html = ""
                for _, sor in tartozasok.groupby("Irány", as_index=False)["Összeg"].sum().iterrows():
                    tart_html += f"""
                    <div class="compact-cat-row">
                        <div class="compact-cat-top">
                            <b>💸 {sor['Irány']}</b>
                            <b style="color:#fda4af;">{fmt_ft(sor['Összeg'])} Ft</b>
                        </div>
                    </div>"""
                st.markdown(
                    f"""<div class="stat-glass-card">
                        <div class="stat-card-header"><span>💸 Tartozások összesítője</span></div>
                        {tart_html}
                    </div>""",
                    unsafe_allow_html=True,
                )

with tab_hitel:
    st.subheader("🏦 Hitel és törlesztés követő")
    hitel_keretek = df[df["Kategória"] == "Hitel: Keret"].copy()
    hitel_torlesztesek = df[df["Kategória"] == "Hitel: Törlesztés"].copy()

    if hitel_keretek.empty:
        st.info("Még nincs beállított hitel. Nyisd le az alábbi panelt a hitel adatainak megadásához!")
    else:
        ma = date.today()

        for _, h_sor in hitel_keretek.iterrows():
            reszek = [r.strip() for r in str(h_sor["Megnevezés"]).split("|")]
            h_nev = reszek[0]
            havi_torleszto = 0
            kezdo_datum_str = str(h_sor["Dátum"])
            vege_datum_str = ""
            for r in reszek[1:]:
                if r.startswith("havi:"):
                    try:
                        havi_torleszto = int(r.replace("havi:", "").strip())
                    except ValueError:
                        havi_torleszto = 0
                elif r.startswith("kezdet:"):
                    kezdo_datum_str = r.replace("kezdet:", "").strip()
                elif r.startswith("vege:"):
                    vege_datum_str = r.replace("vege:", "").strip()

            teljes_osszeg = int(h_sor["Összeg"])
            kapcsolodo_befizetesek = hitel_torlesztesek[hitel_torlesztesek["Megnevezés"].str.startswith(h_nev, na=False)].copy()
            eddig_kifizetve = int(kapcsolodo_befizetesek["Összeg"].sum()) if not kapcsolodo_befizetesek.empty else 0

            if not kapcsolodo_befizetesek.empty:
                ehavi_maszk = (
                    kapcsolodo_befizetesek["Dátum"].apply(lambda d: datum_e_honapban_van_e(d, ma.year, ma.month))
                    & (~kapcsolodo_befizetesek["Megnevezés"].str.contains("korábbi törlesztések", na=False))
                )
                e_havi_levonas = int(kapcsolodo_befizetesek[ehavi_maszk]["Összeg"].sum())
            else:
                e_havi_levonas = 0

            hatralevo = max(0, teljes_osszeg - eddig_kifizetve)
            szazalek = min(1.0, eddig_kifizetve / teljes_osszeg) if teljes_osszeg > 0 else 0.0

            st.markdown(f"### 📌 {h_nev}")
            idosav_szoveg = f"🗓️ Kezdet: **{kezdo_datum_str}**"
            if vege_datum_str:
                idosav_szoveg += f"  |  🏁 Vége (lejárat): **{vege_datum_str}**"
            st.caption(idosav_szoveg)
            st.progress(szazalek, text=f"Kifizetve: {szazalek*100:.1f}% ({fmt_ft(eddig_kifizetve)} Ft / {fmt_ft(teljes_osszeg)} Ft)")

            hc1, hc2 = st.columns(2)
            hc1.metric("Jelenlegi tartozás", f"{fmt_ft(hatralevo)} Ft")
            hc2.metric(f"Ebben a hónapban ({HONAP_NEVEK[ma.month - 1]})", f"{fmt_ft(e_havi_levonas)} Ft")

            if hatralevo == 0:
                st.success("🎉 Ez a hitel teljesen ki van fizetve!")
            else:
                if vege_datum_str:
                    try:
                        vege_dt = date.fromisoformat(vege_datum_str)
                        hatralevo_honapok = max(1, (vege_dt.year - ma.year) * 12 + (vege_dt.month - ma.month))
                        szukseges_havi = havi_torleszto if havi_torleszto > 0 else -(-hatralevo // hatralevo_honapok)
                        st.info(f"⏳ A megadott lejáratig (**{vege_datum_str}**) még **{hatralevo_honapok} hónap** van hátra (havi **{fmt_ft(szukseges_havi)} Ft**).")
                    except ValueError:
                        pass
                elif havi_torleszto > 0:
                    hatralevo_honapok = -(-hatralevo // havi_torleszto)
                    cel_ev = ma.year + (ma.month - 1 + hatralevo_honapok) // 12
                    cel_honap = (ma.month - 1 + hatralevo_honapok) % 12 + 1
                    st.info(f"⏳ Havi **{fmt_ft(havi_torleszto)} Ft**-os törlesztővel még **{hatralevo_honapok} hónap** van hátra → Várható lejárat: **{cel_ev}. {HONAP_NEVEK[cel_honap - 1]}**")
            st.divider()

        with st.expander("💸 Havi levonás / törlesztés rögzítése", expanded=True):
            hitel_nevek = [str(x).split("|")[0].strip() for x in hitel_keretek["Megnevezés"]]
            valasztott_hitel = st.selectbox("Melyik hitelhez?", hitel_nevek)
            alap_torleszto = 0
            for _, h_sor in hitel_keretek.iterrows():
                if str(h_sor["Megnevezés"]).split("|")[0].strip() == valasztott_hitel and "havi:" in str(h_sor["Megnevezés"]):
                    try:
                        alap_torleszto = int(str(h_sor["Megnevezés"]).split("havi:")[1].split("|")[0].strip())
                    except ValueError:
                        alap_torleszto = 0
            if st.session_state.get("utolso_valasztott_hitel") != valasztott_hitel:
                st.session_state["utolso_valasztott_hitel"] = valasztott_hitel
                st.session_state["hitel_levonas_osszeg"] = fmt_ft(alap_torleszto) if alap_torleszto > 0 else ""

            levont_osszeg = osszeg_mezo("Levont összeg (Ft)", key="hitel_levonas_osszeg", alap_ertek=alap_torleszto)
            levonas_datum = st.date_input("Levonás dátuma", value=date.today(), key="hitel_levonas_datum")

            if st.button("✅ Levonás rögzítése", use_container_width=True, type="primary"):
                if levont_osszeg <= 0:
                    hangeffekt("hiba")
                    st.warning("Adj meg 0-nál nagyobb összeget!")
                else:
                    with st.spinner("Rögzítés..."):
                        sheet.append_row([str(levonas_datum), "Zsolt", "Hitel: Törlesztés", f"{valasztott_hitel} – törlesztés", int(levont_osszeg)])
                    adatok_betoltese.clear()
                    hangeffekt("siker")
                    st.toast(f"Levonás rögzítve ({fmt_ft(levont_osszeg)} Ft)!", icon="🏦")
                    time.sleep(0.9)
                    st.rerun()

    with st.expander("⚙️ Új hitel beállítása"):
        uj_hitel_nev = st.text_input("Hitel neve (pl. Telefon részlet, Személyi kölcsön)").strip()
        d_col1, d_col2 = st.columns(2)
        uj_hitel_kezdet = d_col1.date_input("Mikor kezdődött?", value=date.today(), key="uj_hitel_kezdet")
        uj_hitel_vege = d_col2.date_input("Mikor jár le (hitel vége)?", value=date.today() + timedelta(days=365), key="uj_hitel_vege")
        uj_hitel_teljes = osszeg_mezo("Teljes visszafizetendő összeg eredetileg (Ft)", key="uj_hitel_teljes")
        uj_hitel_jelenlegi = osszeg_mezo("Jelenleg mennyi a tartozás még (Ft)", key="uj_hitel_jelenlegi")
        uj_hitel_havi = osszeg_mezo("Havi törlesztőrészlet (Ft – opcionális)", key="uj_hitel_havi")
        if st.button("💾 Hitel mentése", use_container_width=True):
            if not uj_hitel_nev or uj_hitel_teljes <= 0:
                hangeffekt("hiba")
                st.warning("Add meg a hitel nevét és a teljes összeget!")
            elif uj_hitel_jelenlegi > uj_hitel_teljes:
                hangeffekt("hiba")
                st.warning("A jelenlegi tartozás nem lehet nagyobb, mint a teljes hitelösszeg!")
            else:
                with st.spinner("Mentés..."):
                    meta = f"{uj_hitel_nev} | havi:{int(uj_hitel_havi)} | kezdet:{uj_hitel_kezdet} | vege:{uj_hitel_vege}"
                    sheet.append_row([str(uj_hitel_kezdet), "Zsolt", "Hitel: Keret", meta, int(uj_hitel_teljes)])
                    mar_kifizetett = uj_hitel_teljes - uj_hitel_jelenlegi
                    if mar_kifizetett > 0:
                        sheet.append_row([str(uj_hitel_kezdet), "Zsolt", "Hitel: Törlesztés", f"{uj_hitel_nev} – korábbi törlesztések", int(mar_kifizetett)])
                st.session_state["reset_uj_hitel"] = True
                adatok_betoltese.clear()
                hangeffekt("siker")
                st.toast(f"Hitel létrehozva: {uj_hitel_nev}!", icon="🏦")
                time.sleep(0.9)
                st.rerun()

with tab_lista:
    if df.empty:
        st.info("Még nincs rögzített tétel.")
    else:
        hdr_c1, hdr_c2 = st.columns([3.4, 1.3], vertical_alignment="center")
        hdr_c1.subheader("📜 Tranzakciók")
        if hdr_c2.button("🔄 Frissítés", use_container_width=True):
            adatok_betoltese.clear()
            hangeffekt("frissites")
            st.toast("Frissítve!", icon="🔄")
            time.sleep(0.4)
            st.rerun()

        szekcio_tipus = st.pills(
            "Típus",
            ["Összes", "➖ Kiadások", "➕ Bevételek", "💸 Tartozások", "🏦 Hitelek"],
            default="Összes",
            key="elozmenyek_tipus_szuro",
            label_visibility="collapsed",
        ) or "Összes"

        szurt_df = df.iloc[::-1].copy()
        if szekcio_tipus == "➖ Kiadások":
            szurt_df = szurt_df[(~szurt_df["Kategória"].str.startswith("Bevétel:", na=False)) & (~szurt_df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))]
        elif szekcio_tipus == "➕ Bevételek":
            szurt_df = szurt_df[szurt_df["Kategória"].str.startswith("Bevétel:", na=False)]
        elif szekcio_tipus == "💸 Tartozások":
            szurt_df = szurt_df[szurt_df["Kategória"] == "Tartozás"]
        elif szekcio_tipus == "🏦 Hitelek":
            szurt_df = szurt_df[szurt_df["Kategória"].isin(["Hitel: Keret", "Hitel: Törlesztés"])]

        if szekcio_tipus == "➖ Kiadások" and not szurt_df.empty:
            elerheto_kat = ["Minden kategória"] + sorted(szurt_df["Kategória"].unique().tolist())
            val_kat = st.pills(
                "Kategória",
                elerheto_kat,
                default="Minden kategória",
                key="elozmenyek_kat_szuro",
                label_visibility="collapsed",
            ) or "Minden kategória"
            if val_kat != "Minden kategória":
                szurt_df = szurt_df[szurt_df["Kategória"] == val_kat]

        kereso = st.text_input(
            "Keresés",
            placeholder="🔍 Keresés név, kategória, fizető vagy dátum alapján...",
            key="elozmenyek_kereso",
            label_visibility="collapsed",
        ).strip().lower()

        if kereso:
            maszk = (
                szurt_df["Megnevezés"].astype(str).str.lower().str.contains(kereso, na=False)
                | szurt_df["Kategória"].astype(str).str.lower().str.contains(kereso, na=False)
                | szurt_df["Ki"].astype(str).str.lower().str.contains(kereso, na=False)
                | szurt_df["Dátum"].astype(str).str.lower().str.contains(kereso, na=False)
            )
            szurt_df = szurt_df[maszk]

        talalat_db = len(szurt_df)
        talalat_osszeg = int(szurt_df["Összeg"].sum()) if not szurt_df.empty else 0
        st.markdown(
            f"""<div class="tx-summary-bar">
                <span>📋 <b>{talalat_db}</b> tétel megjelenítve</span>
                <span>Összesen: <b style="color:#f8fafc;">{fmt_ft(talalat_osszeg)} Ft</b></span>
            </div>""",
            unsafe_allow_html=True,
        )

        if szurt_df.empty:
            st.info("Nincs a szűrésnek megfelelő tétel.")
        else:
            max_elem = 30 if (kereso or szekcio_tipus != "Összes") else 20
            megerositendo_sor = st.session_state.get("torles_megerosites_sor")

            for _, r in szurt_df.head(max_elem).iterrows():
                sor_id = int(r["Sheet_Row"])
                kat_nyers = str(r["Kategória"])
                aktiv = (megerositendo_sor == sor_id)

                if kat_nyers.startswith("Bevétel:"):
                    card_cls, amt_cls, elojel = "tx-card tx-card-bev", "tx-amount tx-amt-bev", "+"
                    kat_cimke = kat_nyers.replace("Bevétel: ", "")
                elif kat_nyers.startswith("Hitel:"):
                    card_cls, amt_cls, elojel = "tx-card tx-card-hitel", "tx-amount tx-amt-hitel", ""
                    kat_cimke = kat_nyers.replace("Hitel: ", "Hitel • ")
                elif kat_nyers == "Tartozás":
                    card_cls, amt_cls, elojel = "tx-card tx-card-tart", "tx-amount tx-amt-tart", ""
                    kat_cimke = "Tartozás"
                else:
                    card_cls, amt_cls, elojel = "tx-card", "tx-amount tx-amt-ki", "−"
                    kat_cimke = kat_nyers

                if aktiv:
                    card_cls += " tx-card-del"

                nev_tiszta = str(r["Megnevezés"]).split("|")[0].strip()

                c_card, c_act = st.columns([5.2, 1.1], vertical_alignment="center")
                with c_card:
                    st.markdown(
                        f"""<div class="{card_cls}">
                            <div style="min-width:0;">
                                <div class="tx-title">{nev_tiszta}</div>
                                <div class="tx-meta">
                                    <span class="tx-pill">{kat_cimke}</span>
                                    <span>👤 {r['Ki']}</span>
                                    <span>• {r['Dátum']}</span>
                                </div>
                            </div>
                            <div class="{amt_cls}">{elojel}{fmt_ft(r['Összeg'])} Ft</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if not aktiv:
                        if st.button("🗑️", key=f"del_btn_{sor_id}", use_container_width=True, help="Tétel törlése"):
                            st.session_state["torles_megerosites_sor"] = sor_id
                            st.rerun()
                    else:
                        if st.button("✅", key=f"conf_del_{sor_id}", type="primary", use_container_width=True, help="Végleges törlés"):
                            with st.spinner("Törlés..."):
                                sheet.delete_rows(sor_id)
                            st.session_state["torles_megerosites_sor"] = None
                            adatok_betoltese.clear()
                            hangeffekt("torles")
                            st.toast("Tétel törölve!", icon="🗑️")
                            time.sleep(0.5)
                            st.rerun()
                        if st.button("✖️", key=f"canc_del_{sor_id}", use_container_width=True, help="Mégse"):
                            st.session_state["torles_megerosites_sor"] = None
                            st.rerun()

            if talalat_db > max_elem:
                st.caption(f"A legutóbbi {max_elem} tétel látható (összesen {talalat_db}). Használd a keresőt vagy a típus-szűrőt a régebbi tételekhez.")
