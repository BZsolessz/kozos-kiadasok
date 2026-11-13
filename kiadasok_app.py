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

# Letisztult hangeffektek minden művelethez (külső fájl nélkül)
def hangeffekt(tipus="siker"):
    components.html(
        f"""
        <script>
        try {{
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const now = ctx.currentTime;
            const tipus = "{tipus}";

            function playTone(freq, start, duration, type = 'sine', vol = 0.22) {{
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = type;
                osc.frequency.setValueAtTime(freq, start);
                gain.gain.setValueAtTime(vol, start);
                gain.gain.exponentialRampToValueAtTime(0.001, start + duration);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(start);
                osc.stop(start + duration);
            }}

            if (tipus === "siker") {{
                // Felfelé ívelő kettős csilingelés (C5 -> G5)
                playTone(523.25, now, 0.35, 'sine', 0.25);
                playTone(783.99, now + 0.12, 0.55, 'sine', 0.25);
            }} else if (tipus === "torles") {{
                // Lágy lefelé lépő dupla hang (E4 -> A3)
                playTone(329.63, now, 0.25, 'sine', 0.22);
                playTone(220.00, now + 0.14, 0.40, 'sine', 0.22);
            }} else if (tipus === "frissites") {{
                // Rövid, tiszta vízcsepp/pop hang (A5)
                playTone(880.00, now, 0.18, 'sine', 0.18);
            }} else if (tipus === "hiba") {{
                // Tompa figyelmeztető dupla jelzés (F3)
                playTone(174.61, now, 0.16, 'triangle', 0.22);
                playTone(174.61, now + 0.18, 0.22, 'triangle', 0.22);
            }}
        }} catch (e) {{}}
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
                hangeffekt("hiba")
                st.toast("⚠️ Írd be a megnevezést és az összeget!", icon="⚠️")
                st.warning("Írd be a megnevezést és egy 0-nál nagyobb összeget!")
            else:
                with st.spinner("Mentés a Google Táblázatba..."):
                    uj_sor = [str(datum), ki, kategoria, megnevezes, int(osszeg)]
                    sheet.append_row(uj_sor)
                
                hangeffekt("siker")
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
        kat_df = df.groupby("Kategória", as_index=False)["Összeg"].sum()
        fig = px.pie(kat_df, values="Összeg", names="Kategória", hole=0.45, title="Kiadások megoszlása")
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

# 3. FÜL: ELŐZMÉNYEK, TÖRLÉS ÉS FRISSÍTÉS
with tab_lista:
    if df.empty:
        st.info("Üres a lista.")
    else:
        megjelenitendo_df = df.iloc[::-1].drop(columns=["Sheet_Row"])
        st.dataframe(megjelenitendo_df, use_container_width=True, hide_index=True)

        if st.button("🔄 Frissítés a felhőből", use_container_width=True):
            hangeffekt("frissites")
            st.toast("Adatok frissítve!", icon="🔄")
            time.sleep(0.5)
            st.rerun()

        st.divider()

        # Tétel törlése lenyíló listából
        with st.expander("🗑️ Tétel törlése"):
            forditott_df = df.iloc[::-1]
            opciok = {
                row["Sheet_Row"]: f"{row['Dátum']} | {row['Ki']} – {row['Megnevezés']} ({row['Összeg']:,} Ft)".replace(",", " ")
                for _, row in forditott_df.iterrows()
            }

            kivalasztott_sor = st.selectbox(
                "Válaszd ki a törlendő tételt:",
                options=list(opciok.keys()),
                format_func=lambda x: opciok[x],
            )

            if st.button("🗑️ Kiválasztott tétel végleges törlése", type="primary", use_container_width=True):
                with st.spinner("Törlés a Google Táblázatból..."):
                    sheet.delete_rows(int(kivalasztott_sor))
                hangeffekt("torles")
                st.toast("Tétel törölve!", icon="🗑️")
                st.success("A tétel sikeresen törölve lett!")
                time.sleep(1.0)
                st.rerun()
