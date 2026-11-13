import time
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Közös pénzügyek 🍂", page_icon="🍂", layout="centered")

st.markdown(
    """<style>
    :root { color-scheme: dark !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior-y: contain !important;
        touch-action: pan-y !important;
        color: #f5f5f4 !important;
        scroll-behavior: smooth !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0c0a09 !important;
        background-image:
            radial-gradient(circle at 18% 14%, rgba(217, 119, 6, 0.26) 0%, transparent 46%),
            radial-gradient(circle at 84% 24%, rgba(154, 52, 18, 0.28) 0%, transparent 48%),
            radial-gradient(circle at 50% 88%, rgba(71, 85, 105, 0.26) 0%, transparent 55%),
            linear-gradient(160deg, #0f0d0c 0%, #1c1512 52%, #11161d 100%) !important;
        background-attachment: fixed !important;
    }
    /* Késő őszi köd és lágyan szitáló novemberi eső + hulló levelek */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image:
            linear-gradient(172deg, transparent 45%, rgba(203, 213, 225, 0.14) 50%, transparent 55%),
            linear-gradient(172deg, transparent 45%, rgba(217, 119, 6, 0.16) 50%, transparent 55%),
            radial-gradient(3px 2px at 45px 60px, rgba(217, 119, 6, 0.55) 50%, transparent 100%),
            radial-gradient(3.5px 2px at 175px 130px, rgba(180, 83, 9, 0.50) 50%, transparent 100%);
        background-size: 130px 180px, 190px 240px, 260px 260px, 310px 310px;
        animation: novemberRain 3.2s linear infinite;
    }
    @keyframes novemberRain {
        0% { background-position: 0px 0px, 0px 0px, 0px 0px, 0px 0px; }
        100% { background-position: -18px 180px, -24px 240px, 30px 260px, -25px 310px; }
    }
    [data-testid="stHeader"] { background: transparent !important; }

    /* Fluid átmenetek minden interaktív elemen */
    button, input, [data-testid="stMetric"], [data-baseweb="tab"] {
        transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1) !important;
    }
    button:active { transform: scale(0.98) !important; }

    /* Novemberi borostyán-gesztenye kategória gombok (st.pills) */
    [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stPills"] button span {
        background: rgba(28, 22, 19, 0.85) !important;
        color: #e7e5e4 !important;
        border-color: rgba(217, 119, 6, 0.32) !important;
        border-radius: 999px !important;
    }
    [data-testid="stPills"] button[aria-pressed="true"],
    [data-testid="stPills"] button[aria-pressed="true"] p,
    [data-testid="stPills"] button[aria-pressed="true"] span {
        background: linear-gradient(135deg, rgba(180, 83, 9, 0.78), rgba(120, 53, 15, 0.85)) !important;
        border-color: #f59e0b !important;
        color: #fffbeb !important;
        box-shadow: 0 0 14px rgba(217, 119, 6, 0.35) !important;
    }

    /* Meleg üveghatású kártyák */
    [data-testid="stMetric"] {
        background: rgba(24, 19, 17, 0.70) !important;
        border: 1px solid rgba(217, 119, 6, 0.28) !important;
        border-radius: 16px !important;
        padding: 13px 16px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28) !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"] {
        max-height: 55vh !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: pan-y !important;
        background-color: #1c1917 !important;
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
                // Meleg őszi zongora-szerű akkord (F4 -> A4 -> C5 -> E5)
                p(349.23, now, 0.45, 'sine', 0.18);
                p(440.00, now+0.09, 0.45, 'sine', 0.18);
                p(523.25, now+0.18, 0.50, 'sine', 0.20);
                p(659.25, now+0.27, 0.65, 'sine', 0.22);
            }}
            else if (t==="torles") {{
                // Lágy őszi szél / lehulló levél hang (D4 -> A3)
                p(293.66, now, 0.28, 'sine', 0.18);
                p(220.00, now+0.13, 0.42, 'sine', 0.18);
            }}
            else if (t==="frissites") {{
                // Tiszta esőcsepp koppanás (E5 -> B5)
                p(659.25, now, 0.12, 'sine', 0.15);
                p(987.77, now+0.08, 0.22, 'sine', 0.16);
            }}
            else if (t==="hiba") {{
                // Tompa fa koppanás (G3)
                p(196.00, now, 0.15, 'triangle', 0.20);
                p(196.00, now+0.17, 0.20, 'triangle', 0.20);
            }}
        }} catch (e) {{}}</script>""",
        height=0,
    )

st.title("🍂 Közös pénzügyek 🌧️")

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

# Gyorsítótárazott adatbetöltés a villámgyors, akadásmentes felületért
@st.cache_data(ttl=60, show_spinner=False)
def adatok_betoltese():
    rekordok = sheet.get_all_records()
    if not rekordok:
        return pd.DataFrame(columns=["Sheet_Row", "Dátum", "Ki", "Kategória", "Megnevezés", "Összeg"])
    df = pd.DataFrame(rekordok)
    df["Sheet_Row"] = range(2, len(df) + 2)
    df["Összeg"] = pd.to_numeric(df["Összeg"], errors="coerce").fillna(0).astype(int)
    return df

df = adatok_betoltese()
tab_uj, tab_stat, tab_lista = st.tabs(["🍁 Új tétel", "📊 Statisztika", "📜 Előzmények"])

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
            ["Élelmiszer & Háztartás", "Előfizetés", "Tartozás", "Üzemanyag & Autó", "Lakhatás & Rezsi", "Étterem & Randi", "Tech & Vásárlás", "Egyéb"],
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
        megnevezes = st.text_input(
            "Mire vonatkozik?" if kategoria == "Tartozás"
            else ("Melyik előfizetés? (pl. Netflix, Apple Music, Internet)" if kategoria == "Előfizetés"
            else "Mit vettetek? (pl. Lidl, Kávézó)")
        )

    osszeg = st.number_input("Összeg (Ft)", min_value=0, step=500)
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
            adatok_betoltese.clear()
            hangeffekt("siker")
            st.toast(f"Mentve: {vegleges_nev}!", icon="🍂")
            time.sleep(0.9)
            st.rerun()

with tab_stat:
    if df.empty:
        st.info("Még nincs rögzített tétel.")
    else:
        bevetelek = df[df["Kategória"].str.startswith("Bevétel:", na=False)].copy()
        tartozasok = df[df["Kategória"] == "Tartozás"].copy()
        kiadasok = df[(~df["Kategória"].str.startswith("Bevétel:", na=False)) & (df["Kategória"] != "Tartozás")].copy()

        ossz_bevetel = bevetelek["Összeg"].sum() if not bevetelek.empty else 0
        ossz_kiadas = kiadasok["Összeg"].sum() if not kiadasok.empty else 0
        egyenleg = ossz_bevetel - ossz_kiadas

        st.metric("💵 Jelenleg felhasználható egyenleg", f"{egyenleg:,.0f} Ft".replace(",", " "))
        m1, m2 = st.columns(2)
        m1.metric("➕ Összes bevétel", f"{ossz_bevetel:,.0f} Ft".replace(",", " "))
        m2.metric("➖ Összes kiadás", f"{ossz_kiadas:,.0f} Ft".replace(",", " "))

        if not bevetelek.empty:
            st.divider()
            st.subheader("📥 Bevételek forrása (mennyit adtatok bele)")
            for _, sor in bevetelek.groupby("Ki", as_index=False)["Összeg"].sum().iterrows():
                st.metric(f"{sor['Ki']}", f"{sor['Összeg']:,.0f} Ft".replace(",", " "))
            bevetelek["Típus"] = bevetelek["Kategória"].str.replace("Bevétel: ", "", regex=False)
            fig_bev = px.pie(
                bevetelek.groupby("Típus", as_index=False)["Összeg"].sum(),
                values="Összeg",
                names="Típus",
                hole=0.45,
                title="Bevételek megoszlása",
                color_discrete_sequence=["#d97706", "#b45309", "#65a30d", "#0284c7"],
            )
            fig_bev.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f5f5f4")
            st.plotly_chart(fig_bev, use_container_width=True)

        if not kiadasok.empty:
            st.divider()
            st.subheader("📤 Kiadások bontása")
            c1, c2 = st.columns(2)
            c1.metric("Zsolt költötte", f"{kiadasok[kiadasok['Ki'] == 'Zsolt']['Összeg'].sum():,.0f} Ft".replace(",", " "))
            c2.metric("Vivien költötte", f"{kiadasok[kiadasok['Ki'] == 'Vivien']['Összeg'].sum():,.0f} Ft".replace(",", " "))
            fig_ki = px.pie(
                kiadasok.groupby("Kategória", as_index=False)["Összeg"].sum(),
                values="Összeg",
                names="Kategória",
                hole=0.45,
                title="Kiadások megoszlása",
                color_discrete_sequence=["#d97706", "#9a3412", "#ca8a04", "#4d7c0f", "#475569", "#b91c1c", "#0f766e"],
            )
            fig_ki.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f5f5f4")
            st.plotly_chart(fig_ki, use_container_width=True)

        if not tartozasok.empty:
            st.divider()
            st.subheader("💸 Rögzített tartozások")
            tartozasok["Irány"] = tartozasok["Megnevezés"].str.extract(r"\(([^)]+→[^)]+)\)")[0].fillna(tartozasok["Ki"])
            for _, sor in tartozasok.groupby("Irány", as_index=False)["Összeg"].sum().iterrows():
                st.metric(sor["Irány"], f"{sor['Összeg']:,.0f} Ft".replace(",", " "))

with tab_lista:
    if df.empty:
        st.info("Üres a lista.")
    else:
        st.dataframe(df.iloc[::-1].drop(columns=["Sheet_Row"]), use_container_width=True, hide_index=True)
        if st.button("🌧️ Frissítés a felhőből", use_container_width=True):
            adatok_betoltese.clear()
            hangeffekt("frissites")
            st.toast("Frissítve!", icon="🌧️")
            time.sleep(0.4)
            st.rerun()
        st.divider()
        with st.expander("🗑️ Tétel törlése"):
            forditott = df.iloc[::-1]
            opciok = {r["Sheet_Row"]: f"{r['Dátum']} | {r['Ki']} – {r['Megnevezés']} ({r['Összeg']:,} Ft)".replace(",", " ") for _, r in forditott.iterrows()}
            valasztott = st.selectbox("Törlendő tétel:", options=list(opciok.keys()), format_func=lambda x: opciok[x])
            if st.button("🗑️ Kiválasztott tétel végleges törlése", type="primary", use_container_width=True):
                with st.spinner("Törlés..."):
                    sheet.delete_rows(int(valasztott))
                adatok_betoltese.clear()
                hangeffekt("torles")
                st.toast("Tétel törölve!", icon="🗑️")
                time.sleep(0.7)
                st.rerun()
