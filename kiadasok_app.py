import re
import time
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Közös pénzügyek 🍂", page_icon="🍂", layout="centered")

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
        height: 0.5rem !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
    }
    .block-container {
        padding-top: 1.1rem !important;
        padding-bottom: 2.5rem !important;
    }

    .top-nav-hero {
        background: linear-gradient(135deg, rgba(16, 28, 25, 0.86) 0%, rgba(24, 20, 15, 0.84) 100%);
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 20px;
        padding: 14px 18px;
        margin-bottom: 14px;
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
        font-size: 1.28rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .top-nav-sub {
        font-size: 0.78rem;
        color: #cbd5e1;
        margin-top: 2px;
    }
    .top-nav-badge {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(52, 211, 153, 0.42);
        border-radius: 999px;
        padding: 7px 14px;
        text-align: right;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.16);
    }
    .top-nav-badge-neg {
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(251, 191, 36, 0.45);
        border-radius: 999px;
        padding: 7px 14px;
        text-align: right;
    }
    .top-nav-badge-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        display: block;
    }
    .top-nav-badge-val {
        font-size: 0.98rem;
        font-weight: 700;
        color: #6ee7b7;
    }
    .top-nav-badge-neg .top-nav-badge-val {
        color: #fcd34d;
    }

    [data-testid="stTabs"] [role="tablist"] {
        background: rgba(11, 19, 17, 0.78) !important;
        border: 1px solid rgba(251, 191, 36, 0.22) !important;
        border-radius: 16px !important;
        padding: 5px !important;
        gap: 5px !important;
        backdrop-filter: blur(14px) !important;
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        border-radius: 12px !important;
        padding: 9px 4px !important;
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
        transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1) !important;
    }
    button:active { transform: scale(0.97) !important; }

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
        border-radius: 16px !important;
        padding: 13px 16px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
    }
    .kat-arany-sor {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
        margin-bottom: 3px;
        font-size: 0.92rem;
    }
    .kat-arany-szazalek {
        background: rgba(245, 158, 11, 0.22);
        border: 1px solid rgba(251, 191, 36, 0.45);
        color: #fcd34d;
        font-weight: 700;
        font-size: 0.80rem;
        padding: 2px 9px;
        border-radius: 999px;
        margin-left: 6px;
    }
    .torles-kartya {
        background: rgba(16, 26, 24, 0.72);
        border: 1px solid rgba(251, 191, 36, 0.22);
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 6px;
        backdrop-filter: blur(10px);
    }
    .torles-kartya-aktiv {
        background: rgba(127, 29, 29, 0.38);
        border: 1px solid rgba(248, 113, 113, 0.65);
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 6px;
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.25);
    }
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

def formazott_tabla(resz_df, kategoria_szoveg_csere=None):
    megj = resz_df.iloc[::-1].drop(columns=["Sheet_Row", "Ev_Honap"], errors="ignore").copy()
    if kategoria_szoveg_csere:
        megj["Kategória"] = megj["Kategória"].str.replace(kategoria_szoveg_csere, "", regex=False)
    megj["Összeg"] = megj["Összeg"].apply(lambda x: f"{fmt_ft(x)} Ft")
    return megj

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
        <div class="{badge_osztaly}">
            <span class="top-nav-badge-label">Kassza egyenleg</span>
            <span class="top-nav-badge-val">{fmt_ft(aktualis_egyenleg)} Ft</span>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

tab_uj, tab_stat, tab_hitel, tab_lista = st.tabs(["🍁 Új tétel", "📊 Statisztika", "🏦 Hitel", "📜 Előzmények"])

with tab_uj:
    tipus = st.radio("Művelet típusa", ["➖ Kiadás", "➕ Bevétel"], horizontal=True)

    if tipus == "➕ Bevétel":
        kategoria_valasztott = st.pills(
            "Bevétel típusa",
            ["Közös kasszába befizetés", "Ajándék / Támogatás", "Eladás / Visszatérítés", "Egyéb bevétel"],
            default="Közös kasszába befizetés",
        ) or "Közös kasszába befizetés"
        kategoria = f"Bevétel: {kategoria_valasztott}"
        ki = st.text_input("Kitől kaptuk / Ki tette bele?", placeholder="pl. Zsolt, Vivien, Szülők").strip()
        megnevezes = st.text_input("Megnevezés (pl. Havi keret, Visszatérítés)")
    else:
        kategoria = st.pills(
            "Kategória",
            ["Élelmiszer & Háztartás", "Dohánybolt", "Ajándékozás", "Előfizetés", "Tartozás", "Üzemanyag & Autó", "Lakhatás & Rezsi", "Étterem & Randi", "Tech & Vásárlás", "Egyéb"],
            default="Élelmiszer & Háztartás",
        ) or "Élelmiszer & Háztartás"
        if kategoria == "Tartozás":
            st.info("💸 **Tartozás rögzítése**")
            c1, c2 = st.columns(2)
            ki_tartozik = c1.text_input("Ki tartozik?", placeholder="pl. Zsolt").strip()
            kinek_tartozik = c2.text_input("Kinek tartozik?", placeholder="pl. Vivien").strip()
            ki = ki_tartozik
        else:
            ki = st.radio("Ki fizette?", ["Zsolt", "Vivien"], horizontal=True)

        placeholder_szoveg = {
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
            opciok_map["OSSZES"] = "♾️ Összesített (minden hónap)"
            valasztott_idoszak = st.pills(
                "Időszak kiválasztása",
                options=list(opciok_map.keys()),
                format_func=lambda x: opciok_map[x],
                default=elerheto_honapok[0],
                key="stat_idoszak_valaszto",
            ) or elerheto_honapok[0]
            stat_df = df if valasztott_idoszak == "OSSZES" else df[df["Ev_Honap"] == valasztott_idoszak].copy()
            if valasztott_idoszak != "OSSZES":
                st.caption(f"🔎 Kiválasztott hónap: **{honap_cimke(valasztott_idoszak)}**")
        else:
            stat_df = df.copy()

        bevetelek = stat_df[stat_df["Kategória"].str.startswith("Bevétel:", na=False)].copy()
        tartozasok = stat_df[stat_df["Kategória"] == "Tartozás"].copy()
        kiadasok = stat_df[(~stat_df["Kategória"].str.startswith("Bevétel:", na=False)) & (~stat_df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))].copy()

        ossz_bevetel = bevetelek["Összeg"].sum() if not bevetelek.empty else 0
        ossz_kiadas = kiadasok["Összeg"].sum() if not kiadasok.empty else 0
        egyenleg = ossz_bevetel - ossz_kiadas

        egyenleg_cimke = "💵 Havi egyenleg" if (len(elerheto_honapok) > 1 and valasztott_idoszak != "OSSZES") else "💵 Jelenleg felhasználható egyenleg"
        st.metric(egyenleg_cimke, f"{fmt_ft(egyenleg)} Ft")
        m1, m2 = st.columns(2)
        m1.metric("➕ Bevétel", f"{fmt_ft(ossz_bevetel)} Ft")
        m2.metric("➖ Kiadás", f"{fmt_ft(ossz_kiadas)} Ft")

        if not bevetelek.empty:
            st.divider()
            st.subheader("📥 Bevételek forrása (mennyit adtatok bele)")
            for _, sor in bevetelek.groupby("Ki", as_index=False)["Összeg"].sum().iterrows():
                st.metric(f"{sor['Ki']}", f"{fmt_ft(sor['Összeg'])} Ft")
            bevetelek["Típus"] = bevetelek["Kategória"].str.replace("Bevétel: ", "", regex=False)
            fig_bev = px.pie(
                bevetelek.groupby("Típus", as_index=False)["Összeg"].sum(),
                values="Összeg",
                names="Típus",
                hole=0.45,
                title="Bevételek megoszlása",
                color_discrete_sequence=["#f59e0b", "#10b981", "#d97706", "#0ea5e9"],
            )
            fig_bev.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
            st.plotly_chart(fig_bev, use_container_width=True)

        if not kiadasok.empty:
            st.divider()
            st.subheader("📤 Kiadások bontása és kategória arányok")
            c1, c2 = st.columns(2)
            c1.metric("Zsolt költötte", f"{fmt_ft(kiadasok[kiadasok['Ki'] == 'Zsolt']['Összeg'].sum())} Ft")
            c2.metric("Vivien költötte", f"{fmt_ft(kiadasok[kiadasok['Ki'] == 'Vivien']['Összeg'].sum())} Ft")

            kat_osszesites = (
                kiadasok.groupby("Kategória", as_index=False)
                .agg(Összeg=("Összeg", "sum"), Darab=("Összeg", "count"))
                .sort_values("Összeg", ascending=False)
            )
            kat_osszesites["Arány"] = (kat_osszesites["Összeg"] / ossz_kiadas * 100) if ossz_kiadas > 0 else 0.0

            fig_ki = px.pie(
                kat_osszesites,
                values="Összeg",
                names="Kategória",
                hole=0.45,
                title="Kiadások megoszlása",
                color_discrete_sequence=["#f59e0b", "#10b981", "#ea580c", "#0d9488", "#eab308", "#e11d48", "#3b82f6", "#a855f7", "#14b8a6"],
            )
            fig_ki.update_traces(textposition="inside", textinfo="percent+label")
            fig_ki.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
            st.plotly_chart(fig_ki, use_container_width=True)

            st.markdown("#### 📊 Kategóriák pontos aránya")
            for _, k_sor in kat_osszesites.iterrows():
                arany_szazalek = float(k_sor["Arány"])
                arany_szoveg = f"{arany_szazalek:.1f}".replace(".", ",")
                st.markdown(
                    f"""<div class="kat-arany-sor">
                        <div><b>{k_sor['Kategória']}</b> <span class="kat-arany-szazalek">{arany_szoveg}%</span></div>
                        <div style="color:#cbd5e1; font-size:0.86rem;"><b>{fmt_ft(k_sor['Összeg'])} Ft</b> <span style="color:#94a3b8;">({int(k_sor['Darab'])} tétel)</span></div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.progress(min(1.0, max(0.0, arany_szazalek / 100.0)))

        if not tartozasok.empty:
            st.divider()
            st.subheader("💸 Rögzített tartozások")
            tartozasok["Irány"] = tartozasok["Megnevezés"].str.extract(r"\(([^)]+→[^)]+)\)")[0].fillna(tartozasok["Ki"])
            for _, sor in tartozasok.groupby("Irány", as_index=False)["Összeg"].sum().iterrows():
                st.metric(sor["Irány"], f"{fmt_ft(sor['Összeg'])} Ft")

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
        st.info("Üres a lista.")
    else:
        bevetel_elozmenyek = df[df["Kategória"].str.startswith("Bevétel:", na=False)].copy()
        tartozas_elozmenyek = df[df["Kategória"] == "Tartozás"].copy()
        hitel_elozmenyek = df[df["Kategória"].isin(["Hitel: Keret", "Hitel: Törlesztés"])].copy()
        kiadas_elozmenyek = df[(~df["Kategória"].str.startswith("Bevétel:", na=False)) & (~df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))].copy()

        st.subheader("➖ Kiadások")
        if kiadas_elozmenyek.empty:
            st.caption("Nincs rögzített kiadás.")
        else:
            elerheto_kategoriak = ["Összes"] + sorted(kiadas_elozmenyek["Kategória"].unique().tolist())
            valasztott_kat = st.pills(
                "Kategória szűrő",
                elerheto_kategoriak,
                default="Összes",
                key="elozmenyek_kat_szuro",
            ) or "Összes"
            szurt_kiadas = kiadas_elozmenyek if valasztott_kat == "Összes" else kiadas_elozmenyek[kiadas_elozmenyek["Kategória"] == valasztott_kat]
            st.dataframe(formazott_tabla(szurt_kiadas), use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("➕ Bevételek")
        if bevetel_elozmenyek.empty:
            st.caption("Nincs rögzített bevétel.")
        else:
            st.dataframe(formazott_tabla(bevetel_elozmenyek, "Bevétel: "), use_container_width=True, hide_index=True)

        st.divider()

        if not tartozas_elozmenyek.empty:
            st.subheader("💸 Tartozások")
            st.dataframe(formazott_tabla(tartozas_elozmenyek), use_container_width=True, hide_index=True)
            st.divider()

        st.subheader("🏦 Hitelek és törlesztések")
        if hitel_elozmenyek.empty:
            st.caption("Nincs rögzített hitel vagy törlesztés.")
        else:
            hitel_elozmenyek["Kategória"] = hitel_elozmenyek["Kategória"].str.replace("Hitel: ", "", regex=False)
            st.dataframe(formazott_tabla(hitel_elozmenyek), use_container_width=True, hide_index=True)

        st.divider()

        if st.button("🔄 Frissítés a felhőből", use_container_width=True):
            adatok_betoltese.clear()
            hangeffekt("frissites")
            st.toast("Frissítve!", icon="🔄")
            time.sleep(0.4)
            st.rerun()

        st.divider()

        st.subheader("🗑️ Tételek kezelése és törlése")
        kereso = st.text_input("🔍 Gyorskereső (név, kategória vagy dátum)", placeholder="pl. Lidl, Zsolt, Hitel...", key="torles_kereso").strip().lower()
        forditott = df.iloc[::-1]
        if kereso:
            maszk = (
                forditott["Megnevezés"].astype(str).str.lower().str.contains(kereso, na=False)
                | forditott["Kategória"].astype(str).str.lower().str.contains(kereso, na=False)
                | forditott["Ki"].astype(str).str.lower().str.contains(kereso, na=False)
                | forditott["Dátum"].astype(str).str.lower().str.contains(kereso, na=False)
            )
            forditott = forditott[maszk]

        megerositendo_sor = st.session_state.get("torles_megerosites_sor")

        for _, r in forditott.head(15).iterrows():
            sor_id = int(r["Sheet_Row"])
            aktiv = (megerositendo_sor == sor_id)
            kartya_osztaly = "torles-kartya-aktiv" if aktiv else "torles-kartya"
            kat_tiszta = str(r["Kategória"]).replace("Bevétel: ", "")
            nev_tiszta = str(r["Megnevezés"]).split("|")[0].strip()

            k_col1, k_col2 = st.columns([4, 1.4], vertical_alignment="center")
            with k_col1:
                st.markdown(
                    f"""<div class="{kartya_osztaly}">
                        <div style="font-size:0.78rem; color:#cbd5e1;">📅 {r['Dátum']} • <b>{r['Ki']}</b> • {kat_tiszta}</div>
                        <div style="font-size:1.0rem; font-weight:600; color:#f8fafc; margin-top:2px;">{nev_tiszta} — <span style="color:#fbbf24;">{fmt_ft(r['Összeg'])} Ft</span></div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with k_col2:
                if not aktiv:
                    if st.button("🗑️", key=f"del_btn_{sor_id}", use_container_width=True, help="Tétel törlése"):
                        st.session_state["torles_megerosites_sor"] = sor_id
                        st.rerun()
                else:
                    if st.button("✅ Biztos?", key=f"conf_del_{sor_id}", type="primary", use_container_width=True):
                        with st.spinner("Törlés..."):
                            sheet.delete_rows(sor_id)
                        st.session_state["torles_megerosites_sor"] = None
                        adatok_betoltese.clear()
                        hangeffekt("torles")
                        st.toast("Tétel véglegesen törölve!", icon="🗑️")
                        time.sleep(0.6)
                        st.rerun()
                    if st.button("✖️ Mégse", key=f"canc_del_{sor_id}", use_container_width=True):
                        st.session_state["torles_megerosites_sor"] = None
                        st.rerun()

        if len(forditott) > 15:
            st.caption(f"A legutóbbi 15 tétel látható. Használd a fenti gyorskeresőt a régebbi tételek megtalálásához (összesen {len(forditott)} találat).")
