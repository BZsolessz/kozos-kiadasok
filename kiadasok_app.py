import re
import time
from datetime import date, timedelta
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Közös pénzügyek 🍂",
    page_icon="🍂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- TITKOS ÜZENET BEÁLLÍTÁSA ---
TITKOS_UZENET_CIM = "Drága Vivienem ❤️"
TITKOS_UZENET_SZOVEG = """
Ha ezt most olvasod, megtaláltad a kis titkos rejtekhelyünket ebben az alkalmazásban. 🍂✨<br><br>
Nemcsak a közös pénzügyeinket és a mindennapjainkat szeretem veled építeni, hanem minden egyes közös pillanatot, nevetést és csendet is melletted. Te vagy a legjobb dolog, ami velem történt, és végtelenül hálás vagyok azért, hogy vagy nekem.<br><br>
<b>Nagyon-nagyon szeretlek, ma, holnap és mindörökké! 💕</b>
"""

if "titkos_mod" not in st.session_state:
    st.session_state["titkos_mod"] = False

if st.query_params.get("secret") == "vivien":
    st.session_state["titkos_mod"] = True
    st.query_params.clear()

if "aktiv_oldal" not in st.session_state:
    st.session_state["aktiv_oldal"] = "uj"

if st.session_state.pop("reset_uj_tetel", False):
    st.session_state["uj_tetel_osszeg"] = ""
if st.session_state.pop("reset_uj_hitel", False):
    for k in ["uj_hitel_teljes", "uj_hitel_jelenlegi", "uj_hitel_havi"]:
        st.session_state[k] = ""
if st.session_state.pop("reset_alberlet_tetel", False):
    st.session_state["alb_tetel_osszeg"] = ""

# --- MOBILE-FIRST GLASSMORPHISM ŐSZI TÉMA ---
st.markdown(
    """<style>
    :root {
        color-scheme: dark !important;
        --bg-deep: #070c0b;
        --glass-bg: rgba(15, 25, 23, 0.78);
        --glass-border: rgba(251, 191, 36, 0.22);
        --amber: #f59e0b;
        --amber-light: #fcd34d;
        --emerald: #10b981;
        --emerald-light: #6ee7b7;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }

    /* Streamlit alapértelmezett chrome elrejtése a natív app érzetért */
    #MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stDecoration"], .stDeployButton, [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior-y: contain !important;
        touch-action: pan-y !important;
        color: var(--text-main) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-deep) !important;
        background-image:
            radial-gradient(circle at 15% 8%, rgba(245, 158, 11, 0.22) 0%, transparent 45%),
            radial-gradient(circle at 85% 18%, rgba(16, 185, 129, 0.20) 0%, transparent 48%),
            radial-gradient(circle at 20% 85%, rgba(217, 119, 6, 0.16) 0%, transparent 50%),
            linear-gradient(165deg, #070c0b 0%, #0d1816 52%, #15110c 100%) !important;
        background-attachment: fixed !important;
    }

    /* Konténer: mobilon teljes szélesség, alul hely az alsó navigációnak */
    .block-container {
        max-width: 640px !important;
        padding-top: 0.75rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 6.2rem !important;
        margin: 0 auto !important;
    }

    /* Kompakt mobilos felső app-sáv */
    .app-header {
        background: linear-gradient(135deg, rgba(17, 29, 26, 0.90), rgba(24, 19, 14, 0.88));
        border: 1px solid rgba(251, 191, 36, 0.26);
        border-radius: 20px;
        padding: 12px 16px;
        margin-bottom: 14px;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    }
    .app-brand {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .leaf-btn {
        font-size: 1.55rem;
        line-height: 1;
        cursor: pointer;
        user-select: none;
        padding: 4px;
        border-radius: 12px;
        background: rgba(251, 191, 36, 0.12);
        border: 1px solid rgba(251, 191, 36, 0.25);
        transition: transform 0.15s ease;
    }
    .leaf-btn:active { transform: scale(1.2) rotate(15deg); }
    .app-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.2;
    }
    .app-date {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .balance-chip {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(52, 211, 153, 0.40);
        border-radius: 14px;
        padding: 6px 12px;
        text-align: right;
    }
    .balance-chip-neg {
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(251, 191, 36, 0.42);
        border-radius: 14px;
        padding: 6px 12px;
        text-align: right;
    }
    .balance-lbl {
        font-size: 0.62rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        display: block;
    }
    .balance-val {
        font-size: 0.96rem;
        font-weight: 800;
        color: #6ee7b7;
        white-space: nowrap;
    }
    .balance-chip-neg .balance-val { color: #fcd34d; }

    /* Fix alsó mobil navigációs sáv */
    .bottom-nav-wrap {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 99999;
        display: flex;
        justify-content: center;
        padding: 8px 10px calc(10px + env(safe-area-inset-bottom, 0px)) 10px;
        background: linear-gradient(to top, rgba(7, 12, 11, 0.96) 72%, rgba(7, 12, 11, 0));
        pointer-events: none;
    }
    .bottom-nav-bar {
        pointer-events: auto;
        width: 100%;
        max-width: 610px;
        background: rgba(14, 23, 21, 0.92);
        border: 1px solid rgba(251, 191, 36, 0.28);
        border-radius: 22px;
        padding: 5px;
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 4px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    .nav-item {
        text-decoration: none !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 7px 2px;
        border-radius: 16px;
        color: #94a3b8 !important;
        font-size: 0.68rem;
        font-weight: 600;
        gap: 2px;
        transition: all 0.18s ease;
        -webkit-tap-highlight-color: transparent;
    }
    .nav-item-ico {
        font-size: 1.18rem;
        line-height: 1.1;
    }
    .nav-item.active {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.38), rgba(5, 150, 105, 0.38));
        border: 1px solid rgba(251, 191, 36, 0.52);
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.22);
    }

    /* Szekció címek és üveg kártyák */
    .sec-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #fbbf24;
        margin: 6px 0 8px 2px;
    }
    .glass-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 14px;
        margin-bottom: 12px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.26);
    }
    .glass-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #fbbf24;
        margin-bottom: 10px;
        gap: 6px;
    }

    /* Mobilos érintésbarát gombok és inputok */
    button[kind="primary"] {
        background: linear-gradient(135deg, #d97706, #059669) !important;
        border: 1px solid rgba(251, 191, 36, 0.65) !important;
        border-radius: 15px !important;
        min-height: 48px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        box-shadow: 0 6px 18px rgba(217, 119, 6, 0.28) !important;
    }
    button[kind="secondary"] {
        background: rgba(15, 25, 23, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.11) !important;
        border-radius: 14px !important;
        color: #e2e8f0 !important;
        min-height: 44px !important;
        padding: 6px 6px !important;
    }
    button[kind="secondary"]:hover {
        border-color: rgba(251, 191, 36, 0.45) !important;
        color: #ffffff !important;
    }
    button[kind="secondary"] p {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }
    button:active { transform: scale(0.97) !important; }

    /* Input mezők nagyítása mobilon (16px font = nincs iOS/Android auto-zoom) */
    input, [data-baseweb="input"] input, [data-baseweb="select"] {
        font-size: 16px !important;
        min-height: 44px !important;
        border-radius: 13px !important;
    }
    [data-baseweb="input"] {
        background-color: rgba(10, 17, 16, 0.85) !important;
        border-color: rgba(251, 191, 36, 0.25) !important;
        border-radius: 13px !important;
    }

    /* Radio & Pills mobilos stílus */
    [data-testid="stRadio"] > div {
        background: rgba(11, 19, 17, 0.80);
        border: 1px solid rgba(251, 191, 36, 0.22);
        border-radius: 14px;
        padding: 6px 10px;
        justify-content: space-around;
    }
    [data-testid="stPills"] button {
        background: rgba(14, 23, 21, 0.85) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(245, 158, 11, 0.28) !important;
        border-radius: 999px !important;
        min-height: 36px !important;
        padding: 4px 12px !important;
    }
    [data-testid="stPills"] button[aria-pressed="true"] {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.80), rgba(5, 150, 105, 0.80)) !important;
        border-color: #fbbf24 !important;
        color: #ffffff !important;
    }

    /* Statisztika KPI rács (2 oszlopos mobilon) */
    .kpi-hero-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.14), rgba(245, 158, 11, 0.12));
        border: 1px solid rgba(52, 211, 153, 0.30);
        border-radius: 16px;
        padding: 12px 14px;
        text-align: center;
        margin-bottom: 8px;
    }
    .kpi-two-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .kpi-mini-box {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 10px 12px;
    }
    .kpi-lbl { font-size: 0.70rem; color: #94a3b8; margin-bottom: 2px; }
    .kpi-val { font-size: 1.08rem; font-weight: 800; color: #f8fafc; }

    /* Megoszlás sáv és kategória sorok */
    .split-bar {
        width: 100%;
        height: 10px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        overflow: hidden;
        display: flex;
        margin: 8px 0 4px 0;
    }
    .split-zsolt { background: linear-gradient(90deg, #f59e0b, #fbbf24); height: 100%; }
    .split-vivien { background: linear-gradient(90deg, #10b981, #34d399); height: 100%; }

    .cat-row {
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .cat-row:last-child { border-bottom: none; }
    .cat-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        margin-bottom: 5px;
    }
    .cat-pct {
        background: rgba(245, 158, 11, 0.18);
        border: 1px solid rgba(251, 191, 36, 0.38);
        color: #fcd34d;
        font-weight: 700;
        font-size: 0.70rem;
        padding: 1px 7px;
        border-radius: 999px;
        margin-left: 4px;
    }
    .cat-bar-bg {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.07);
        border-radius: 999px;
        overflow: hidden;
    }
    .cat-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #f59e0b, #10b981);
    }

    /* Albérlet státusz és mérőóra kártya */
    .badge-ok {
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(52, 211, 153, 0.42);
        color: #6ee7b7;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 700;
    }
    .badge-warn {
        background: rgba(245, 158, 11, 0.18);
        border: 1px solid rgba(251, 191, 36, 0.45);
        color: #fcd34d;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.68rem;
        font-weight: 700;
    }
    .meter-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(56, 189, 248, 0.24);
        border-left: 4px solid #38bdf8;
        border-radius: 14px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }

    /* Tranzakció kártyák */
    .tx-item {
        background: linear-gradient(135deg, rgba(16, 26, 24, 0.86), rgba(12, 20, 18, 0.80));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #f59e0b;
        border-radius: 15px;
        padding: 10px 12px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }
    .tx-bev { border-left-color: #10b981; }
    .tx-hitel { border-left-color: #38bdf8; }
    .tx-tart { border-left-color: #f43f5e; }
    .tx-alb { border-left-color: #a855f7; }
    .tx-del {
        background: rgba(127, 29, 29, 0.45);
        border: 1px solid rgba(248, 113, 113, 0.65);
        border-left: 4px solid #ef4444;
    }
    .tx-name {
        font-size: 0.90rem;
        font-weight: 600;
        color: #f8fafc;
        line-height: 1.25;
        word-break: break-word;
    }
    .tx-sub {
        font-size: 0.71rem;
        color: #94a3b8;
        margin-top: 3px;
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        align-items: center;
    }
    .tx-tag {
        background: rgba(255, 255, 255, 0.07);
        padding: 1px 7px;
        border-radius: 999px;
        color: #e2e8f0;
        font-size: 0.67rem;
    }
    .tx-val {
        font-size: 0.94rem;
        font-weight: 800;
        white-space: nowrap;
        text-align: right;
    }

    /* Titkos romantikus mód */
    .love-card {
        background: linear-gradient(145deg, rgba(66, 16, 36, 0.88), rgba(32, 15, 38, 0.90));
        border: 1px solid rgba(244, 114, 182, 0.50);
        border-radius: 26px;
        padding: 26px 20px;
        margin: 12px auto 16px auto;
        text-align: center;
        backdrop-filter: blur(18px);
        box-shadow: 0 16px 45px rgba(225, 29, 72, 0.30);
    }
    .love-hearts { font-size: 1.7rem; letter-spacing: 8px; margin-bottom: 10px; }
    .love-title {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #fbcfe8, #fda4af, #fde68a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 14px;
    }
    .love-body { font-size: 1.0rem; line-height: 1.68; color: #ffe4e6; margin-bottom: 16px; }
    .love-sign { font-size: 0.92rem; font-weight: 700; color: #fbcfe8; }

    /* Oszlopok megtartása keskeny mobil kijelzőn is */
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 0 !important;
    }
    </style>""",
    unsafe_allow_html=True,
)


def globalis_gomb_hang_es_titok():
    """Azonnali UI-kattanás + 5x koppintásos titkos mód a 🍂 ikonon + alsó menü navigáció."""
    components.html(
        """<script>
        (function() {
            try {
                const pDoc = window.parent.document;
                const pWin = window.parent;
                if (pWin.__kozosUiClickHooked) return;
                pWin.__kozosUiClickHooked = true;

                let audioCtx = null;
                function playClick() {
                    try {
                        const Ctx = pWin.AudioContext || pWin.webkitAudioContext;
                        if (!Ctx) return;
                        if (!audioCtx) audioCtx = new Ctx();
                        if (audioCtx.state === 'suspended') audioCtx.resume();
                        const now = audioCtx.currentTime;
                        const osc = audioCtx.createOscillator();
                        const gain = audioCtx.createGain();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(740, now);
                        osc.frequency.exponentialRampToValueAtTime(510, now + 0.036);
                        gain.gain.setValueAtTime(0.11, now);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.042);
                        osc.connect(gain);
                        gain.connect(audioCtx.destination);
                        osc.start(now);
                        osc.stop(now + 0.045);
                    } catch (err) {}
                }

                let leafTaps = 0;
                let leafTimer = null;

                pDoc.addEventListener('pointerdown', function(e) {
                    const leaf = e.target.closest('#secret-leaf-btn');
                    if (leaf) {
                        playClick();
                        leafTaps++;
                        clearTimeout(leafTimer);
                        leafTimer = setTimeout(function() { leafTaps = 0; }, 2200);
                        if (leafTaps >= 5) {
                            leafTaps = 0;
                            const url = new URL(pWin.location.href);
                            url.searchParams.set('secret', 'vivien');
                            pWin.location.href = url.toString();
                        }
                        return;
                    }

                    const nav = e.target.closest('.nav-item');
                    if (nav) {
                        playClick();
                        return;
                    }

                    const target = e.target.closest(
                        'button, [role="tab"], [role="radio"], [role="option"], [data-baseweb="radio"], [data-testid="stExpander"] summary'
                    );
                    if (target && !target.disabled) {
                        playClick();
                    }
                }, { capture: true, passive: true });
            } catch (e) {}
        })();
        </script>""",
        height=0,
    )


globalis_gomb_hang_es_titok()


def romantikus_zene_lejatszo():
    components.html(
        """<div style="display:flex; justify-content:center; margin-top:4px;">
            <button id="love-music-btn" style="
                background: linear-gradient(135deg, rgba(244, 63, 94, 0.82), rgba(217, 70, 239, 0.72));
                border: 1px solid rgba(251, 207, 232, 0.65);
                color: #fff1f2;
                font-family: sans-serif;
                font-size: 0.90rem;
                font-weight: 700;
                padding: 11px 22px;
                border-radius: 999px;
                cursor: pointer;
                box-shadow: 0 6px 20px rgba(244, 63, 94, 0.35);
            ">🎵 Romantikus zene lejátszása / megállítása</button>
        </div>
        <script>
        (function() {
            const Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            let ctx = null, playing = false, loopTimer = null;
            const melody = [
                [349.23, 0.0, 1.4], [440.00, 0.45, 1.3], [523.25, 0.90, 1.4], [659.25, 1.35, 1.8],
                [587.33, 2.2, 0.9], [523.25, 2.7, 1.5],
                [329.63, 3.6, 1.4], [392.00, 4.05, 1.3], [523.25, 4.50, 1.4], [587.33, 4.95, 1.8],
                [523.25, 5.8, 0.9], [440.00, 6.3, 1.5],
                [293.66, 7.2, 1.4], [349.23, 7.65, 1.3], [440.00, 8.10, 1.4], [523.25, 8.55, 1.8],
                [493.88, 9.4, 0.9], [440.00, 9.9, 1.5],
                [233.08, 10.8, 1.4], [349.23, 11.25, 1.3], [440.00, 11.70, 1.4], [523.25, 12.15, 2.0],
                [440.00, 13.1, 1.6]
            ];
            function playPianoNote(freq, startOffset, dur) {
                if (!ctx || !playing) return;
                const now = ctx.currentTime + startOffset;
                const osc1 = ctx.createOscillator(), osc2 = ctx.createOscillator(), gain = ctx.createGain();
                osc1.type = 'sine'; osc2.type = 'triangle';
                osc1.frequency.setValueAtTime(freq, now); osc2.frequency.setValueAtTime(freq * 2, now);
                const subGain = ctx.createGain(); subGain.gain.setValueAtTime(0.035, now);
                gain.gain.setValueAtTime(0.0001, now);
                gain.gain.linearRampToValueAtTime(0.14, now + 0.06);
                gain.gain.exponentialRampToValueAtTime(0.0008, now + dur + 0.6);
                osc1.connect(gain); osc2.connect(subGain); subGain.connect(gain); gain.connect(ctx.destination);
                osc1.start(now); osc2.start(now); osc1.stop(now + dur + 0.7); osc2.stop(now + dur + 0.7);
            }
            function scheduleLoop() {
                if (!playing) return;
                melody.forEach(n => playPianoNote(n[0], n[1], n[2]));
                loopTimer = setTimeout(scheduleLoop, 14600);
            }
            function startMusic() {
                if (!ctx) ctx = new Ctx();
                if (ctx.state === 'suspended') ctx.resume();
                if (playing) return;
                playing = true;
                btn.innerText = "⏸️ Zene szüneteltetése (szól a dallam 💕)";
                scheduleLoop();
            }
            function stopMusic() {
                playing = false;
                clearTimeout(loopTimer);
                btn.innerText = "🎵 Romantikus zene indítása";
            }
            const btn = document.getElementById('love-music-btn');
            btn.addEventListener('click', function() { if (playing) stopMusic(); else startMusic(); });
            try { startMusic(); if (ctx && ctx.state === 'suspended') stopMusic(); } catch (e) {}
        })();
        </script>""",
        height=56,
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
            }} else if (t==="torles") {{
                p(293.66, now, 0.28, 'sine', 0.18);
                p(220.00, now+0.13, 0.42, 'sine', 0.18);
            }} else if (t==="frissites") {{
                p(659.25, now, 0.12, 'sine', 0.15);
                p(987.77, now+0.08, 0.22, 'sine', 0.16);
            }} else if (t==="hiba") {{
                p(196.00, now, 0.15, 'triangle', 0.20);
                p(196.00, now+0.17, 0.20, 'triangle', 0.20);
            }}
        }} catch (e) {{}}</script>""",
        height=0,
    )


# --- TITKOS ROMANTIKUS NÉZET ---
if st.session_state.get("titkos_mod", False):
    st.markdown(
        f'<div class="love-card"><div class="love-hearts">💖 ✨ 🍂 ✨ 💖</div><div class="love-title">{TITKOS_UZENET_CIM}</div><div class="love-body">{TITKOS_UZENET_SZOVEG}</div><div class="love-sign">— Örökké a tiéd, Zsolt ❤️</div></div>',
        unsafe_allow_html=True,
    )
    romantikus_zene_lejatszo()
    st.write("")
    if st.button("🔙 Vissza a pénzügyekhez", use_container_width=True, type="primary"):
        st.session_state["titkos_mod"] = False
        st.rerun()
    st.stop()


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


def mobil_kategoria_racs(opciok_lista, state_key, oszlopok=3):
    """Kompakt 3 oszlopos mobilos érintőrács ikonnal és rövid címkével."""
    if state_key not in st.session_state or st.session_state[state_key] not in [o[0] for o in opciok_lista]:
        st.session_state[state_key] = opciok_lista[0][0]

    aktualis = st.session_state[state_key]
    for i in range(0, len(opciok_lista), oszlopok):
        cols = st.columns(oszlopok)
        for j in range(oszlopok):
            if i + j < len(opciok_lista):
                valos_nev, rovid_cimke = opciok_lista[i + j]
                kivalasztva = (valos_nev == aktualis)
                felirat = f"✓ {rovid_cimke}" if kivalasztva else rovid_cimke
                if cols[j].button(
                    felirat,
                    key=f"{state_key}_btn_{i+j}",
                    use_container_width=True,
                    type="primary" if kivalasztva else "secondary",
                ):
                    st.session_state[state_key] = valos_nev
                    st.rerun()
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

KIZART_KATEGORIAK = [
    "Tartozás",
    "Hitel: Keret",
    "Hitel: Törlesztés",
    "Albérlet: Beállítás",
    "Albérlet: Óraállás",
    "Albérlet: Csak napló",
]

if not df.empty:
    _bev = df[df["Kategória"].str.startswith("Bevétel:", na=False)]["Összeg"].sum()
    _ki = df[(~df["Kategória"].str.startswith("Bevétel:", na=False)) & (~df["Kategória"].isin(KIZART_KATEGORIAK))]["Összeg"].sum()
    aktualis_egyenleg = int(_bev - _ki)
else:
    aktualis_egyenleg = 0

# --- URL QUERY PARAMÉTER ALAPÚ NAVIGÁCIÓ ---
nav_param = st.query_params.get("nav")
if nav_param in ["uj", "stat", "alb", "hitel", "lista"]:
    st.session_state["aktiv_oldal"] = nav_param
    st.query_params.clear()

aktiv_oldal = st.session_state["aktiv_oldal"]
ma_fejlec = date.today()
bal_cls = "balance-chip" if aktualis_egyenleg >= 0 else "balance-chip-neg"

# --- KOMPAKT MOBIL FEJLÉC ---
st.markdown(
    f'<div class="app-header"><div class="app-brand"><div id="secret-leaf-btn" class="leaf-btn">🍂</div><div><div class="app-title">Közös pénzügyek</div><div class="app-date">Zsolt &amp; Vivien • {ma_fejlec.month:02d}. {ma_fejlec.day:02d}.</div></div></div><div class="{bal_cls}"><span class="balance-lbl">Kassza egyenleg</span><span class="balance-val">{fmt_ft(aktualis_egyenleg)} Ft</span></div></div>',
    unsafe_allow_html=True,
)

# ==============================================================================
# 1. NÉZET: ÚJ TÉTEL
# ==============================================================================
if aktiv_oldal == "uj":
    tipus = st.radio("Művelet", ["➖ Kiadás", "➕ Bevétel"], horizontal=True, label_visibility="collapsed")

    st.markdown('<div class="sec-title">1. Válassz kategóriát</div>', unsafe_allow_html=True)
    if tipus == "➕ Bevétel":
        bevetel_opciok = [
            ("Közös kasszába befizetés", "💰 Kassza"),
            ("Ajándék / Támogatás", "🎁 Ajándék"),
            ("Eladás / Visszatérítés", "🔄 Visszatérítés"),
            ("Egyéb bevétel", "✨ Egyéb"),
        ]
        kat_val = mobil_kategoria_racs(bevetel_opciok, "valasztott_bev_kat", oszlopok=2)
        kategoria = f"Bevétel: {kat_val}"
    else:
        kiadas_opciok = [
            ("Élelmiszer & Háztartás", "🛒 Élelmiszer"),
            ("Étterem & Randi", "🍽️ Randi/Étel"),
            ("Üzemanyag & Autó", "⛽ Autó"),
            ("Lakhatás & Rezsi", "🏠 Lakhatás"),
            ("Gyógyszertár", "💊 Patika"),
            ("Dohánybolt", "🚬 Trafik"),
            ("Előfizetés", "📱 Előfizetés"),
            ("Ajándékozás", "🎁 Ajándék"),
            ("Tech & Vásárlás", "💻 Vásárlás"),
            ("Tartozás", "💸 Tartozás"),
            ("Egyéb", "📦 Egyéb"),
        ]
        kategoria = mobil_kategoria_racs(kiadas_opciok, "valasztott_ki_kat", oszlopok=3)

    st.markdown('<div class="sec-title">2. Részletek</div>', unsafe_allow_html=True)
    if tipus == "➕ Bevétel":
        ki = st.text_input("Kitől / Ki tette bele?", placeholder="pl. Zsolt, Vivien, Szülők").strip()
        megnevezes = st.text_input("Megnevezés", placeholder="pl. Havi keret, Visszatérítés")
    else:
        if kategoria == "Tartozás":
            c1, c2 = st.columns(2)
            ki_tartozik = c1.text_input("Ki tartozik?", placeholder="pl. Zsolt").strip()
            kinek_tartozik = c2.text_input("Kinek?", placeholder="pl. Vivien").strip()
            ki = ki_tartozik
        else:
            ki = st.radio("Ki fizette?", ["Zsolt", "Vivien"], horizontal=True, label_visibility="collapsed")

        placeholder_szoveg = {
            "Gyógyszertár": "Mit vettetek? (pl. Vitamin, Gyógyszer)",
            "Tartozás": "Mire vonatkozik?",
            "Előfizetés": "Melyik előfizetés? (pl. Netflix, Internet)",
            "Dohánybolt": "Mit vettetek? (pl. Trafik, Üdítő)",
            "Ajándékozás": "Kinek és mit?",
        }.get(kategoria, "Mit vettetek? (pl. Lidl, Kávézó)")
        megnevezes = st.text_input("Megnevezés", placeholder=placeholder_szoveg)

    c_osszeg, c_datum = st.columns([1.3, 1])
    with c_osszeg:
        osszeg = osszeg_mezo("Összeg (Ft)", key="uj_tetel_osszeg")
    with c_datum:
        datum = st.date_input("Dátum", value=date.today())

    st.write("")
    if st.button("🍂 Rögzítés a felhőbe", use_container_width=True, type="primary"):
        if megnevezes.strip().lower() in ["vivien", "szeretlek", "titok", "❤️"]:
            st.session_state["titkos_mod"] = True
            hangeffekt("siker")
            st.rerun()

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
            time.sleep(0.8)
            st.rerun()

# ==============================================================================
# 2. NÉZET: STATISZTIKA
# ==============================================================================
elif aktiv_oldal == "stat":
    if df.empty:
        st.info("Még nincs rögzített tétel.")
    else:
        nem_hitel_df = df[~df["Kategória"].isin(KIZART_KATEGORIAK)]
        elerheto_honapok = sorted([h for h in nem_hitel_df["Ev_Honap"].unique() if h != "Ismeretlen"], reverse=True)

        if len(elerheto_honapok) > 1:
            opciok_map = {h: honap_cimke(h) for h in elerheto_honapok}
            opciok_map["OSSZES"] = "♾️ Összes"
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
        kiadasok = stat_df[(~stat_df["Kategória"].str.startswith("Bevétel:", na=False)) & (~stat_df["Kategória"].isin(KIZART_KATEGORIAK))].copy()

        ossz_bevetel = int(bevetelek["Összeg"].sum()) if not bevetelek.empty else 0
        ossz_kiadas = int(kiadasok["Összeg"].sum()) if not kiadasok.empty else 0
        egyenleg = ossz_bevetel - ossz_kiadas
        egyenleg_szin = "#34d399" if egyenleg >= 0 else "#fbbf24"

        st.markdown(
            f'<div class="glass-card"><div class="glass-header"><span>📌 Havi mérleg</span><span style="color:#94a3b8;">{idoszak_cim}</span></div><div class="kpi-hero-box"><div class="kpi-lbl">Időszaki egyenleg</div><div class="kpi-val" style="font-size:1.35rem; color:{egyenleg_szin};">{fmt_ft(egyenleg)} Ft</div></div><div class="kpi-two-grid"><div class="kpi-mini-box"><div class="kpi-lbl">➕ Bevétel</div><div class="kpi-val" style="color:#6ee7b7;">{fmt_ft(ossz_bevetel)} Ft</div></div><div class="kpi-mini-box"><div class="kpi-lbl">➖ Kiadás</div><div class="kpi-val" style="color:#fcd34d;">{fmt_ft(ossz_kiadas)} Ft</div></div></div></div>',
            unsafe_allow_html=True,
        )

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

                st.markdown(
                    f'<div class="glass-card"><div class="glass-header"><span>👥 Ki mennyit fizetett</span></div><div style="display:flex; justify-content:space-between; font-size:0.82rem;"><span>🟡 <b>Zsolt:</b> {fmt_ft(zsolt_ki)} Ft ({str(zsolt_pct).replace(".", ",")}%)</span><span>🟢 <b>Vivien:</b> {fmt_ft(vivien_ki)} Ft ({str(vivien_pct).replace(".", ",")}%)</span></div><div class="split-bar"><div class="split-zsolt" style="width:{zsolt_pct}%;"></div><div class="split-vivien" style="width:{vivien_pct}%;"></div></div></div>',
                    unsafe_allow_html=True,
                )

                kat_osszesites = (
                    kiadasok.groupby("Kategória", as_index=False)
                    .agg(Összeg=("Összeg", "sum"), Darab=("Összeg", "count"))
                    .sort_values("Összeg", ascending=False)
                )
                kat_osszesites["Arány"] = (kat_osszesites["Összeg"] / ossz_kiadas * 100) if ossz_kiadas > 0 else 0.0

                sorok_html = ""
                for _, k_sor in kat_osszesites.iterrows():
                    arany_szazalek = float(k_sor["Arány"])
                    arany_szoveg = f"{arany_szazalek:.1f}".replace(".", ",")
                    sorok_html += f'<div class="cat-row"><div class="cat-top"><div><b>{k_sor["Kategória"]}</b> <span class="cat-pct">{arany_szoveg}%</span></div><div><b>{fmt_ft(k_sor["Összeg"])} Ft</b> <span style="color:#94a3b8; font-size:0.72rem;">({int(k_sor["Darab"])})</span></div></div><div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{min(100.0, arany_szazalek):.1f}%;"></div></div></div>'

                st.markdown(
                    f'<div class="glass-card"><div class="glass-header"><span>📊 Kategóriák bontása</span><span>{len(kat_osszesites)} db</span></div>{sorok_html}</div>',
                    unsafe_allow_html=True,
                )

                fig_ki = px.pie(
                    kat_osszesites,
                    values="Összeg",
                    names="Kategória",
                    hole=0.60,
                    color_discrete_sequence=["#f59e0b", "#10b981", "#ea580c", "#0d9488", "#eab308", "#e11d48", "#3b82f6", "#a855f7", "#14b8a6", "#ec4899"],
                )
                fig_ki.update_traces(textposition="inside", textinfo="percent")
                fig_ki.update_layout(
                    height=240,
                    margin=dict(t=6, b=6, l=6, r=6),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#f8fafc",
                    legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=10)),
                )
                st.plotly_chart(fig_ki, use_container_width=True, config={"displayModeBar": False})

        elif stat_nezet == "📥 Bevételek":
            if bevetelek.empty:
                st.info("Ebben az időszakban nincs rögzített bevétel.")
            else:
                bev_forras_html = ""
                for _, sor in bevetelek.groupby("Ki", as_index=False)["Összeg"].sum().sort_values("Összeg", ascending=False).iterrows():
                    pct = (sor["Összeg"] / ossz_bevetel * 100) if ossz_bevetel > 0 else 0.0
                    pct_str = f"{pct:.1f}".replace(".", ",")
                    bev_forras_html += f'<div class="cat-row"><div class="cat-top"><div><b>👤 {sor["Ki"]}</b> <span class="cat-pct">{pct_str}%</span></div><div style="color:#6ee7b7;"><b>{fmt_ft(sor["Összeg"])} Ft</b></div></div><div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{min(100.0, pct):.1f}%;"></div></div></div>'
                st.markdown(
                    f'<div class="glass-card"><div class="glass-header"><span>💰 Befizetők aránya</span></div>{bev_forras_html}</div>',
                    unsafe_allow_html=True,
                )

        elif stat_nezet == "💸 Tartozások":
            if tartozasok.empty:
                st.info("Ebben az időszakban nincs rögzített tartozás.")
            else:
                tartozasok["Irány"] = tartozasok["Megnevezés"].str.extract(r"\(([^)]+→[^)]+)\)")[0].fillna(tartozasok["Ki"])
                tart_html = ""
                for _, sor in tartozasok.groupby("Irány", as_index=False)["Összeg"].sum().iterrows():
                    tart_html += f'<div class="cat-row"><div class="cat-top"><b>💸 {sor["Irány"]}</b><b style="color:#fda4af;">{fmt_ft(sor["Összeg"])} Ft</b></div></div>'
                st.markdown(
                    f'<div class="glass-card"><div class="glass-header"><span>💸 Tartozások összesítője</span></div>{tart_html}</div>',
                    unsafe_allow_html=True,
                )

# ==============================================================================
# 3. NÉZET: ALBÉRLET
# ==============================================================================
elif aktiv_oldal == "alb":
    ma_alb = date.today()

    alb_beallitas_df = df[df["Kategória"] == "Albérlet: Beállítás"].copy()
    alap_berleti_dij = 0
    alap_kaucio = 0
    alap_fizetesi_nap = 10
    alap_foberlo = ""
    alap_megjegyzes = ""

    if not alb_beallitas_df.empty:
        utolso_beall = alb_beallitas_df.iloc[-1]
        alap_berleti_dij = int(utolso_beall["Összeg"])
        for r in str(utolso_beall["Megnevezés"]).split("|"):
            r = r.strip()
            if r.startswith("kaucio:"):
                try:
                    alap_kaucio = int(r.replace("kaucio:", "").strip())
                except ValueError:
                    alap_kaucio = 0
            elif r.startswith("nap:"):
                try:
                    alap_fizetesi_nap = int(r.replace("nap:", "").strip())
                except ValueError:
                    alap_fizetesi_nap = 10
            elif r.startswith("foberlo:"):
                alap_foberlo = r.replace("foberlo:", "").strip()
            elif r.startswith("megj:"):
                alap_megjegyzes = r.replace("megj:", "").strip()

    alb_penz_maszk = (
        (df["Kategória"] == "Lakhatás & Rezsi")
        | (df["Kategória"] == "Albérlet: Csak napló")
        | (df["Megnevezés"].astype(str).str.startswith("Albérlet:", na=False))
    )
    alb_penz_df = df[alb_penz_maszk].copy()

    ehavi_alb_df = alb_penz_df[alb_penz_df["Dátum"].apply(lambda d: datum_e_honapban_van_e(d, ma_alb.year, ma_alb.month))]
    ehavi_alb_osszeg = int(ehavi_alb_df["Összeg"].sum()) if not ehavi_alb_df.empty else 0
    ossz_alb_osszeg = int(alb_penz_df["Összeg"].sum()) if not alb_penz_df.empty else 0

    ehavi_berleti_fizetve = False
    if not ehavi_alb_df.empty:
        ehavi_berleti_fizetve = ehavi_alb_df["Megnevezés"].astype(str).str.lower().str.contains("bérleti díj|lakbér|albérlet", na=False).any()

    statusz_badge = (
        '<span class="badge-ok">✅ E havi lakbér OK</span>'
        if ehavi_berleti_fizetve
        else f'<span class="badge-warn">⏳ Esedékes: {alap_fizetesi_nap}.</span>'
    )

    fob_sor = f"<span>👤 {alap_foberlo}</span>" if alap_foberlo else ""
    megj_sor = f'<div style="font-size:0.74rem; color:#94a3b8; margin-top:6px;">📝 {alap_megjegyzes}</div>' if alap_megjegyzes else ""

    st.markdown(
        f'<div class="glass-card"><div class="glass-header"><span>🏠 Albérlet ({HONAP_NEVEK[ma_alb.month - 1]})</span>{statusz_badge}</div><div class="kpi-two-grid"><div class="kpi-mini-box"><div class="kpi-lbl">🔑 Bérleti díj</div><div class="kpi-val" style="color:#fbbf24;">{fmt_ft(alap_berleti_dij)} Ft</div></div><div class="kpi-mini-box"><div class="kpi-lbl">📅 E havi lakhatás</div><div class="kpi-val" style="color:#34d399;">{fmt_ft(ehavi_alb_osszeg)} Ft</div></div><div class="kpi-mini-box"><div class="kpi-lbl">🛡️ Kaució</div><div class="kpi-val" style="color:#7dd3fc;">{fmt_ft(alap_kaucio)} Ft</div></div><div class="kpi-mini-box"><div class="kpi-lbl">📊 Összes kiadás</div><div class="kpi-val">{fmt_ft(ossz_alb_osszeg)} Ft</div></div></div><div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; font-size:0.76rem; color:#cbd5e1; margin-top:8px;">{fob_sor}</div>{megj_sor}</div>',
        unsafe_allow_html=True,
    )

    alb_al_nezet = st.pills(
        "Albérlet nézet",
        ["💳 Befizetés", "⚡ Mérőórák", "📜 Napló", "⚙️ Adatok"],
        default="💳 Befizetés",
        key="alb_al_nezet_valaszto",
        label_visibility="collapsed",
    ) or "💳 Befizetés"

    if alb_al_nezet == "💳 Befizetés":
        alb_tipusok = [
            ("Bérleti díj", "🔑 Lakbér"),
            ("Közös költség", "🏢 Közös ktg."),
            ("Villany számla", "⚡ Villany"),
            ("Gáz / Fűtés számla", "🔥 Gáz/Fűtés"),
            ("Víz / Csatorna", "💧 Víz"),
            ("Internet & TV", "📶 Internet"),
            ("Javítás / Felszerelés", "🛠️ Javítás"),
            ("Egyéb rezsi", "📦 Egyéb"),
        ]
        val_alb_tipus = mobil_kategoria_racs(alb_tipusok, "valasztott_alb_tipus", oszlopok=4)

        alb_ki = st.radio("Ki fizette?", ["Zsolt", "Vivien"], horizontal=True, key="alb_ki_fizette", label_visibility="collapsed")
        alb_megj = st.text_input(
            "Megjegyzés",
            placeholder=f"pl. {ma_alb.year}. {HONAP_NEVEK[ma_alb.month - 1]}",
            key="alb_megj_input",
        ).strip()

        alapertelmezett_osszeg = alap_berleti_dij if (val_alb_tipus == "Bérleti díj" and alap_berleti_dij > 0) else 0
        if st.session_state.get("utolso_alb_tipus") != val_alb_tipus:
            st.session_state["utolso_alb_tipus"] = val_alb_tipus
            st.session_state["alb_tetel_osszeg"] = fmt_ft(alapertelmezett_osszeg) if alapertelmezett_osszeg > 0 else ""

        c_a1, c_a2 = st.columns([1.3, 1])
        with c_a1:
            alb_osszeg = osszeg_mezo("Összeg (Ft)", key="alb_tetel_osszeg", alap_ertek=alapertelmezett_osszeg)
        with c_a2:
            alb_datum = st.date_input("Dátum", value=date.today(), key="alb_befiz_datum")

        kasszabol_levon = st.checkbox(
            "💰 Levonom a közös kasszából és számolja a statisztika is",
            value=True,
            key="alb_kasszabol_cb",
        )

        if st.button("🏠 Albérlet tétel mentése", use_container_width=True, type="primary"):
            if alb_osszeg <= 0:
                hangeffekt("hiba")
                st.warning("Adj meg 0-nál nagyobb összeget!")
            else:
                teljes_nev = f"Albérlet: {val_alb_tipus}" + (f" ({alb_megj})" if alb_megj else "")
                cel_kategoria = "Lakhatás & Rezsi" if kasszabol_levon else "Albérlet: Csak napló"
                with st.spinner("Mentés..."):
                    sheet.append_row([str(alb_datum), alb_ki, cel_kategoria, teljes_nev, int(alb_osszeg)])
                st.session_state["reset_alberlet_tetel"] = True
                adatok_betoltese.clear()
                hangeffekt("siker")
                st.toast(f"Mentve: {teljes_nev}!", icon="🏠")
                time.sleep(0.8)
                st.rerun()

    elif alb_al_nezet == "⚡ Mérőórák":
        ora_df = df[df["Kategória"] == "Albérlet: Óraállás"].copy()
        if not ora_df.empty:
            ora_df["Ora_Nev"] = ora_df["Megnevezés"].astype(str).apply(lambda x: x.split("|")[0].strip())
            for o_nev in ora_df["Ora_Nev"].unique():
                sub_o = ora_df[ora_df["Ora_Nev"] == o_nev].copy()
                utolso_sor = sub_o.iloc[-1]
                utolso_ertek = int(utolso_sor["Összeg"])
                utolso_datum = str(utolso_sor["Dátum"])
                fogyasztas_html = ""
                if len(sub_o) >= 2:
                    elozo_ertek = int(sub_o.iloc[-2]["Összeg"])
                    kulonbseg = utolso_ertek - elozo_ertek
                    if kulonbseg >= 0:
                        fogyasztas_html = f'<span style="color:#6ee7b7; font-size:0.74rem;">(+{fmt_ft(kulonbseg)} fogyasztás)</span>'
                st.markdown(
                    f'<div class="meter-box"><div style="display:flex; justify-content:space-between; align-items:center;"><b>{o_nev}</b><span style="font-size:1.05rem; font-weight:800; color:#7dd3fc;">{fmt_ft(utolso_ertek)}</span></div><div style="display:flex; justify-content:space-between; margin-top:4px; font-size:0.72rem; color:#94a3b8;"><span>📅 {utolso_datum}</span>{fogyasztas_html}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="sec-title">Új óraállás rögzítése</div>', unsafe_allow_html=True)
        ora_tipus = st.selectbox(
            "Mérőóra",
            ["⚡ Villanyóra (kWh)", "🔥 Gázóra (m³)", "💧 Hideg vízóra (m³)", "♨️ Meleg vízóra (m³)"],
            key="ora_tipus_sel",
        )
        c_o1, c_o2 = st.columns([1.2, 1])
        with c_o1:
            ora_allas = st.number_input("Óraállás", min_value=0, step=1, key="ora_allas_num")
        with c_o2:
            ora_datum = st.date_input("Dátum", value=date.today(), key="ora_datum_inp")
        ora_megj = st.text_input("Megjegyzés", placeholder="pl. Fotózva, diktálva", key="ora_megj_inp").strip()

        if st.button("💾 Óraállás mentése", use_container_width=True, type="primary"):
            if ora_allas <= 0:
                hangeffekt("hiba")
                st.warning("Írj be 0-nál nagyobb óraállást!")
            else:
                ora_szoveg = f"{ora_tipus}" + (f" | {ora_megj}" if ora_megj else "")
                with st.spinner("Rögzítés..."):
                    sheet.append_row([str(ora_datum), "Zsolt", "Albérlet: Óraállás", ora_szoveg, int(ora_allas)])
                adatok_betoltese.clear()
                hangeffekt("siker")
                st.toast("Óraállás rögzítve!", icon="⚡")
                time.sleep(0.8)
                st.rerun()

    elif alb_al_nezet == "📜 Napló":
        alb_osszes_df = df[
            alb_penz_maszk | (df["Kategória"] == "Albérlet: Óraállás")
        ].iloc[::-1].copy()

        if alb_osszes_df.empty:
            st.info("Még nincs rögzített albérleti tétel.")
        else:
            megerositendo_alb_sor = st.session_state.get("torles_megerosites_sor")
            for _, r in alb_osszes_df.head(20).iterrows():
                sor_id = int(r["Sheet_Row"])
                kat_nyers = str(r["Kategória"])
                aktiv = (megerositendo_alb_sor == sor_id)
                is_ora = (kat_nyers == "Albérlet: Óraállás")

                card_cls = "tx-item tx-hitel" if is_ora else "tx-item tx-alb"
                if aktiv:
                    card_cls += " tx-del"
                val_color = "#7dd3fc" if is_ora else "#d8b4fe"
                ertek_szoveg = f"{fmt_ft(r['Összeg'])}" if is_ora else f"−{fmt_ft(r['Összeg'])} Ft"
                jelveny = "Óraállás" if is_ora else ("Kasszából" if kat_nyers == "Lakhatás & Rezsi" else "Csak napló")

                c_card, c_act = st.columns([5.2, 1.1], vertical_alignment="center")
                with c_card:
                    st.markdown(
                        f'<div class="{card_cls}"><div style="min-width:0;"><div class="tx-name">{r["Megnevezés"]}</div><div class="tx-sub"><span class="tx-tag">{jelveny}</span><span>{r["Ki"]}</span><span>• {r["Dátum"]}</span></div></div><div class="tx-val" style="color:{val_color};">{ertek_szoveg}</div></div>',
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if not aktiv:
                        if st.button("🗑️", key=f"alb_del_{sor_id}", use_container_width=True):
                            st.session_state["torles_megerosites_sor"] = sor_id
                            st.rerun()
                    else:
                        if st.button("✅", key=f"alb_conf_{sor_id}", type="primary", use_container_width=True):
                            with st.spinner("Törlés..."):
                                sheet.delete_rows(sor_id)
                            st.session_state["torles_megerosites_sor"] = None
                            adatok_betoltese.clear()
                            hangeffekt("torles")
                            st.toast("Törölve!", icon="🗑️")
                            time.sleep(0.5)
                            st.rerun()

    elif alb_al_nezet == "⚙️ Adatok":
        uj_berleti_dij = osszeg_mezo("Havi bérleti díj (Ft)", key="beall_berleti_dij", alap_ertek=alap_berleti_dij)
        uj_kaucio = osszeg_mezo("Letett kaució (Ft)", key="beall_kaucio", alap_ertek=alap_kaucio)
        uj_fiz_nap = st.number_input("Fizetési határnap (hónap napja)", min_value=1, max_value=31, value=int(alap_fizetesi_nap), key="beall_fiz_nap")
        uj_foberlo = st.text_input("Főbérlő neve / tel / számlaszám", value=alap_foberlo, key="beall_fob").strip()
        uj_megj = st.text_input("Megjegyzés (cím, szerződés)", value=alap_megjegyzes, key="beall_megj").strip()

        if st.button("💾 Lakás adatainak mentése", use_container_width=True, type="primary"):
            meta_str = f"Albérlet adatok | kaucio:{int(uj_kaucio)} | nap:{int(uj_fiz_nap)} | foberlo:{uj_foberlo} | megj:{uj_megj}"
            with st.spinner("Mentés..."):
                sheet.append_row([str(date.today()), "Zsolt", "Albérlet: Beállítás", meta_str, int(uj_berleti_dij)])
            adatok_betoltese.clear()
            hangeffekt("siker")
            st.toast("Albérlet adatai frissítve!", icon="🏡")
            time.sleep(0.8)
            st.rerun()

# ==============================================================================
# 4. NÉZET: HITEL
# ==============================================================================
elif aktiv_oldal == "hitel":
    hitel_keretek = df[df["Kategória"] == "Hitel: Keret"].copy()
    hitel_torlesztesek = df[df["Kategória"] == "Hitel: Törlesztés"].copy()

    if hitel_keretek.empty:
        st.info("Még nincs beállított hitel.")
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

            st.markdown(
                f'<div class="glass-card"><div class="glass-header"><span>🏦 {h_nev}</span><span>{szazalek*100:.1f}%</span></div><div class="kpi-two-grid"><div class="kpi-mini-box"><div class="kpi-lbl">Hátralévő tartozás</div><div class="kpi-val" style="color:#fbbf24;">{fmt_ft(hatralevo)} Ft</div></div><div class="kpi-mini-box"><div class="kpi-lbl">E havi ({HONAP_NEVEK[ma.month - 1]})</div><div class="kpi-val" style="color:#34d399;">{fmt_ft(e_havi_levonas)} Ft</div></div></div><div style="font-size:0.72rem; color:#94a3b8; margin-top:8px;">🗓️ {kezdo_datum_str} → {vege_datum_str or "folyamatban"} • Kifizetve: {fmt_ft(eddig_kifizetve)} / {fmt_ft(teljes_osszeg)} Ft</div></div>',
                unsafe_allow_html=True,
            )
            st.progress(szazalek)

        with st.expander("💸 Törlesztés / levonás rögzítése", expanded=True):
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

            c_h1, c_h2 = st.columns([1.3, 1])
            with c_h1:
                levont_osszeg = osszeg_mezo("Összeg (Ft)", key="hitel_levonas_osszeg", alap_ertek=alap_torleszto)
            with c_h2:
                levonas_datum = st.date_input("Dátum", value=date.today(), key="hitel_levonas_datum")

            if st.button("✅ Levonás rögzítése", use_container_width=True, type="primary"):
                if levont_osszeg <= 0:
                    hangeffekt("hiba")
                    st.warning("Adj meg 0-nál nagyobb összeget!")
                else:
                    with st.spinner("Rögzítés..."):
                        sheet.append_row([str(levonas_datum), "Zsolt", "Hitel: Törlesztés", f"{valasztott_hitel} – törlesztés", int(levont_osszeg)])
                    adatok_betoltese.clear()
                    hangeffekt("siker")
                    st.toast("Levonás rögzítve!", icon="🏦")
                    time.sleep(0.8)
                    st.rerun()

    with st.expander("⚙️ Új hitel felvétele"):
        uj_hitel_nev = st.text_input("Hitel neve").strip()
        d_col1, d_col2 = st.columns(2)
        uj_hitel_kezdet = d_col1.date_input("Kezdet", value=date.today(), key="uj_hitel_kezdet")
        uj_hitel_vege = d_col2.date_input("Lejárat", value=date.today() + timedelta(days=365), key="uj_hitel_vege")
        uj_hitel_teljes = osszeg_mezo("Teljes összeg (Ft)", key="uj_hitel_teljes")
        uj_hitel_jelenlegi = osszeg_mezo("Jelenlegi tartozás (Ft)", key="uj_hitel_jelenlegi")
        uj_hitel_havi = osszeg_mezo("Havi törlesztő (Ft)", key="uj_hitel_havi")
        if st.button("💾 Hitel mentése", use_container_width=True):
            if not uj_hitel_nev or uj_hitel_teljes <= 0:
                hangeffekt("hiba")
                st.warning("Add meg a hitel nevét és a teljes összeget!")
            elif uj_hitel_jelenlegi > uj_hitel_teljes:
                hangeffekt("hiba")
                st.warning("A jelenlegi tartozás nem lehet nagyobb!")
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
                st.toast("Hitel létrehozva!", icon="🏦")
                time.sleep(0.8)
                st.rerun()

# ==============================================================================
# 5. NÉZET: ELŐZMÉNYEK / NAPLÓ
# ==============================================================================
elif aktiv_oldal == "lista":
    if df.empty:
        st.info("Még nincs rögzített tétel.")
    else:
        szekcio_tipus = st.pills(
            "Típus",
            ["Összes", "➖ Kiadások", "➕ Bevételek", "🏠 Albérlet", "💸 Tartozások", "🏦 Hitelek"],
            default="Összes",
            key="elozmenyek_tipus_szuro",
            label_visibility="collapsed",
        ) or "Összes"

        szurt_df = df.iloc[::-1].copy()
        if szekcio_tipus == "➖ Kiadások":
            szurt_df = szurt_df[(~szurt_df["Kategória"].str.startswith("Bevétel:", na=False)) & (~szurt_df["Kategória"].isin(KIZART_KATEGORIAK))]
        elif szekcio_tipus == "➕ Bevételek":
            szurt_df = szurt_df[szurt_df["Kategória"].str.startswith("Bevétel:", na=False)]
        elif szekcio_tipus == "🏠 Albérlet":
            szurt_df = szurt_df[
                (szurt_df["Kategória"] == "Lakhatás & Rezsi")
                | (szurt_df["Kategória"].str.startswith("Albérlet:", na=False))
                | (szurt_df["Megnevezés"].astype(str).str.startswith("Albérlet:", na=False))
            ]
        elif szekcio_tipus == "💸 Tartozások":
            szurt_df = szurt_df[szurt_df["Kategória"] == "Tartozás"]
        elif szekcio_tipus == "🏦 Hitelek":
            szurt_df = szurt_df[szurt_df["Kategória"].isin(["Hitel: Keret", "Hitel: Törlesztés"])]

        c_search, c_ref = st.columns([4.5, 1], vertical_alignment="center")
        with c_search:
            kereso = st.text_input(
                "Keresés",
                placeholder="🔍 Keresés név, kategória, dátum...",
                key="elozmenyek_kereso",
                label_visibility="collapsed",
            ).strip().lower()
        with c_ref:
            if st.button("🔄", use_container_width=True, help="Frissítés"):
                adatok_betoltese.clear()
                hangeffekt("frissites")
                st.toast("Frissítve!", icon="🔄")
                time.sleep(0.3)
                st.rerun()

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
        st.caption(f"📋 **{talalat_db} tétel** • Összesen: **{fmt_ft(talalat_osszeg)} Ft**")

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
                    card_cls, val_color, elojel = "tx-item tx-bev", "#34d399", "+"
                    kat_cimke = kat_nyers.replace("Bevétel: ", "")
                elif kat_nyers.startswith("Hitel:"):
                    card_cls, val_color, elojel = "tx-item tx-hitel", "#7dd3fc", ""
                    kat_cimke = kat_nyers.replace("Hitel: ", "Hitel • ")
                elif kat_nyers.startswith("Albérlet:"):
                    card_cls, val_color, elojel = "tx-item tx-alb", "#d8b4fe", ""
                    kat_cimke = kat_nyers.replace("Albérlet: ", "Albérlet • ")
                elif kat_nyers == "Tartozás":
                    card_cls, val_color, elojel = "tx-item tx-tart", "#fda4af", ""
                    kat_cimke = "Tartozás"
                else:
                    card_cls, val_color, elojel = "tx-item", "#fbbf24", "−"
                    kat_cimke = kat_nyers

                if aktiv:
                    card_cls += " tx-del"

                nev_tiszta = str(r["Megnevezés"]).split("|")[0].strip()

                c_card, c_act = st.columns([5.2, 1.05], vertical_alignment="center")
                with c_card:
                    st.markdown(
                        f'<div class="{card_cls}"><div style="min-width:0;"><div class="tx-name">{nev_tiszta}</div><div class="tx-sub"><span class="tx-tag">{kat_cimke}</span><span>{r["Ki"]}</span><span>• {r["Dátum"]}</span></div></div><div class="tx-val" style="color:{val_color};">{elojel}{fmt_ft(r["Összeg"])} Ft</div></div>',
                        unsafe_allow_html=True,
                    )
                with c_act:
                    if not aktiv:
                        if st.button("🗑️", key=f"del_btn_{sor_id}", use_container_width=True):
                            st.session_state["torles_megerosites_sor"] = sor_id
                            st.rerun()
                    else:
                        if st.button("✅", key=f"conf_del_{sor_id}", type="primary", use_container_width=True):
                            with st.spinner("Törlés..."):
                                sheet.delete_rows(sor_id)
                            st.session_state["torles_megerosites_sor"] = None
                            adatok_betoltese.clear()
                            hangeffekt("torles")
                            st.toast("Törölve!", icon="🗑️")
                            time.sleep(0.4)
                            st.rerun()

# ==============================================================================
# FIX ALSÓ MOBIL NAVIGÁCIÓS SÁV
# ==============================================================================
nav_elemek = [
    ("uj", "🍁", "Új tétel"),
    ("stat", "📊", "Statisztika"),
    ("alb", "🏠", "Albérlet"),
    ("hitel", "🏦", "Hitel"),
    ("lista", "📜", "Napló"),
]
nav_links_html = ""
for key, ico, lbl in nav_elemek:
    akt_cls = "nav-item active" if aktiv_oldal == key else "nav-item"
    nav_links_html += f'<a class="{akt_cls}" href="?nav={key}" target="_self"><span class="nav-item-ico">{ico}</span><span>{lbl}</span></a>'

st.markdown(
    f'<div class="bottom-nav-wrap"><nav class="bottom-nav-bar">{nav_links_html}</nav></div>',
    unsafe_allow_html=True,
)
