import os
from datetime import date
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd

# Megjelenés beállítása
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FAJLNEV = "kiadasok_asztali.csv"
KATEGORIAK = [
    "Élelmiszer & Háztartás",
    "Üzemanyag & Autó",
    "Lakhatás & Rezsi",
    "Szórakozás & Étterem",
    "Tech & Vásárlás",
    "Előfizetések",
    "Egyéb",
]

class KiadaskovetoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Személyes Kiadáskövető & Statisztika v2.0")
        self.geometry("920x620")
        self.resizable(False, False)

        self.df = self.adatok_betoltese()

        # --- BAL OLDALI PANEL (Bevitel) ---
        self.bal_panel = ctk.CTkFrame(self, width=260, corner_radius=10)
        self.bal_panel.pack(side="left", fill="y", padx=15, pady=15)

        ctk.CTkLabel(self.bal_panel, text="➕ Új tétel", font=("Segoe UI", 20, "bold")).pack(pady=(20, 15))

        ctk.CTkLabel(self.bal_panel, text="Kategória:", anchor="w").pack(fill="x", padx=20)
        self.kat_menu = ctk.CTkOptionMenu(self.bal_panel, values=KATEGORIAK)
        self.kat_menu.pack(fill="x", padx=20, pady=(2, 12))

        ctk.CTkLabel(self.bal_panel, text="Megnevezés:", anchor="w").pack(fill="x", padx=20)
        self.nev_mezo = ctk.CTkEntry(self.bal_panel, placeholder_text="pl. Tankolás, Bevásárlás")
        self.nev_mezo.pack(fill="x", padx=20, pady=(2, 12))

        ctk.CTkLabel(self.bal_panel, text="Összeg (Ft):", anchor="w").pack(fill="x", padx=20)
        self.osszeg_mezo = ctk.CTkEntry(self.bal_panel, placeholder_text="pl. 15000")
        self.osszeg_mezo.pack(fill="x", padx=20, pady=(2, 20))

        self.hozzaad_gomb = ctk.CTkButton(
            self.bal_panel, text="Rögzítés", font=("Segoe UI", 14, "bold"),
            height=40, command=self.tetel_hozzaadasa
        )
        self.hozzaad_gomb.pack(fill="x", padx=20, pady=5)

        self.hiba_cimke = ctk.CTkLabel(self.bal_panel, text="", text_color="#FF5555", wraplength=220)
        self.hiba_cimke.pack(pady=10)

        # --- JOBB OLDALI PANEL (Kártyák + Lapozófülek) ---
        self.jobb_panel = ctk.CTkFrame(self, corner_radius=10)
        self.jobb_panel.pack(side="right", fill="both", expand=True, padx=(0, 15), pady=15)

        # 3 Statisztikai kártya felül
        self.kartya_sor = ctk.CTkFrame(self.jobb_panel, fg_color="transparent")
        self.kartya_sor.pack(fill="x", padx=15, pady=(15, 5))

        self.osszes_cimke = self.kartya_letrehozasa(self.kartya_sor, "Összes kiadás", "0 Ft", "#1f538d")
        self.max_cimke = self.kartya_letrehozasa(self.kartya_sor, "Legnagyobb tétel", "0 Ft", "#2b5b4c")
        self.db_cimke = self.kartya_letrehozasa(self.kartya_sor, "Rögzített tételek", "0 db", "#5b3a5b")

        # Lapozófülek (Lista vs. Grafikonok)
        self.tabview = ctk.CTkTabview(self.jobb_panel)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.tab_lista = self.tabview.add("📝 Tételek listája")
        self.tab_stat = self.tabview.add("📊 Grafikon & Kategóriák")

        # 1. Fül: Görgethető lista
        self.lista_keret = ctk.CTkScrollableFrame(self.tab_lista)
        self.lista_keret.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. Fül: Statisztika és kördiagram keret
        self.stat_keret = ctk.CTkFrame(self.tab_stat, fg_color="transparent")
        self.stat_keret.pack(fill="both", expand=True)

        self.felulet_frissitese()

    def kartya_letrehozasa(self, szulo, cim, alap_ertek, szin):
        keret = ctk.CTkFrame(szulo, fg_color=szin, corner_radius=8)
        keret.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(keret, text=cim, font=("Segoe UI", 12), text_color="#dddddd").pack(pady=(8, 0))
        ertek_cimke = ctk.CTkLabel(keret, text=alap_ertek, font=("Segoe UI", 18, "bold"), text_color="white")
        ertek_cimke.pack(pady=(2, 10))
        return ertek_cimke

    def adatok_betoltese(self):
        if os.path.exists(FAJLNEV):
            return pd.read_csv(FAJLNEV)
        return pd.DataFrame(columns=["Dátum", "Kategória", "Megnevezés", "Összeg"])

    def adatok_mentese(self):
        self.df.to_csv(FAJLNEV, index=False)

    def tetel_hozzaadasa(self):
        nev = self.nev_mezo.get().strip()
        osszeg_szoveg = self.osszeg_mezo.get().strip()
        kat = self.kat_menu.get()

        if not nev or not osszeg_szoveg.isdigit() or int(osszeg_szoveg) <= 0:
            self.hiba_cimke.configure(text="Adj meg nevet és pozitív számot!")
            return

        self.hiba_cimke.configure(text="")
        uj_sor = pd.DataFrame([{
            "Dátum": str(date.today()),
            "Kategória": kat,
            "Megnevezés": nev,
            "Összeg": int(osszeg_szoveg)
        }])
        self.df = pd.concat([self.df, uj_sor], ignore_index=True)
        self.adatok_mentese()

        self.nev_mezo.delete(0, "end")
        self.osszeg_mezo.delete(0, "end")
        self.felulet_frissitese()

    def tetel_torlese(self, index):
        self.df = self.df.drop(index=index).reset_index(drop=True)
        self.adatok_mentese()
        self.felulet_frissitese()

    def felulet_frissitese(self):
        # Kártyák frissítése
        if self.df.empty:
            self.osszes_cimke.configure(text="0 Ft")
            self.max_cimke.configure(text="0 Ft")
            self.db_cimke.configure(text="0 db")
        else:
            osszes = self.df["Összeg"].sum()
            legnagyobb = self.df["Összeg"].max()
            db = len(self.df)
            self.osszes_cimke.configure(text=f"{osszes:,.0f} Ft".replace(",", " "))
            self.max_cimke.configure(text=f"{legnagyobb:,.0f} Ft".replace(",", " "))
            self.db_cimke.configure(text=f"{db} db")

        # Lista újrarajzolása
        for widget in self.lista_keret.winfo_children():
            widget.destroy()

        for idx, sor in self.df.iloc[::-1].iterrows():
            sor_keret = ctk.CTkFrame(self.lista_keret)
            sor_keret.pack(fill="x", pady=4)

            szoveg = f"{sor['Dátum']}  |  [{sor['Kategória']}]  {sor['Megnevezés']}  —  {sor['Összeg']:,} Ft".replace(",", " ")
            ctk.CTkLabel(sor_keret, text=szoveg, font=("Segoe UI", 13)).pack(side="left", padx=10, pady=8)

            torles_gomb = ctk.CTkButton(
                sor_keret, text="X", width=30, height=26,
                fg_color="#aa3333", hover_color="#882222",
                command=lambda i=idx: self.tetel_torlese(i)
            )
            torles_gomb.pack(side="right", padx=8)

        # Statisztika és kördiagram újrarajzolása
        self.grafikon_frissitese()

    def grafikon_frissitese(self):
        for widget in self.stat_keret.winfo_children():
            widget.destroy()

        if self.df.empty:
            ctk.CTkLabel(
                self.stat_keret, text="Adj hozzá legalább egy tételt a grafikon megjelenítéséhez!",
                font=("Segoe UI", 14), text_color="#aaaaaa"
            ).pack(pady=60)
            return

        kat_osszeg = self.df.groupby("Kategória")["Összeg"].sum().sort_values(ascending=False)

        # Bal oldal: Kördiagram (Matplotlib)
        bal_graf = ctk.CTkFrame(self.stat_keret, fg_color="#2b2b2b", corner_radius=8)
        bal_graf.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=5)

        fig, ax = plt.subplots(figsize=(4.2, 3.6), dpi=100)
        fig.patch.set_facecolor("#2b2b2b")
        ax.set_facecolor("#2b2b2b")

        szinek = ["#3b8ed0", "#2fa572", "#e07a5f", "#f2cc8f", "#9b5de5", "#00bbf9", "#8d99ae"]
        wedges, texts, autotexts = ax.pie(
            kat_osszeg.values,
            autopct="%1.0f%%",
            startangle=140,
            colors=szinek[:len(kat_osszeg)],
            pctdistance=0.78,
            wedgeprops=dict(width=0.45, edgecolor="#2b2b2b", linewidth=2),
            textprops=dict(color="white", fontweight="bold", fontsize=9)
        )
        ax.set_title("Megoszlás (%)", color="white", fontsize=12, fontweight="bold", pad=10)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=bal_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

        # Jobb oldal: Kategóriánkénti bontás lista
        jobb_bontas = ctk.CTkScrollableFrame(self.stat_keret, fg_color="#2b2b2b", corner_radius=8)
        jobb_bontas.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=5)

        ctk.CTkLabel(
            jobb_bontas, text="Kategóriák összesítve:", font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 8))

        for i, (kat, ossz) in enumerate(kat_osszeg.items()):
            szin = szinek[i % len(szinek)]
            sor = ctk.CTkFrame(jobb_bontas, fg_color="#363636")
            sor.pack(fill="x", padx=8, pady=4)

            jelolo = ctk.CTkLabel(sor, text="●", text_color=szin, font=("Segoe UI", 16))
            jelolo.pack(side="left", padx=(8, 4))

            ctk.CTkLabel(sor, text=kat, font=("Segoe UI", 12)).pack(side="left", pady=6)
            ctk.CTkLabel(
                sor, text=f"{ossz:,.0f} Ft".replace(",", " "),
                font=("Segoe UI", 12, "bold"), text_color="#66ccff"
            ).pack(side="right", padx=10)

if __name__ == "__main__":
    app = KiadaskovetoApp()
    app.mainloop()