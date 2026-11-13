import time
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Közös pénzügyek", page_icon="💰", layout="centered")

st.markdown(
    """<style>
    :root { color-scheme: dark !important; }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior-y: contain !important;
        touch-action: pan-y !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #070b14 !important;
        background-image:
            radial-gradient(circle at 15% 18%, rgba(16, 185, 129, 0.22) 0%, transparent 45%),
            radial-gradient(circle at 85% 25%, rgba(99, 102, 241, 0.24) 0%, transparent 48%),
            radial-gradient(circle at 50% 88%, rgba(14, 165, 233, 0.20) 0%, transparent 52%),
            linear-gradient(145deg, #060913 0%, #0d1528 50%, #08121e 100%) !important;
        background-attachment: fixed !important;
        animation: ambientPulse 14s ease-in-out infinite alternate;
    }
    @keyframes ambientPulse {
        0% { background-position: 0% 0%; filter: brightness(0.96); }
        100% { background-position: 100% 100%; filter: brightness(1.06); }
    }
    [data-testid="stHeader"] { background: transparent !important; }

    /* Kategória gombok (st.pills) */
    [data-testid="stPills"] button, [data-testid="stPills"] button p, [data-testid="stPills"] button span {
        background: rgba(15, 23, 42, 0.85) !important;
        color: #f1f5f9 !important;
        border-color: rgba(148, 163, 184, 0.35) !important;
    }
    [data-testid="stPills"] button[aria-pressed="true"],
    [data-testid="stPills"] button[aria-pressed="true"] p,
    [data-testid="stPills"] button[aria-pressed="true"] span {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.45), rgba(59, 130, 246, 0.45)) !important;
        border-color: #34d399 !important;
        color: #ffffff !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        padding: 12px 16px !important;
        backdrop-filter: blur(10px) !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"] {
        max-height: 55vh !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        touch-action: pan-y !important;
        background-color: #0f172a !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

def hangeffekt(tipus="siker"):
    components.html(
        f"""<script>try {{
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime, t = "{tipus}";
            function p(f, s, d, y='sine', v=0.22) {{
                const o = ctx.createOscillator(), g = ctx.createGain();
                o.type = y; o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(v, s); g.gain.exponentialRampToValueAtTime(0.001, s + d);
                o.connect(g); g.connect(ctx.destination); o.start(s); o.stop(s + d);
            }}
            if (t==="siker") {{ p(523.25, now, 0.35, 'sine', 0.25); p(783.99, now+0.12, 0.55, 'sine', 0.25); }}
            else if (t==="torles") {{ p(329.63, now, 0.25); p(220.00, now+0.14, 0.40); }}
            else if (t==="frissites") {{ p(880.00, now, 0.18, 'sine', 0.18); }}
            else if (t==="hiba") {{ p(174.61, now, 0.16, 'triangle'); p(174.61, now+0.18, 0.22, 'triangle'); }}
        }} catch (e) {{}}</script>""",
        height=0,
    )

st.title("💰 Közös pénzügyek")

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

def adatok_betoltese():
    rekordok = sheet.get_all_records()
    if not rekordok:
        return pd.DataFrame(columns=["Sheet_Row", "Dátum", "Ki", "Kategória", "Megnevezés", "Összeg"])
    df = pd.DataFrame(rekordok)
    df["Sheet_Row"] = range(2, len(df) + 2)
    df["Összeg"] = pd.to_numeric(df["Összeg"], errors="coerce").fillna(0).astype(int)
    return df

df = adatok_betoltese()
tab_uj, tab_stat, tab_lista = st.tabs(["➕ Új tétel", "📊 Statisztika", "📝 Előzmények"])

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
        megnevezes = st.text_input("Megnevezés (pl. Havi keret, Szülinap)")
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
            else "Mit vettetek? (pl. Lidl)")
        )

    osszeg = st.number_input("Összeg (Ft)", min_value=0, step=500)
    datum = st.date_input("Dátum", value=date.today())

    if st.button("💾 Rögzítés a felhőbe", use_container_width=True, type="primary"):
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
            hangeffekt("siker")
            st.balloons()
            st.toast(f"Mentve: {vegleges_nev}!", icon="✅")
            time.sleep(1.5)
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
            fig_bev = px.pie(bevetelek.groupby("Típus", as_index=False)["Összeg"].sum(), values="Összeg", names="Típus", hole=0.45, title="Bevételek megoszlása")
            fig_bev.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
            st.plotly_chart(fig_bev, use_container_width=True)

        if not kiadasok.empty:
            st.divider()
            st.subheader("📤 Kiadások bontása")
            c1, c2 = st.columns(2)
            c1.metric("Zsolt költötte", f"{kiadasok[kiadasok['Ki'] == 'Zsolt']['Összeg'].sum():,.0f} Ft".replace(",", " "))
            c2.metric("Vivien költötte", f"{kiadasok[kiadasok['Ki'] == 'Vivien']['Összeg'].sum():,.0f} Ft".replace(",", " "))
            fig_ki = px.pie(kiadasok.groupby("Kategória", as_index=False)["Összeg"].sum(), values="Összeg", names="Kategória", hole=0.45, title="Kiadások megoszlása")
            fig_ki.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f1f5f9")
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
        if st.button("🔄 Frissítés a felhőből", use_container_width=True):
            hangeffekt("frissites")
            st.toast("Frissítve!", icon="🔄")
            time.sleep(0.5)
            st.rerun()
        st.divider()
        with st.expander("🗑️ Tétel törlése"):
            forditott = df.iloc[::-1]
            opciok = {r["Sheet_Row"]: f"{r['Dátum']} | {r['Ki']} – {r['Megnevezés']} ({r['Összeg']:,} Ft)".replace(",", " ") for _, r in forditott.iterrows()}
            valasztott = st.selectbox("Törlendő tétel:", options=list(opciok.keys()), format_func=lambda x: opciok[x])
            if st.button("🗑️ Kiválasztott tétel végleges törlése", type="primary", use_container_width=True):
                with st.spinner("Törlés..."):
                    sheet.delete_rows(int(valasztott))
                hangeffekt("torles")
                st.toast("Tétel törölve!", icon="🗑️")
                time.sleep(1.0)
                st.rerun()
