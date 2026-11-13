import time
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# Mobilbarát oldalbeállítás
st.set_page_config(page_title="Közös Kiadások", page_icon="💑", layout="centered")

# Lehúzós oldalfrissítés (Pull-to-Refresh) tiltása mobilon
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .main {
        overscroll-behavior-y: contain !important;
        overscroll-behavior: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Beépített kellemes csilingelő hangeffekt (külső fájl nélkül)
def siker_hang():
    components.html(
        """
        <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            
            // 1. hang (C5)
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(523.25, now);
            gain1.gain.setValueAtTime(0.25, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            osc1.start(now);
            osc1.stop(now + 0.35);

            // 2. hang (G5 - magasabb csilingelés)
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(783.99, now + 0.12);
            gain2.gain.setValueAtTime(0.25, now + 0.12);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            osc2.start(now + 0.12);
            osc2.stop(now + 0.6);
        } catch (e) {}
        </script>
        """,
        height=0,
    )

st.title("💑 Közös Kiadáskövető")

# --- CSATLAKOZÁS A GOOGLE TÁBLÁZATHOZ ---
@st.cache_resource
def csatlakozas_sheetshez():
    hatokorok = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=hatokorok
            )
        else:
            creds = Credentials.from_service_account_file("kulcs.json", scopes=hatokorok)
    except Exception:
        creds = Credentials.from_service_account_file("kulcs.json", scopes=hatokorok)
    
    client = gspread.authorize(creds)
    return client.open("Kozos_Kiadasok").sheet1

try:
    sheet = csatlakozas_sheetshez()
except Exception as e:
    st.error(f"Nem sikerült csatlakozni a Google Táblázathoz! Ellenőrizd a Secrets beállítást és a megosztást.\nRészletek: {e}")
    st.stop()

# Adatok beolvasása a táblázatból (pontos Google Sheets sorszámmal együtt)
def adatok_betoltese():
    rekordok = sheet.get_all_records()
    if not rekordok:
        return pd.DataFrame(columns=["Sheet_Row", "Dátum", "Ki", "Kategória", "Megnevezés", "Összeg"])
    df = pd.DataFrame(rekordok)
    # A Google Sheets 1. sora a fejléc, az első adat a 2. sorban van
    df["Sheet_Row"] = range(2, len(df) + 2)
    df["Összeg"] = pd.to_numeric(df["Összeg"], errors="coerce").fillna(0).astype(int)
    return df

df = adatok_betoltese()

# --- 3 FÜL A TELEFONOS KÉNYELEMÉRT ---
tab_uj, tab_stat, tab_lista = st.tabs(["➕ Új tétel", "📊 Statisztika", "📝 Előzmények"])

# 1. FÜL: ÚJ KIADÁS RÖGZÍTÉSE
with tab_uj:
    with st.form("uj_kiadas_form", clear_on_submit=True):
        ki = st.radio("Ki fizette?", ["Zsolt", "Vivien"], horizontal=True)
        kategoria = st.selectbox(
            "Kategória",
            [
                "Élelmiszer & Háztartás",
                "Üzemanyag & Autó",
                "Lakhatás & Rezsi",
                "Étterem & Randi",
                "Tech & Vásárlás",
                "Egyéb",
            ],
        )
        megnevezes = st.text_input("Mit vettetek? (pl. Lidl, Tankolás)")
        osszeg = st.number_input("Összeg (Ft)", min_value=0, step=500)
        datum = st.date_input("Dátum", value=date.today())

        kuldes = st.form_submit_button("💾 Rögzítés a felhőbe", use_container_width=True, type="primary")

        if kuldes:
            if not megnevezes or osszeg <= 0:
                st.toast("⚠️ Írd be a megnevezést és az összeget!", icon="⚠️")
                st.warning("Írd be a megnevezést és egy 0-nál nagyobb összeget!")
            else:
                with st.spinner("Mentés a Google Táblázatba..."):
                    uj_sor = [str(datum), ki, kategoria, megnevezes, int(osszeg)]
                    sheet.append_row(uj_sor)
                
                # Hangeffekt + animált visszacsatolás
                siker_hang()
                st.balloons()
                st.toast(f"Sikeresen mentve: {megnevezes}!", icon="✅")
                st.success(f"Rögzítve: {megnevezes} ({osszeg:,} Ft)".replace(",", " "))
                time.sleep(1.5)
                st.rerun()

# 2. FÜL: KÖZÖS STATISZTIKA ÉS GRAFIKON
with tab_stat:
    if df.empty:
        st.info("Még nincs rögzített tétel a táblázatban.")
    else:
        osszes = df["Összeg"].sum()
        zsolt_ossz = df[df["Ki"] == "Zsolt"]["Összeg"].sum()
        vivien_ossz = df[df["Ki"] == "Vivien"]["Összeg"].sum()

        st.metric("Összes közös kiadás", f"{osszes:,.0f} Ft".replace(",", " "))
        
        col1, col2 = st.columns(2)
        col1.metric("Zsolt", f"{zsolt_ossz:,.0f} Ft".replace(",", " "))
        col2.metric("Vivien", f"{vivien_ossz:,.0f} Ft".replace(",", " "))

        st.divider()

        # Kördiagram kategóriánként
        kat
