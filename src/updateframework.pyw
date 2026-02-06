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
FILE_NAME      = "applicationdebugger.pyw"      # Name der Hauptdatei deiner Anwendung
urllib.request.urlcleanup()
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

# ────────────────────────────────────────────────

# Pfade relativ zum Updater-Skript
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
APP_DIR       = os.path.join(LOCAL_APPDATA, "UpdateFramework")
APP_PATH      = os.path.join(APP_DIR, FILE_NAME)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

IS_WINDOWS = platform.system().lower() == "windows"

venv_activated = False
venv_python = "./venv/Scripts/python.exe"

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
        req = urllib.request.Request(UPDATE_URL)
        req.add_header('Pragma', 'no-cache')
        response = urllib.request.urlopen(req, timeout=15, context=context)
        with response as resp:
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

# --- Try to activate venv ---

def try_install_venv() -> bool:
    venv_path = os.path.join("./venv")
    if not os.path.exists(venv_path):
        if subprocess.run(["python", "-m", "venv", ".venv"], check=False):
            print("Virtual environment created.")
            return True
        else:
            print("Failed to create virtual environment.")
            return False
    
    return True

def install_dependencies():
    if venv_activated:
        try:
            import requests
            print("Dependencies already installed.")
        except ImportError:
            print("Installing dependencies...")
            if subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"]):
                print("Dependencies installed successfully.")
            else:
                print("Failed to install dependencies.")
            try:
                import requests
            except ImportError:
                print("Failed to import dependencies after installation.")

if __name__ == "__main__":
    if try_install_venv():
        print("Virtual environment is ready.")
        install_dependencies()
    else:
        print("Failed to activate virtual environment.")
else:
    print("Failed to create virtual environment.")



def start_main_app():
    """Startet die Hauptanwendung zuverlässig unter Windows & Linux"""
    if not os.path.exists(APP_PATH):
        return False

    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0 # type: ignore

    try:
        subprocess.run([venv_python, "applicationdebugger.pyw"], creationflags=creationflags)
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
