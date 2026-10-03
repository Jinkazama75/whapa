#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
whapa-gui.py - Interfaccia grafica moderna per WhaPa (CustomTkinter)
Traduzione completa in Italiano ed interfaccia ridisegnata.

Autore originale: Ivan Moreno a.k.a B16f00t
Edizione Italiana & Aggiornamenti: Jinkazama75
"""

import os
import sys
import queue
import shlex
import threading
import subprocess
import webbrowser
from configparser import ConfigParser

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError:
    sys.exit("Libreria mancante: customtkinter. Installala con: pip install customtkinter")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LIBS = os.path.join(APP_DIR, "libs")
VERSION = "2.0.1"

# ===========================================================================
#  Palette colori moderna (WhatsApp Dark Mode / Modern Slate)
# ===========================================================================
ACCENT = "#25D366"          # Verde brillante WhatsApp
ACCENT_HOVER = "#1EBE5D"    # Verde hover
ACCENT_MUTED = "#0F3E2E"    # Sfondo verde scuro per badge / pillole
BG = "#0B141A"              # Sfondo principale scuro
PANEL = "#111B21"           # Sfondo schede e riquadri
PANEL_BORDER = "#1F2C34"    # Bordo delicato
FIELD = "#202C33"           # Sfondo campi di inserimento
FIELD_BORDER = "#2A3942"    # Bordo campi di input
TEXT = "#E9EDEF"            # Testo principale bianco/argento
MUTED = "#8696A0"           # Testo secondario grigio
ERROR = "#F15C6D"           # Rosso chiaro per errori / alert
BUTTON_SEC = "#202C33"      # Pulsanti secondari
BUTTON_SEC_HOVER = "#2A3942"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
F10 = dict(family=FONT_FAMILY, size=10)
F11 = dict(family=FONT_FAMILY, size=11)
F11_BOLD = dict(family=FONT_FAMILY, size=11, weight="bold")
F12 = dict(family=FONT_FAMILY, size=12)
F12_BOLD = dict(family=FONT_FAMILY, size=12, weight="bold")
F13_BOLD = dict(family=FONT_FAMILY, size=13, weight="bold")

if sys.platform.startswith("win"):
    import winreg


def tool(name):
    return os.path.join(LIBS, name)


def get_installed_browsers():
    """Rileva automaticamente i browser installati sul PC."""
    browsers = {"🌐 Predefinito di Sistema": ""}

    if sys.platform.startswith("win"):
        # 1. Ricerca nel Registro di Windows (HKCU e HKLM StartMenuInternet)
        hives = [
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Clients\StartMenuInternet"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Clients\StartMenuInternet"),
        ]
        for hive, subkey in hives:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        name = winreg.EnumKey(key, i)
                        try:
                            cmd_path = f"{subkey}\\{name}\\shell\\open\\command"
                            with winreg.OpenKey(hive, cmd_path) as cmd_key:
                                cmd_val, _ = winreg.QueryValue(cmd_key, "")
                                exe_path = cmd_val.strip()
                                if exe_path.startswith('"'):
                                    exe_path = exe_path[1:].split('"')[0]
                                else:
                                    exe_path = exe_path.split(" ")[0]

                                if os.path.isfile(exe_path):
                                    display_name = name
                                    try:
                                        with winreg.OpenKey(hive, f"{subkey}\\{name}") as n_key:
                                            d_val, _ = winreg.QueryValue(n_key, "")
                                            if d_val:
                                                display_name = d_val
                                    except Exception:
                                        pass
                                    browsers[display_name] = exe_path
                        except Exception:
                            pass
            except Exception:
                pass

        # 2. Controllo dei percorsi standard noti su disco
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app_data = os.environ.get("LocalAppData", "")

        check_paths = [
            ("Mozilla Firefox", os.path.join(program_files, "Mozilla Firefox", "firefox.exe")),
            ("Mozilla Firefox", os.path.join(program_files_x86, "Mozilla Firefox", "firefox.exe")),
            ("Google Chrome", os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe")),
            ("Google Chrome", os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe")),
            ("Google Chrome", os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe")),
            ("Microsoft Edge", os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe")),
            ("Microsoft Edge", os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe")),
            ("Brave", os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", "brave.exe")),
            ("Brave", os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "Application", "brave.exe")),
            ("Opera", os.path.join(local_app_data, "Programs", "Opera", "launcher.exe")),
            ("Opera GX", os.path.join(local_app_data, "Programs", "Opera GX", "launcher.exe")),
            ("Vivaldi", os.path.join(local_app_data, "Vivaldi", "Application", "vivaldi.exe")),
        ]

        for name, path in check_paths:
            if path and os.path.isfile(path) and name not in browsers:
                browsers[name] = path

    return browsers


class Field:
    """Campo di testo con placeholder e interfaccia .get() / .set()."""

    def __init__(self, value=""):
        self._widget = None
        self._value = value

    def attach(self, widget):
        self._widget = widget
        if self._value:
            widget.insert(0, self._value)

    def get(self):
        if self._widget is not None:
            try:
                return self._widget.get()
            except Exception:
                pass
        return self._value

    def set(self, valor):
        self._value = valor or ""
        if self._widget is None:
            return
        try:
            self._widget.delete(0, "end")
            if valor:
                self._widget.insert(0, valor)
            else:
                self._widget._activate_placeholder()
        except Exception:
            pass


class Row:
    """Helper per disporre i controlli a griglia all'interno di una scheda."""

    def __init__(self, master):
        self.m = master
        self.r = 0
        master.grid_columnconfigure(1, weight=1)

    def file(self, label, var, title, types=None, save=False, folder=False, hint=None):
        ctk.CTkLabel(self.m, text=label, text_color=TEXT, anchor="w",
                     font=ctk.CTkFont(**F12)).grid(row=self.r, column=0, sticky="w",
                                                   padx=(14, 8), pady=5)
        e = ctk.CTkEntry(self.m, fg_color=FIELD, border_color=FIELD_BORDER, border_width=1,
                         corner_radius=8, placeholder_text=hint or "", font=ctk.CTkFont(**F12))
        e.grid(row=self.r, column=1, columnspan=2, sticky="ew", pady=5, padx=(0, 8))
        var.attach(e)

        def pick():
            if folder:
                p = filedialog.askdirectory(title=title)
            elif save:
                p = filedialog.asksaveasfilename(title=title, filetypes=types or [("Tutti i file", "*.*")])
            else:
                p = filedialog.askopenfilename(title=title, filetypes=types or [("Tutti i file", "*.*")])
            if p:
                var.set(p)

        ctk.CTkButton(self.m, text="📁 Sfoglia", width=95, command=pick,
                      fg_color=BUTTON_SEC, hover_color=BUTTON_SEC_HOVER,
                      corner_radius=8, font=ctk.CTkFont(**F11)
                      ).grid(row=self.r, column=3, padx=(0, 14), pady=5)
        self.r += 1

    def entry(self, label, var, placeholder="", width=240):
        ctk.CTkLabel(self.m, text=label, text_color=TEXT, anchor="w",
                     font=ctk.CTkFont(**F12)).grid(row=self.r, column=0, sticky="w",
                                                   padx=(14, 8), pady=5)
        e = ctk.CTkEntry(self.m, fg_color=FIELD, border_color=FIELD_BORDER, border_width=1,
                         corner_radius=8, placeholder_text=placeholder, width=width,
                         font=ctk.CTkFont(**F12))
        e.grid(row=self.r, column=1, sticky="w", pady=5)
        var.attach(e)
        self.r += 1

    def options(self, label, var, values, width=220):
        ctk.CTkLabel(self.m, text=label, text_color=TEXT, anchor="w",
                     font=ctk.CTkFont(**F12)).grid(row=self.r, column=0, sticky="w",
                                                   padx=(14, 8), pady=5)
        ctk.CTkOptionMenu(self.m, variable=var, values=values, width=width,
                          fg_color=FIELD, button_color=BUTTON_SEC_HOVER,
                          button_hover_color=ACCENT_HOVER,
                          corner_radius=8, font=ctk.CTkFont(**F12),
                          dropdown_font=ctk.CTkFont(**F12)
                          ).grid(row=self.r, column=1, sticky="w", pady=5)
        self.r += 1

    def checks(self, items, cols=5, label=None):
        if label:
            ctk.CTkLabel(self.m, text=label, text_color=MUTED, anchor="w",
                         font=ctk.CTkFont(**F10)).grid(row=self.r, column=0,
                                                       columnspan=4, sticky="w",
                                                       padx=14, pady=(10, 2))
            self.r += 1
        box = ctk.CTkFrame(self.m, fg_color="transparent")
        box.grid(row=self.r, column=0, columnspan=4, sticky="w", padx=12, pady=3)
        for i, (var, txt) in enumerate(items):
            ctk.CTkCheckBox(box, text=txt, variable=var, text_color=TEXT,
                            fg_color=ACCENT, hover_color=ACCENT_HOVER,
                            corner_radius=5, checkbox_width=17, checkbox_height=17,
                            font=ctk.CTkFont(**F11)
                            ).grid(row=i // cols, column=i % cols, sticky="w",
                                   padx=8, pady=3)
        self.r += 1

    def section(self, text):
        ctk.CTkLabel(self.m, text=text, text_color=ACCENT,
                     font=ctk.CTkFont(**F12_BOLD)
                     ).grid(row=self.r, column=0, columnspan=4, sticky="w",
                            padx=14, pady=(14, 4))
        self.r += 1

    def run(self, text, command):
        b = ctk.CTkButton(self.m, text=text, command=command, width=220, height=36,
                          fg_color=ACCENT, hover_color=ACCENT_HOVER,
                          text_color="#0B141A", corner_radius=10,
                          font=ctk.CTkFont(**F13_BOLD))
        b.grid(row=self.r, column=0, columnspan=2, sticky="w", padx=14, pady=16)
        self.r += 1
        return b


class SettingsDialog(ctk.CTkToplevel):
    """Finestra di configurazione: dati del report e credenziali Google/iCloud."""

    CAMPOS = [
        ("report", "company",   "Organizzazione / Studio"),
        ("report", "record",    "Codice Riferimento / Fascicolo"),
        ("report", "unit",      "Unità / Reparto"),
        ("report", "examiner",  "Operatore / Analista"),
        ("report", "notes",     "Note Aggiuntive"),
        ("google-auth", "gmail",      "Indirizzo Gmail"),
        ("google-auth", "oauth",      "Token OAuth / Master Token (da EmbeddedSetup)"),
        ("google-auth", "celnumbr",   "Numero Telefono (es. 393401234567)"),
        ("google-auth", "password",   "Password Google (opzionale / per app)"),
        ("google-auth", "android_id", "Android ID (predefinito se non noto)"),
        ("icloud-auth", "icloud", "Account Apple iCloud"),
        ("icloud-auth", "passw",  "Password iCloud"),
    ]
    SECCIONI = {
        "report": "📋 Dati del Report Forense",
        "google-auth": "☁️ Autenticazione Google Drive (WhatsApp Android)",
        "icloud-auth": "🍏 Autenticazione iCloud (WhatsApp iOS)",
    }

    def __init__(self, master):
        super().__init__(master)
        self.master_gui = master
        self.title("Configurazione & Credenziali - WhaPa")
        self.geometry("680x660")
        self.configure(fg_color=BG)
        self.transient(master)
        self.ruta = os.path.join(APP_DIR, "cfg", "settings.cfg")
        self.vars = {}
        self._build()
        self.after(120, self.grab_set)

    def _build(self):
        sc = ctk.CTkScrollableFrame(self, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=16, pady=16)
        sc.grid_columnconfigure(1, weight=1)

        cfg = ConfigParser()
        if os.path.exists(self.ruta):
            try:
                cfg.read(self.ruta, encoding="utf-8")
            except Exception:
                pass

        fila = 0
        seccion_actual = None
        for sec, clave, etiqueta in self.CAMPOS:
            if sec != seccion_actual:
                seccion_actual = sec
                ctk.CTkLabel(sc, text=self.SECCIONI[sec], text_color=ACCENT,
                             font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")
                             ).grid(row=fila, column=0, columnspan=2, sticky="w",
                                    pady=(16, 6))
                fila += 1
            valor = ""
            if cfg.has_option(sec, clave):
                valor = cfg.get(sec, clave).strip().strip('"')
            var = ctk.StringVar(value=valor)
            self.vars[(sec, clave)] = var
            ctk.CTkLabel(sc, text=etiqueta, text_color=TEXT, anchor="w",
                         font=ctk.CTkFont(**F12)).grid(row=fila, column=0,
                                                       sticky="w", padx=(0, 10), pady=4)
            oculta = "*" if clave in ("password", "passw") else ""
            ctk.CTkEntry(sc, textvariable=var, fg_color=FIELD, border_color=FIELD_BORDER,
                         border_width=1, corner_radius=8, show=oculta, width=350,
                         font=ctk.CTkFont(**F12)).grid(row=fila, column=1,
                                                      sticky="ew", pady=4)
            fila += 1

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(barra, text="💾 Salva Impostazioni", command=self._save, width=160, height=36,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      text_color="#0B141A", corner_radius=8,
                      font=ctk.CTkFont(**F13_BOLD)).pack(side="right")
        ctk.CTkButton(barra, text="Annulla", command=self.destroy, width=100, height=36,
                      fg_color=BUTTON_SEC, hover_color=BUTTON_SEC_HOVER,
                      corner_radius=8, font=ctk.CTkFont(**F12)).pack(side="right", padx=10)
        ctk.CTkLabel(barra, text="Salvataggio in: cfg/settings.cfg", text_color=MUTED,
                     font=ctk.CTkFont(**F10)).pack(side="left")

    def _save(self):
        cfg = ConfigParser()
        if os.path.exists(self.ruta):
            try:
                cfg.read(self.ruta, encoding="utf-8")
            except Exception:
                pass
        for (sec, clave), var in self.vars.items():
            if not cfg.has_section(sec):
                cfg.add_section(sec)
            valor = var.get()
            if sec == "report":
                valor = '"{}"'.format(valor.replace('"', ""))
            cfg.set(sec, clave, valor)
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as fh:
                cfg.write(fh)
            self.master_gui._emit("[-] Impostazioni salvate con successo in cfg/settings.cfg", "ok")
            self.destroy()
        except OSError as e:
            messagebox.showerror("WhaPa", f"Errore durante il salvataggio: {e}")


class WhapaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"WhaPa v{VERSION} - Suite Forense & Backup WhatsApp")
        try:
            _sw, _sh = self.winfo_screenwidth(), self.winfo_screenheight()
        except Exception:
            _sw, _sh = 1280, 800
        self.geometry(f"{min(1100, _sw - 20)}x{min(880, _sh - 80)}")
        self.minsize(min(920, _sw - 40), min(660, _sh - 100))
        self.configure(fg_color=BG)
        self.q = queue.Queue()
        self.busy = False
        self.buttons = []

        # Rilevamento automatico browser installati
        self.installed_browsers = get_installed_browsers()
        saved_browser = ""
        cfg_path = os.path.join(APP_DIR, "cfg", "settings.cfg")
        if os.path.exists(cfg_path):
            try:
                cfg = ConfigParser()
                cfg.read(cfg_path, encoding="utf-8")
                if cfg.has_option("gui", "browser"):
                    saved_browser = cfg.get("gui", "browser").strip()
            except Exception:
                pass

        default_browser = saved_browser if saved_browser in self.installed_browsers else (
            "Mozilla Firefox" if "Mozilla Firefox" in self.installed_browsers else list(self.installed_browsers.keys())[0]
        )
        self.selected_browser = ctk.StringVar(value=default_browser)

        self._set_icon()
        self._build()
        self.after(10, self._maximizar)
        self.after(100, self._drain)

    def _maximizar(self):
        for metodo in (lambda: self.state("zoomed"),
                       lambda: self.attributes("-zoomed", True)):
            try:
                metodo()
                self.update_idletasks()
                if self.state() == "zoomed":
                    return
            except Exception:
                continue

    def _set_icon(self):
        ico = os.path.join(APP_DIR, "images", "logo.ico")
        png = os.path.join(APP_DIR, "images", "logo.png")
        try:
            if sys.platform.startswith("win") and os.path.exists(ico):
                self.iconbitmap(ico)
            elif os.path.exists(png):
                import tkinter as tk
                self._icon_img = tk.PhotoImage(file=png)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, minsize=220)

        # Intestazione superiore moderna
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))

        # Brand / Titolo
        brand_box = ctk.CTkFrame(head, fg_color="transparent")
        brand_box.pack(side="left")

        ctk.CTkLabel(brand_box, text="💬 WhaPa", text_color=ACCENT,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold")).pack(side="left")

        badge = ctk.CTkFrame(brand_box, fg_color=ACCENT_MUTED, corner_radius=12)
        badge.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(badge, text=f"v{VERSION} • Italiano", text_color=ACCENT,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold")).pack(padx=8, pady=2)

        ctk.CTkLabel(brand_box, text="Suite Forense & Download Backup WhatsApp",
                     text_color=MUTED, font=ctk.CTkFont(**F12)).pack(side="left")

        # Barra strumenti in alto a destra
        for txt, cmd in (("ℹ️ Informazioni", self._about),
                         ("📖 Manuale", self._readme),
                         ("📦 Dipendenze", self._install_deps),
                         ("⚙️ Impostazioni", self._settings)):
            ctk.CTkButton(head, text=txt, command=cmd, width=125, height=32,
                          fg_color=BUTTON_SEC, hover_color=BUTTON_SEC_HOVER,
                          corner_radius=8, font=ctk.CTkFont(**F11)).pack(side="right", padx=4)

        # Schede principali dell'applicazione
        self.tabs = ctk.CTkTabview(self, fg_color=PANEL, segmented_button_fg_color=FIELD,
                                   segmented_button_selected_color=ACCENT,
                                   segmented_button_selected_hover_color=ACCENT_HOVER,
                                   segmented_button_unselected_hover_color=BUTTON_SEC_HOVER,
                                   corner_radius=12)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=18, pady=6)

        tab_names = (
            "📥 Google Drive (WhaGoDri)",
            "🔍 Analisi Chat (WhaPa)",
            "🔐 Cifratura (WhaCipher)",
            "📑 Chat Esportate (WhaChat)",
            "🔀 Unisci Database (WhaMerge)",
            "☁️ iCloud (WhaCloud)"
        )
        for name in tab_names:
            self.tabs.add(name)

        self._tab_whagodri(self.tabs.tab("📥 Google Drive (WhaGoDri)"))
        self._tab_whapa(self.tabs.tab("🔍 Analisi Chat (WhaPa)"))
        self._tab_whacipher(self.tabs.tab("🔐 Cifratura (WhaCipher)"))
        self._tab_whachat(self.tabs.tab("📑 Chat Esportate (WhaChat)"))
        self._tab_whamerge(self.tabs.tab("🔀 Unisci Database (WhaMerge)"))
        self._tab_whacloud(self.tabs.tab("☁️ iCloud (WhaCloud)"))

        # Pannello inferiore (Output / Console Log)
        bottom = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=12, border_color=PANEL_BORDER, border_width=1)
        bottom.grid(row=2, column=0, sticky="nsew", padx=18, pady=(6, 14))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(bottom, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        ctk.CTkLabel(bar, text="🖥️ Console di Output", text_color=ACCENT,
                     font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")).pack(side="left")

        ctk.CTkButton(bar, text="🧹 Pulisci", width=80, height=28, command=self._clear,
                      fg_color=BUTTON_SEC, hover_color=BUTTON_SEC_HOVER,
                      corner_radius=6, font=ctk.CTkFont(**F11)).pack(side="right", padx=4)

        self.progress = ctk.CTkProgressBar(bar, width=170, height=10, mode="indeterminate",
                                           progress_color=ACCENT)
        self.progress.pack(side="right", padx=10)
        self.progress.set(0)

        self.log = ctk.CTkTextbox(bottom, fg_color="#090E11", text_color=TEXT,
                                  corner_radius=8, wrap="word",
                                  font=ctk.CTkFont(family="Consolas", size=12))
        self.log.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log.tag_config("ok", foreground=ACCENT)
        self.log.tag_config("err", foreground=ERROR)
        self.log.tag_config("cmd", foreground=MUTED)
        self._emit("Pronto. Scegli un'operazione, imposta i parametri e clicca sul pulsante di avvio.", "cmd")

    # ------------------------------------------------------------------
    #  Barra strumenti superiore
    # ------------------------------------------------------------------
    def _install_deps(self):
        req = os.path.join(APP_DIR, "doc", "requirements.txt")
        if not os.path.exists(req):
            return messagebox.showerror("WhaPa", f"File non trovato: {req}")
        faltan = []
        try:
            sys.path.insert(0, LIBS)
            import whadeps
            faltan = whadeps.check("Crypto", "colorama", "customtkinter", "requests",
                                   "pandas", "numpy", "configobj", "click",
                                   "pyicloud", "selenium", "Cryptodome")
        except Exception:
            pass
        dettagli = (f"\n\nDipendenze mancanti: {', '.join(faltan)}"
                    if faltan else "\n\nTutte le dipendenze sono già installate.")
        if not messagebox.askyesno("Verifica Dipendenze",
                                   "Vuoi procedere con l'installazione/aggiornamento delle librerie?" + dettagli):
            return
        self._launch_raw([sys.executable, "-m", "pip", "install", "--upgrade", "-r", req])

    def _settings(self):
        SettingsDialog(self)

    def _on_browser_changed(self, choice):
        cfg_path = os.path.join(APP_DIR, "cfg", "settings.cfg")
        try:
            cfg = ConfigParser()
            if os.path.exists(cfg_path):
                cfg.read(cfg_path, encoding="utf-8")
            if not cfg.has_section("gui"):
                cfg.add_section("gui")
            cfg.set("gui", "browser", choice)
            with open(cfg_path, "w", encoding="utf-8") as f:
                cfg.write(f)
            self._emit(f"[-] Browser impostato su: {choice}", "ok")
        except Exception:
            pass

    def open_url(self, url):
        browser_name = self.selected_browser.get()
        exe_path = self.installed_browsers.get(browser_name, "")
        if exe_path and os.path.isfile(exe_path):
            try:
                subprocess.Popen([exe_path, url])
                return
            except Exception as e:
                self._emit(f"[avviso] Impossibile avviare {browser_name}: {e}. Uso browser predefinito.", "err")
        webbrowser.open(url)

    def _readme(self):
        ruta = os.path.join(APP_DIR, "README.md")
        url = "file://" + os.path.abspath(ruta) if os.path.exists(ruta) else "https://github.com/Jinkazama75/whapa"
        self.open_url(url)

    def _about(self):
        messagebox.showinfo(
            f"WhaPa {VERSION}",
            f"WhaPa v{VERSION} - Suite Forense WhatsApp (Android & iOS)\n\n"
            "Interfaccia utente interamente localizzata in Italiano.\n"
            "Supporto per download backup Google Drive ed estrazione dati.\n\n"
            "Repository: https://github.com/Jinkazama75/whapa\n"
            "Licenza: GPL-3.0"
        )

    # ------------------------------------------------------------------
    #  Scheda 1: Google Drive (WhaGoDri)
    # ------------------------------------------------------------------
    def _tab_whagodri(self, tab):
        sc = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=6, pady=6)
        r = Row(sc)

        # Banner informativo moderno con selezione browser rilevato
        info_frame = ctk.CTkFrame(sc, fg_color=FIELD, corner_radius=10, border_color=PANEL_BORDER, border_width=1)
        info_frame.grid(row=r.r, column=0, columnspan=4, sticky="ew", padx=12, pady=(4, 14))

        top_info = ctk.CTkFrame(info_frame, fg_color="transparent")
        top_info.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(top_info, text="💡 Connessione a Google Drive: le credenziali e il Master Token vengono gestiti in Impostazioni.",
                     text_color=TEXT, font=ctk.CTkFont(**F11)).pack(side="left")

        browser_bar = ctk.CTkFrame(info_frame, fg_color="transparent")
        browser_bar.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkLabel(browser_bar, text="🌐 Browser:", text_color=ACCENT,
                     font=ctk.CTkFont(**F12_BOLD)).pack(side="left", padx=(0, 6))

        browser_dropdown = ctk.CTkOptionMenu(
            browser_bar,
            variable=self.selected_browser,
            values=list(self.installed_browsers.keys()),
            command=self._on_browser_changed,
            width=210, height=30,
            fg_color=BUTTON_SEC, button_color=BUTTON_SEC_HOVER,
            button_hover_color=ACCENT_HOVER,
            corner_radius=8, font=ctk.CTkFont(**F11),
            dropdown_font=ctk.CTkFont(**F11)
        )
        browser_dropdown.pack(side="left", padx=(0, 10))

        ctk.CTkButton(browser_bar, text="🔑 Apri Pagina Token (EmbeddedSetup)", width=230, height=30,
                      command=lambda: self.open_url("https://accounts.google.com/EmbeddedSetup"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#0B141A",
                      corner_radius=8, font=ctk.CTkFont(**F12_BOLD)).pack(side="left", padx=(0, 8))

        def mostra_guida_token():
            b_name = self.selected_browser.get()
            if "Firefox" in b_name:
                msg = (
                    "Procedura per Mozilla Firefox:\n\n"
                    "1. Clicca su 'Apri Pagina Token' (si aprirà una scheda in Firefox).\n"
                    "2. Premi F12 sulla tastiera per aprire gli strumenti sviluppatore.\n"
                    "3. Clicca sulla scheda 'Archiviazione' (Storage).\n"
                    "4. Nel menu a sinistra espandi 'Cookie' e seleziona 'https://accounts.google.com'.\n"
                    "5. Cerca il cookie con nome 'oauth_token', fai doppio clic sul valore e copialo.\n"
                    "6. Apri '⚙️ Impostazioni' qui in WhaPa e incollalo nel campo 'Token OAuth'."
                )
            else:
                msg = (
                    f"Procedura per {b_name}:\n\n"
                    "1. Clicca su 'Apri Pagina Token' (si aprirà una scheda nel browser).\n"
                    "2. Premi F12 sulla tastiera per aprire gli strumenti sviluppatore.\n"
                    "3. Clicca sulla scheda 'Applicazione' (Application).\n"
                    "4. Nel menu a sinistra espandi 'Cookie' e seleziona 'https://accounts.google.com'.\n"
                    "5. Cerca il cookie con nome 'oauth_token', fai doppio clic sul valore e copialo.\n"
                    "6. Apri '⚙️ Impostazioni' qui in WhaPa e incollalo nel campo 'Token OAuth'."
                )
            messagebox.showinfo("Guida Estrazione Token Google", msg)

        ctk.CTkButton(browser_bar, text="❓ Come trovare il token", width=160, height=30,
                      command=mostra_guida_token,
                      fg_color=BUTTON_SEC, hover_color=BUTTON_SEC_HOVER,
                      corner_radius=8, font=ctk.CTkFont(**F11)).pack(side="left")
        r.r += 1

        r.section("Parametri di Download da Google Drive")

        self.g_action = ctk.StringVar(value="Informazioni sul backup")
        opzioni_godri = [
            "Informazioni sul backup",
            "Elenca tutti i file nel backup",
            "Elenca backup WhatsApp",
            "Sincronizza tutto (Media e Database)",
            "Solo immagini (Foto)",
            "Solo video",
            "Solo audio e note vocali",
            "Solo documenti",
            "Solo database (msgstore.db)",
            "Scarica un singolo file"
        ]
        r.options("Azione da eseguire", self.g_action, opzioni_godri, width=280)

        self.g_file = Field()
        r.entry("File remoto specifico", self.g_file, "Percorso file (solo per 'Scarica un singolo file')", width=320)

        self.g_out = Field()
        r.file("Cartella di destinazione", self.g_out, "Cartella dove salvare i media", folder=True,
               hint="Cartella locale sul PC dove salvare i download")

        self.g_threads = Field("12")
        r.entry("Thread simultanei", self.g_threads, "12", width=100)

        self.g_np, self.g_dry = ctk.BooleanVar(), ctk.BooleanVar()
        r.checks([
            (self.g_np, "Disattiva download paralleli"),
            (self.g_dry, "Simulazione (Dry Run - nessun file scaricato)")
        ], cols=2)

        self.buttons.append(r.run("🚀 Avvia Download Google Drive", self._run_whagodri))

    def _run_whagodri(self):
        mapa = {
            "Informazioni sul backup": "-i",
            "Elenca tutti i file nel backup": "-l",
            "Elenca backup WhatsApp": "-lw",
            "Sincronizza tutto (Media e Database)": "-s",
            "Solo immagini (Foto)": "-si",
            "Solo video": "-sv",
            "Solo audio e note vocali": "-sa",
            "Solo documenti": "-sx",
            "Solo database (msgstore.db)": "-sd"
        }
        a = [tool("whagodri.py")]
        acc = self.g_action.get()
        if acc == "Scarica un singolo file":
            if not self.g_file.get():
                return messagebox.showwarning("Dati Mancanti", "Indica il percorso del file remoto da scaricare.")
            a += ["-p", self.g_file.get()]
        else:
            a.append(mapa.get(acc, "-i"))
        if self.g_out.get():
            a += ["-o", self.g_out.get()]
        if self.g_np.get():
            a.append("-np")
        if self.g_dry.get():
            a.append("-dr")
        if self.g_threads.get().isdigit():
            a += ["-tc", self.g_threads.get()]
        self._launch(a)

    # ------------------------------------------------------------------
    #  Scheda 2: Analisi Chat (WhaPa)
    # ------------------------------------------------------------------
    def _tab_whapa(self, tab):
        sc = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=6, pady=6)
        r = Row(sc)

        self.p_db, self.p_wa, self.p_out = Field(), Field(), Field()
        r.section("Database Sorgente")
        r.file("Database decifrato", self.p_db, "msgstore.db / ChatStorage.sqlite",
               [("Database SQLite", "*.db *.sqlite"), ("Tutti i file", "*.*")],
               hint="msgstore.db (Android) oppure ChatStorage.sqlite (iOS)")
        r.file("Rubrica contatti", self.p_wa, "wa.db / ContactsV2.sqlite",
               [("Database SQLite", "*.db *.sqlite"), ("Tutti i file", "*.*")],
               hint="wa.db (Android) oppure ContactsV2.sqlite (iOS) - opzionale per i nomi")
        r.file("Cartella di output", self.p_out, "Cartella di destinazione report", folder=True,
               hint="Cartella in cui salvare i report generati")

        self.p_media = Field()
        r.file("Cartella Media", self.p_media, "Cartella WhatsApp Media", folder=True,
               hint="Cartella WhatsApp contenente i media estratti")
        self.p_copymedia = ctk.BooleanVar()
        r.checks([(self.p_copymedia, "Copia gli allegati multimediali all'interno del report")], cols=1)

        r.section("Modalità di Analisi & Piattaforma")
        self.p_mode = ctk.StringVar(value="Messaggi")
        r.options("Modalità", self.p_mode, ["Messaggi", "Info: stati", "Info: chiamate",
                                            "Info: chat attive", "Estrai allegati", "Carving (recupero cancellati)"])
        self.p_platform = ctk.StringVar(value="Rilevamento automatico")
        r.options("Piattaforma", self.p_platform,
                  ["Rilevamento automatico", "Android recente", "Android precedente", "iOS"])

        r.section("Filtri Destinatari & Contatti")
        self.p_recip = ctk.StringVar(value="Tutti")
        r.options("Ambito", self.p_recip, ["Tutti", "Utente singolo", "Gruppo",
                                           "Messaggi da un numero", "Broadcast (diffusione)"])
        self.p_target = Field()
        r.entry("Numero o Gruppo", self.p_target, "es. 393401234567 oppure ID gruppo", width=280)

        r.section("Filtri Ricerca Messaggi")
        self.p_text, self.p_sender = Field(), Field()
        self.p_ts, self.p_te, self.p_raw = Field(), Field(), Field()
        r.entry("Testo da cercare", self.p_text, "Parola chiave, allegato o citazione", width=300)
        r.entry("Mittente", self.p_sender, "Numero o nome mittente", width=220)
        r.entry("Data inizio", self.p_ts, "gg-mm-aaaa HH:MM", width=180)
        r.entry("Data fine", self.p_te, "gg-mm-aaaa HH:MM", width=180)
        r.entry("Codici tipo nativi", self.p_raw, "es. 66,112", width=140)

        self.p_dir = ctk.StringVar(value="Tutte")
        r.options("Direzione messaggi", self.p_dir, ["Tutte", "Inviati", "Ricevuti", "Di sistema"])

        self.p_flags = {}
        for k in ("regex", "case", "word", "web", "starred", "forwarded",
                  "edited", "media", "location", "read", "unread"):
            self.p_flags[k] = ctk.BooleanVar()
        r.checks([
            (self.p_flags["regex"], "Regex"),
            (self.p_flags["case"], "Maiusc/Minusc"),
            (self.p_flags["word"], "Parola intera"),
            (self.p_flags["web"], "WhatsApp Web"),
            (self.p_flags["starred"], "Preferiti"),
            (self.p_flags["forwarded"], "Inoltrati"),
            (self.p_flags["edited"], "Modificati"),
            (self.p_flags["media"], "Con allegato"),
            (self.p_flags["location"], "Con coordinate GPS"),
            (self.p_flags["read"], "Letti"),
            (self.p_flags["unread"], "Non letti")
        ], cols=4, label="OPZIONI AVANZATE DI RICERCA")

        self.p_types = {}
        tipi = [("tt", "Testo"), ("ti", "Immagini"), ("ta", "Audio"), ("tv", "Video"),
                ("tc", "Contatto"), ("tl", "Posizione"), ("tx", "Chiamate"),
                ("tp", "Documenti"), ("tg", "GIF"), ("td", "Eliminati"),
                ("tr", "Posiz. tempo reale"), ("tk", "Sticker"), ("tm", "Sistema"),
                ("tn", "Sondaggio"), ("tq", "Visualizz. singola"), ("tj", "Video nota"),
                ("tz", "Evento")]
        for k, _ in tipi:
            self.p_types[k] = ctk.BooleanVar()
        r.checks([(self.p_types[k], t) for k, t in tipi], cols=6,
                 label="TIPI DI MESSAGGIO (selezionane nessuno per includerli tutti)")

        r.section("Formato del Report di Uscita")
        self.p_report = ctk.StringVar(value="Nessuno")
        r.options("Report Interattivo", self.p_report, ["Nessuno", "ES", "EN"])
        self.p_out_flags = {k: ctk.BooleanVar()
                            for k in ("print", "csv", "kml", "maps", "single")}
        r.checks([
            (self.p_out_flags["print"], "Report stampabile"),
            (self.p_out_flags["csv"], "Esporta tabella CSV"),
            (self.p_out_flags["kml"], "Esporta posizioni KML (Google Earth)"),
            (self.p_out_flags["maps"], "Scarica mappe GPS (richiede connessione)"),
            (self.p_out_flags["single"], "Report in file unico HTML")
        ], cols=3)

        self.buttons.append(r.run("🚀 Avvia Analisi WhaPa", self._run_whapa))

    def _run_whapa(self):
        if not self.p_db.get():
            return messagebox.showwarning("Dati Mancanti", "Seleziona il database delle chat da analizzare.")
        a = [tool("whapa.py"), self.p_db.get()]
        modo = self.p_mode.get()
        if modo == "Messaggi":
            a.append("-m")
        elif modo.startswith("Info"):
            a += ["-i", {"Info: stati": "1", "Info: chiamate": "2",
                         "Info: chat attive": "3"}[modo]]
        elif modo == "Estrai allegati":
            a.append("-e")
        else:
            a.append("-c")

        plat = {"Android recente": "android", "Android precedente": "android_legacy",
                "iOS": "ios"}.get(self.p_platform.get())
        if plat:
            a += ["--platform", plat]
        if self.p_wa.get():
            a += ["-wa", self.p_wa.get()]
        if self.p_out.get():
            a += ["-o", self.p_out.get()]
        if self.p_media.get():
            a += ["-mp", self.p_media.get()]
            if self.p_copymedia.get():
                a.append("-cm")

        if modo == "Messaggi":
            alc, tgt = self.p_recip.get(), self.p_target.get().strip()
            if alc == "Tutti":
                a.append("-a")
            elif alc == "Broadcast (diffusione)":
                a += ["-a", "-b"]
            elif alc == "Utente singolo" and tgt:
                a += ["-u", tgt]
            elif alc == "Gruppo" and tgt:
                a += ["-g", tgt]
            elif alc == "Messaggi da un numero" and tgt:
                a += ["-ua", tgt]
            else:
                a.append("-a")

            if self.p_text.get():
                a += ["-t", self.p_text.get()]
            if self.p_sender.get():
                a += ["-sn", self.p_sender.get()]
            if self.p_ts.get():
                a += ["-ts", self.p_ts.get()]
            if self.p_te.get():
                a += ["-te", self.p_te.get()]
            if self.p_raw.get():
                a += ["-rt", self.p_raw.get()]
            d = {"Inviati": "sent", "Ricevuti": "received",
                 "Di sistema": "system"}.get(self.p_dir.get())
            if d:
                a += ["-d", d]
            for k, flag in (("regex", "-re"), ("case", "-cs"), ("word", "-ww"),
                            ("web", "-w"), ("starred", "-s"), ("forwarded", "-fw"),
                            ("edited", "-ed"), ("media", "-md"), ("location", "-gp"),
                            ("read", "-lr"), ("unread", "-lu")):
                if self.p_flags[k].get():
                    a.append(flag)
            for k, v in self.p_types.items():
                if v.get():
                    a.append("-" + k)
            if self.p_report.get() != "Nessuno":
                a += ["-r", self.p_report.get()]
            if self.p_out_flags["print"].get():
                a.append("-p")
            if self.p_out_flags["csv"].get():
                a.append("-x")
            if self.p_out_flags["kml"].get():
                a.append("-k")
            if self.p_out_flags["maps"].get():
                a.append("-gm")
            if self.p_out_flags["single"].get():
                a.append("-1")
        self._launch(a)

    # ------------------------------------------------------------------
    #  Scheda 3: Cifratura / Decifratura (WhaCipher)
    # ------------------------------------------------------------------
    def _tab_whacipher(self, tab):
        r = Row(tab)
        self.c_mode = ctk.StringVar(value="Decifra")
        self.c_in, self.c_key, self.c_out = Field(), Field(), Field()
        self.c_isdir = ctk.BooleanVar()
        r.section("Cifratura & Decifratura Database WhatsApp")
        r.options("Operazione", self.c_mode, ["Decifra", "Cifra (crypt15)"])
        r.file("File di ingresso", self.c_in, "Database cifrato o decifrato",
               [("Database WhatsApp", "*.crypt12 *.crypt14 *.crypt15 *.db"), ("Tutti i file", "*.*")],
               hint="msgstore.db.crypt15, .crypt14 o database .db")
        r.checks([(self.c_isdir, "L'ingresso è un'intera cartella (solo per decifratura)")], cols=1)
        r.file("Chiave di decifratura", self.c_key, "File della chiave di decifratura",
               hint="File key, encrypted_backup.key oppure chiave esadecimale a 64 cifre")
        ctk.CTkLabel(tab, text="Nota: La chiave può essere il file 'key' (da memoria interna), "
                               "'encrypted_backup.key' o la chiave esadecimale a 64 caratteri.",
                     text_color=MUTED, font=ctk.CTkFont(**F11), wraplength=820,
                     justify="left").grid(row=r.r, column=0, columnspan=4,
                                          sticky="w", padx=14, pady=(0, 6))
        r.r += 1
        r.file("File di destinazione", self.c_out, "File o cartella decifrata", save=True,
               hint="msgstore.db (file generato)")
        self.buttons.append(r.run("🚀 Esegui WhaCipher", self._run_whacipher))

    def _run_whacipher(self):
        if not (self.c_in.get() and self.c_key.get() and self.c_out.get()):
            return messagebox.showwarning("Dati Mancanti",
                                          "I campi Ingresso, Chiave e Destinazione sono tutti obbligatori.")
        a = [tool("whacipher.py")]
        a += ["-p" if self.c_isdir.get() else "-f", self.c_in.get()]
        a += ["-d" if self.c_mode.get() == "Decifra" else "-e", self.c_key.get()]
        a += ["-o", self.c_out.get()]
        self._launch(a)

    # ------------------------------------------------------------------
    #  Scheda 4: Chat Esportate (.txt) (WhaChat)
    # ------------------------------------------------------------------
    def _tab_whachat(self, tab):
        r = Row(tab)
        self.h_file, self.h_user = Field(), Field()
        self.h_fmt, self.h_ts, self.h_te = Field(), Field(), Field()
        r.section("Analisi Chat Esportata dall'App WhatsApp")
        r.file("File del chat (.txt)", self.h_file, "Chat esportata (.txt)",
               [("File di testo", "*.txt"), ("Tutti i file", "*.*")], hint="Chat WhatsApp con <Nome>.txt")
        self.h_sys = ctk.StringVar(value="android")
        r.options("Sistema operativo", self.h_sys, ["android", "ios"], width=150)
        self.h_report = ctk.StringVar(value="Nessuno")
        r.options("Report interattivo", self.h_report, ["Nessuno", "ES", "EN"], width=150)
        r.entry("Nome utente target", self.h_user, "Nome del contatto esattamente come appare", width=280)
        r.entry("Formato data", self.h_fmt, "%d/%m/%y %H:%M:%S", width=220)
        r.entry("Da data", self.h_ts, "gg-mm-aaaa HH:MM", width=190)
        r.entry("A data", self.h_te, "gg-mm-aaaa HH:MM", width=190)
        self.h_media = Field()
        r.file("Cartella allegati", self.h_media, "Cartella con allegati esportati",
               folder=True, hint="Predefinito: la stessa cartella in cui si trova il file .txt")
        self.h_out = Field()
        r.file("Cartella di output", self.h_out, "Cartella output report", folder=True,
               hint="Cartella in cui salvare il report generato")
        self.h_text = Field()
        r.entry("Cerca nel testo", self.h_text, "", width=260)
        self.h_part = ctk.BooleanVar()
        self.h_flags = {k: ctk.BooleanVar() for k in ("print", "csv", "copy", "regex")}
        r.checks([
            (self.h_part, "Elenca solo i partecipanti"),
            (self.h_flags["print"], "Report stampabile"),
            (self.h_flags["csv"], "Esporta CSV"),
            (self.h_flags["copy"], "Copia allegati nel report"),
            (self.h_flags["regex"], "Usa Regex")
        ], cols=3)
        self.buttons.append(r.run("🚀 Esegui Analisi Chat", self._run_whachat))

    def _run_whachat(self):
        if not self.h_file.get():
            return messagebox.showwarning("Dati Mancanti", "Seleziona il file .txt della chat esportata.")
        a = [tool("whachat.py"), self.h_file.get()]
        if self.h_part.get():
            a.append("-p")
        if self.h_user.get():
            a += ["-u", self.h_user.get()]
        a += ["-s", self.h_sys.get()]
        if self.h_report.get() != "Nessuno":
            a += ["-r", self.h_report.get()]
        if self.h_fmt.get():
            a += ["-f", self.h_fmt.get()]
        if self.h_ts.get():
            a += ["-ts", self.h_ts.get()]
        if self.h_te.get():
            a += ["-te", self.h_te.get()]
        if self.h_out.get():
            a += ["-o", self.h_out.get()]
        if self.h_media.get():
            a += ["-mp", self.h_media.get()]
        if self.h_text.get():
            a += ["-t", self.h_text.get()]
        if self.h_flags["regex"].get():
            a.append("-re")
        if self.h_flags["print"].get():
            a.append("-pr")
        if self.h_flags["csv"].get():
            a.append("-x")
        if self.h_flags["copy"].get():
            a.append("-cm")
        self._launch(a)

    # ------------------------------------------------------------------
    #  Scheda 5: Unisci Database (WhaMerge)
    # ------------------------------------------------------------------
    def _tab_whamerge(self, tab):
        r = Row(tab)
        self.m_path, self.m_out = Field(), Field()
        r.section("Unione di Database WhatsApp Multipli")
        r.file("Cartella con i database", self.m_path, "Cartella contenente i vari msgstore*.db",
               folder=True, hint="Cartella contenente più file msgstore.db da unire")
        r.file("Database risultante", self.m_out, "msgstore_merge.db", save=True,
               hint="msgstore_merge.db (file generato finale)")
        self.buttons.append(r.run("🚀 Esegui Unione Database", self._run_whamerge))

    def _run_whamerge(self):
        if not self.m_path.get():
            return messagebox.showwarning("Dati Mancanti", "Seleziona la cartella contenente i database.")
        a = [tool("whamerge.py"), self.m_path.get()]
        if self.m_out.get():
            a += ["-o", self.m_out.get()]
        self._launch(a)

    # ------------------------------------------------------------------
    #  Scheda 6: iCloud (WhaCloud)
    # ------------------------------------------------------------------
    def _tab_whacloud(self, tab):
        r = Row(tab)
        r.section("Download Backup da Apple iCloud (iOS)")
        ctk.CTkLabel(tab, text="Le credenziali vengono lette da Impostazioni (cfg/settings.cfg), sezione [icloud-auth].",
                     text_color=MUTED, font=ctk.CTkFont(**F11)).grid(row=r.r, column=0, columnspan=4,
                                                                     sticky="w", padx=14, pady=(0, 8))
        r.r += 1
        self.k_action = ctk.StringVar(value="Elenca file")
        r.options("Azione", self.k_action, ["Elenca file", "Scarica un singolo file",
                                            "Sincronizza tutto", "Solo immagini",
                                            "Solo video e audio"], 240)
        self.k_file, self.k_out = Field(), Field()
        r.entry("File remoto specifico", self.k_file, "Percorso file remoto", 280)
        r.file("Cartella di destinazione", self.k_out, "Cartella locale output", folder=True,
               hint="Cartella in cui salvare i download")
        self.buttons.append(r.run("🚀 Esegui Download iCloud", self._run_whacloud))

    def _run_whacloud(self):
        mapa = {"Elenca file": "-l", "Sincronizza tutto": "-s", "Solo immagini": "-si",
                "Solo video e audio": "-sv"}
        a = [tool("whacloud.py")]
        if self.k_action.get() == "Scarica un singolo file":
            if not self.k_file.get():
                return messagebox.showwarning("Dati Mancanti", "Specifica il percorso del file da scaricare.")
            a += ["-p", self.k_file.get()]
        else:
            a.append(mapa.get(self.k_action.get(), "-l"))
        if self.k_out.get():
            a += ["-o", self.k_out.get()]
        self._launch(a)

    # ------------------------------------------------------------------
    #  Gestione esecuzione comandi & Output in tempo reale
    # ------------------------------------------------------------------
    def _emit(self, msg, tag=None):
        self.q.put((msg, tag))

    def _clear(self):
        self.log.delete("1.0", "end")

    def _drain(self):
        try:
            while True:
                msg, tag = self.q.get_nowait()
                if tag == "__done__":
                    self._set_busy(False)
                    continue
                self.log.insert("end", msg + "\n", tag or ())
                self.log.see("end")
        except queue.Empty:
            pass
        self.after(120, self._drain)

    def _set_busy(self, busy):
        self.busy = busy
        for b in self.buttons:
            b.configure(state="disabled" if busy else "normal")
        if busy:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def _launch_raw(self, argv):
        if self.busy:
            return
        self._set_busy(True)
        self._emit("\n$ " + " ".join(shlex.quote(x) for x in argv), "cmd")
        threading.Thread(target=self._work_raw, args=(argv,), daemon=True).start()

    def _work_raw(self, argv):
        try:
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    bufsize=1, encoding="utf-8",
                                    errors="replace",
                                    env=dict(os.environ,
                                             PYTHONIOENCODING="utf-8:replace"))
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line.strip():
                    self._emit(line)
            proc.wait()
            self._emit("[fine] {}".format(
                "Operazione completata con successo." if proc.returncode == 0 else
                f"Terminato con codice di errore {proc.returncode}"),
                "ok" if proc.returncode == 0 else "err")
        except Exception as e:
            self._emit(f"[errore] {e}", "err")
        finally:
            self.q.put(("", "__done__"))

    def _launch(self, argv):
        if self.busy:
            return
        self._set_busy(True)
        self._emit("\n$ python3 " + " ".join(shlex.quote(x) for x in argv), "cmd")
        threading.Thread(target=self._work, args=(argv,), daemon=True).start()

    def _work(self, argv):
        try:
            entorno = dict(os.environ, PYTHONIOENCODING="utf-8:replace")
            proc = subprocess.Popen([sys.executable] + argv,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    cwd=APP_DIR, text=True, bufsize=1,
                                    encoding="utf-8", errors="replace",
                                    env=entorno)
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line.strip():
                    tag = "err" if line.startswith("[e]") or line.startswith("[errore]") else (
                        "ok" if line.startswith("[-]") or line.startswith("[+]") else None)
                    self._emit(line, tag)
            proc.wait()
            if proc.returncode == 0:
                self._emit("[fine] Operazione terminata con successo.", "ok")
            else:
                self._emit(f"[fine] Operazione terminata con codice di errore {proc.returncode}.", "err")
        except Exception as e:
            self._emit(f"[errore] Impossibile avviare il processo: {e}", "err")
        finally:
            self.q.put(("", "__done__"))


if __name__ == "__main__":
    WhapaGUI().mainloop()
