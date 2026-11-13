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
    [data-testid="stHeader"] { background: transparent !important; }

    button, input, [data-testid="stMetric"], [data-baseweb="tab"] {
        transition: all 0.22s cubic-bezier(0.22, 1, 0.36, 1) !important;
    }
    button:active { transform: scale(0.98) !important; }

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

st.title("🍂 Közös pénzügyek ✨")

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
        return pd.DataFrame(columns=["Sheet_Row", "Dátum", "Ki", "Kategória", "Megnevezés", "Összeg"])
    df = pd.DataFrame(rekordok)
    df["Sheet_Row"] = range(2, len(df) + 2)
    df["Összeg"] = pd.to_numeric(df["Összeg"], errors="coerce").fillna(0).astype(int)
    return df

df = adatok_betoltese()
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
        kiadasok = df[(~df["Kategória"].str.startswith("Bevétel:", na=False)) & (~df["Kategória"].isin(["Tartozás", "Hitel: Keret", "Hitel: Törlesztés"]))].copy()

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
                color_discrete_sequence=["#f59e0b", "#10b981", "#d97706", "#0ea5e9"],
            )
            fig_bev.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
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
                color_discrete_sequence=["#f59e0b", "#10b981", "#ea580c", "#0d9488", "#eab308", "#e11d48", "#3b82f6", "#a855f7", "#14b8a6"],
            )
            fig_ki.update_layout(margin=dict(t=40, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc")
            st.plotly_chart(fig_ki, use_container_width=True)

        if not tartozasok.empty:
            st.divider()
            st.subheader("💸 Rögzített tartozások")
            tartozasok["Irány"] = tartozasok["Megnevezés"].str.extract(r"\(([^)]+→[^)]+)\)")[0].fillna(tartozasok["Ki"])
            for _, sor in tartozasok.groupby("Irány", as_index=False)["Összeg"].sum().iterrows():
                st.metric(sor["Irány"], f"{sor['Összeg']:,.0f} Ft".replace(",", " "))

with tab_hitel:
    st.subheader("🏦 Hitel és törlesztés követő")
    hitel_keretek = df[df["Kategória"] == "Hitel: Keret"].copy()
    hitel_torlesztesek = df[df["Kategória"] == "Hitel: Törlesztés"].copy()

    if hitel_keretek.empty:
        st.info("Még nincs beállított hitel. Nyisd le az alábbi panelt az első hitel rögzítéséhez!")
    else:
        honap_nevek = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember", "október", "november", "december"]
        akt_honap = date.today().strftime("%Y-%m")

        for _, h_sor in hitel_keretek.iterrows():
            # Formátum: "Hitel neve | havi:25000"
            reszek = str(h_sor["Megnevezés"]).split("|")
            h_nev = reszek[0].strip()
            havi_torleszto = 0
            if len(reszek) > 1 and "havi:" in reszek[1]:
                try:
                    havi_torleszto = int(reszek[1].replace("havi:", "").strip())
                except ValueError:
                    havi_torleszto = 0

            teljes_osszeg = int(h_sor["Összeg"])
            kapcsolodo_befizetesek = hitel_torlesztesek[hitel_torlesztesek["Megnevezés"].str.startswith(h_nev, na=False)]
            eddig_kifizetve = int(kapcsolodo_befizetesek["Összeg"].sum()) if not kapcsolodo_befizetesek.empty else 0
            e_havi_levonas = int(kapcsolodo_befizetesek[kapcsolodo_befizetesek["Dátum"].astype(str).str.startswith(akt_honap)]["Összeg"].sum()) if not kapcsolodo_befizetesek.empty else 0
            hatralevo = max(0, teljes_osszeg - eddig_kifizetve)
            szazalek = min(1.0, eddig_kifizetve / teljes_osszeg) if teljes_osszeg > 0 else 0.0

            st.markdown(f"### 📌 {h_nev}")
            st.progress(szazalek, text=f"Kifizetve: {szazalek*100:.1f}% ({eddig_kifizetve:,.0f} Ft / {teljes_osszeg:,.0f} Ft)".replace(",", " "))

            hc1, hc2 = st.columns(2)
            hc1.metric("Hátralévő tartozás", f"{hatralevo:,.0f} Ft".replace(",", " "))
            hc2.metric("Ebben a hónapban levonva", f"{e_havi_levonas:,.0f} Ft".replace(",", " "))

            if hatralevo == 0:
                st.success("🎉 Ez a hitel teljesen ki van fizetve!")
            elif havi_torleszto > 0:
                hatralevo_honapok = -(-hatralevo // havi_torleszto)  # felfelé kerekítés
                ma = date.today()
                cel_ev = ma.year + (ma.month - 1 + hatralevo_honapok) // 12
                cel_honap = (ma.month - 1 + hatralevo_honapok) % 12 + 1
                st.info(f"⏳ Havi **{havi_torleszto:,.0f} Ft**-os törlesztővel még **{hatralevo_honapok} hónap** van hátra → Várható lejárat: **{cel_ev}. {honap_nevek[cel_honap - 1]}**".replace(",", " "))
            st.divider()

        # Havi levonás rögzítése
        with st.expander("💸 Havi levonás / törlesztés rögzítése", expanded=True):
            hitel_nevek = [str(x).split("|")[0].strip() for x in hitel_keretek["Megnevezés"]]
            valasztott_hitel = st.selectbox("Melyik hitelhez?", hitel_nevek)
            # Alapértelmezett összegként betölti a beállított havi törlesztőt
            alap_torleszto = 0
            for _, h_sor in hitel_keretek.iterrows():
                if str(h_sor["Megnevezés"]).split("|")[0].strip() == valasztott_hitel and "havi:" in str(h_sor["Megnevezés"]):
                    try:
                        alap_torleszto = int(str(h_sor["Megnevezés"]).split("havi:")[1].strip())
                    except ValueError:
                        alap_torleszto = 0
            levont_osszeg = st.number_input("Levont összeg (Ft)", min_value=0, value=alap_torleszto, step=500, key="hitel_levonas_osszeg")
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
                    st.toast("Havi levonás rögzítve!", icon="🏦")
                    time.sleep(0.9)
                    st.rerun()

    with st.expander("⚙️ Új hitel beállítása"):
        uj_hitel_nev = st.text_input("Hitel neve (pl. Telefon részlet, Személyi kölcsön)").strip()
        uj_hitel_teljes = st.number_input("Teljes visszafizetendő összeg (Ft)", min_value=0, step=5000, key="uj_hitel_teljes")
        uj_hitel_havi = st.number_input("Havi törlesztőrészlet (Ft)", min_value=0, step=1000, key="uj_hitel_havi")
        if st.button("💾 Hitel mentése", use_container_width=True):
            if not uj_hitel_nev or uj_hitel_teljes <= 0:
                hangeffekt("hiba")
                st.warning("Add meg a hitel nevét és a teljes összeget!")
            else:
                with st.spinner("Mentés..."):
                    sheet.append_row([str(date.today()), "Zsolt", "Hitel: Keret", f"{uj_hitel_nev} | havi:{int(uj_hitel_havi)}", int(uj_hitel_teljes)])
                adatok_betoltese.clear()
                hangeffekt("siker")
                st.toast(f"Hitel létrehozva: {uj_hitel_nev}!", icon="🏦")
                time.sleep(0.9)
                st.rerun()

with tab_lista:
    if df.empty:
        st.info("Üres a lista.")
    else:
        st.dataframe(df.iloc[::-1].drop(columns=["Sheet_Row"]), use_container_width=True, hide_index=True)
        if st.button("🔄 Frissítés a felhőből", use_container_width=True):
            adatok_betoltese.clear()
            hangeffekt("frissites")
            st.toast("Frissítve!", icon="🔄")
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
