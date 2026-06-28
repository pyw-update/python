import tkinter as tk
import os
import time
import base64
import threading
from io import BytesIO
import re
from pathlib import Path

try:
    from PIL import ImageGrab
except Exception as e:
    ImageGrab = None
    print("PIL/ImageGrab nicht verfügbar:", e)

try:
    from pynput import mouse
except Exception as e:
    mouse = None
    print("pynput/mouse nicht verfügbar:", e)

try:
    import requests
except Exception as e:
    requests = None
    print("requests nicht verfügbar:", e)


# ------------------------------------------------------------
# APP-/CONFIG-PFADE
# ------------------------------------------------------------

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent

# .env bleibt absichtlich neben der App-Datei, damit sie auf dem UNC-/Adobe-Ordner
# sichtbar und bearbeitbar ist. Die venv darf dagegen lokal liegen.
CONFIG_DIR = Path(os.environ.get("UPDATEFRAMEWORK_CONFIG_DIR", str(SCRIPT_DIR))).resolve()
ENV_FILE = CONFIG_DIR / ".env"


# ------------------------------------------------------------
# ENV
# ------------------------------------------------------------

def ensure_default_env(env_file=".env"):
    if os.path.exists(env_file):
        return

    env_dir = os.path.dirname(os.fspath(env_file))
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)

    defaults = {
        "GEMINI_API_KEY": "HIER_DEIN_GEMINI_API_KEY_EINFUEGEN",
        "GEMINI_MODEL": "gemini-3.1-flash-lite",
        "GEMINI_USE_GOOGLE_SEARCH": "0",
        "FONT_NAME": "Arial",
        "FONT_SIZE": "7",
        "FONT_STYLE": "normal",
        "TEXT_POSITION": "bottom_center",
        "TEXT_COLOR": "#d3d3d3",
        "ANSWER_BG_COLOR": "#eeeeee",
    }

    with open(env_file, "w", encoding="utf-8") as f:
        f.write("# Auto-generated default .env\n")
        f.write("# Trage hier deinen Gemini API Key ein.\n")
        f.write("# TEXT_POSITION: top_left, top_center, top_right, center_left, center, center_right, bottom_left, bottom_center, bottom_right\n\n")
        for k, v in defaults.items():
            safe_value = str(v).replace('\\', '\\\\').replace('"', '\\"')
            f.write(f'{k}="{safe_value}"\n')


def load_env(env_file=".env", overwrite=False):
    data = {}
    if not os.path.exists(env_file):
        return data

    with open(env_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if value and value[0] not in ("'", '"') and "#" in value:
                value = value.split("#", 1)[0].strip()

            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1].replace('\\"', '"')

            data[key] = value
            if overwrite or key not in os.environ:
                os.environ[key] = value

    return data


def to_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "ja", "on")


ensure_default_env(ENV_FILE)
cfg = load_env(ENV_FILE)


# ------------------------------------------------------------
# QA
# ------------------------------------------------------------
# Hier kannst du feste Fragen/Lösungen einfügen.
# Beispiel:
# QA = {
#     "Was bedeutet Vertraulichkeit?": "Nur Berechtigte dürfen Daten lesen.",
#     "Nenne die drei Schutzziele.": "Vertraulichkeit | Integrität | Verfügbarkeit",
# }

QA = {
    # Eigene lokale Frage/Antwort-Paare hier eintragen.
}

# ------------------------------------------------------------
# KONFIG
# ------------------------------------------------------------

def clean_env_value(value, default):
    value = str(value or "").strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1].strip()

    if not value:
        return default

    return value


def clean_color(value, default):
    value = clean_env_value(value, default)

    # Falls jemand aus Versehen nur # oder leeren Wert einträgt
    if value == "#":
        return default

    # Hex-Farbe grob prüfen: #RGB oder #RRGGBB
    if value.startswith("#"):
        hex_part = value[1:]
        if len(hex_part) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in hex_part):
            return value
        return default

    # Normale Tkinter-Farbnamen wie red, white, black erlauben
    return value


# ------------------------------------------------------------
# GEMINI KONFIG
# ------------------------------------------------------------

GEMINI_API_KEY = clean_env_value(
    cfg.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
    ""
)

GEMINI_MODEL = clean_env_value(
    cfg.get("GEMINI_MODEL", os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")),
    "gemini-3.1-flash-lite"
)

GEMINI_USE_GOOGLE_SEARCH = to_bool(
    cfg.get("GEMINI_USE_GOOGLE_SEARCH", os.environ.get("GEMINI_USE_GOOGLE_SEARCH", "0")),
    False
)


FONT_NAME = clean_env_value(cfg.get("FONT_NAME", "Arial"), "Arial")
FONT_SIZE = to_int(cfg.get("FONT_SIZE", 7), 7)
FONT_STYLE = clean_env_value(cfg.get("FONT_STYLE", "normal"), "normal")

TEXT_COLOR = clean_color(cfg.get("TEXT_COLOR", "#d3d3d3"), "#d3d3d3")
ANSWER_BG_COLOR = clean_color(cfg.get("ANSWER_BG_COLOR", "#eeeeee"), "#eeeeee")
POSITION = clean_env_value(cfg.get("TEXT_POSITION", "bottom_center"), "bottom_center")

MAX_WIDTH_RATIO = 0.50

ORANGE = "#ff9900"
GREEN = "#00cc44"
RED = "#ff0000"
MAGENTA = "#ff00ff"
DARKMAGENTA = "#9900ff"
BLUE = "#0099ff"

BACKGROUND_WIDTH = None
BACKGROUND_HEIGHT = None

OFFSET_X = 0
OFFSET_Y = -5
BOX_LENGTH = 5
BOX_HEIGHT = 2

KI_SERVER_URL = clean_env_value(cfg.get("KI_SERVER_URL", "https://zeitdoc.com"), "https://zeitdoc.com").rstrip("/")

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
log_dir = desktop_path if os.path.isdir(desktop_path) else os.getcwd()
ERROR_LOG = os.path.join(log_dir, "test.txt")

boolean_ki_enabled = True


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

def log_error(msg: str):
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


# ------------------------------------------------------------
# TK SETUP
# ------------------------------------------------------------

root = tk.Tk()
root.withdraw()


def close_app(event=None):
    try:
        root.quit()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass
    return "break"


current_status_color = ORANGE
green_since = None

status_win = tk.Toplevel(root)
status_win.overrideredirect(True)
status_win.attributes("-topmost", True)
status_win.geometry(
    f"{BOX_LENGTH}x{BOX_HEIGHT}+"
    f"{status_win.winfo_screenwidth() - BOX_LENGTH}+"
    f"{status_win.winfo_screenheight() - BOX_HEIGHT}"
)

status = tk.Frame(status_win, bg=ORANGE, bd=0, highlightthickness=0)
status.pack(fill="both", expand=True)

overlay = tk.Toplevel(root)
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)

label = tk.Label(
    overlay,
    text="",
    fg=TEXT_COLOR,
    font=(FONT_NAME, FONT_SIZE, FONT_STYLE),
    justify="left",
    bg=ANSWER_BG_COLOR,
)
label.pack()
overlay.withdraw()


# ------------------------------------------------------------
# STATUS / THREAD
# ------------------------------------------------------------

def set_status(color):
    global current_status_color, green_since
    current_status_color = color
    try:
        status.configure(bg=color)
    except Exception:
        pass
    green_since = time.time() if color == GREEN else None


def set_processing(on: bool):
    if on:
        set_status(DARKMAGENTA)
    else:
        set_status(GREEN if listening else ORANGE)


def status_refresher():
    do_refresh = current_status_color == ORANGE
    if current_status_color == GREEN and green_since is not None:
        do_refresh = time.time() - green_since >= 10

    if do_refresh:
        try:
            status_win.attributes("-topmost", False)
            status_win.attributes("-topmost", True)
            status_win.lift()
        except Exception:
            pass

    root.after(500, status_refresher)


def run_worker(work_fn, done_fn=None, fallback_error="Fehler"):
    def target():
        try:
            result = work_fn()
        except Exception as e:
            log_error(f"Worker error: {repr(e)}")
            result = fallback_error

        if done_fn:
            try:
                root.after(0, lambda r=result: done_fn(r))
            except Exception as e:
                log_error(f"root.after error: {repr(e)}")

    threading.Thread(target=target, daemon=True).start()


# ------------------------------------------------------------
# GEMINI KI
# ------------------------------------------------------------

KI_QA_DEFAULT_INSTRUCTION = """
Du bist ein Aufgaben-Löser für ein Overlay. Antworte ausschließlich als Raw Text in genau einer Zeile.

EXTREM WICHTIG:
Gib NUR die finale Lösung aus.
Wiederhole NIEMALS die Frage.
Schreibe NIEMALS den Aufgabentitel.
Schreibe NIEMALS "Antwort:", "Lösung:", "Die Antwort ist", "Aufgabe:", "Frage:", "Titel:" oder ähnliche Labels.
Schreibe keine Erklärung.
Schreibe kein JSON.
Schreibe kein Markdown.
Schreibe keine Aufzählung.
Schreibe keine Nummerierung.
Schreibe keine Emojis.
Schreibe keine Zeilenumbrüche.

FORMAT:
- Eine einzelne Antwort: nur die Antwort
- Mehrere Antworten: Antwort1 | Antwort2 | Antwort3
- Zuordnungsaufgabe: Teil1 > Teil2 | Teil3 > Teil4

WENN EIN BILD GESENDET WIRD:
Ignoriere Überschriften, Fragetitel, Aufgabennamen und Einleitungstexte.
Gib nur das aus, was als Lösung eingetragen werden muss.
""".strip()


def gemini_api_url() -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def gemini_key_ok() -> bool:
    key = str(GEMINI_API_KEY or "").strip()
    return bool(key) and key != "HIER_DEIN_GEMINI_API_KEY_EINFUEGEN"


def one_line(text) -> str:
    return " ".join(str(text or "").strip().split())


def strip_wrapping_quotes(text: str) -> str:
    s = one_line(text)
    while len(s) >= 2 and (
        (s[0] == '"' and s[-1] == '"')
        or (s[0] == "'" and s[-1] == "'")
        or (s[0] == "“" and s[-1] == "”")
        or (s[0] == "„" and s[-1] == "“")
    ):
        s = s[1:-1].strip()
    return s


def strip_bad_ai_prefix(text: str) -> str:
    s = strip_wrapping_quotes(text)
    if not s:
        return ""

    s = s.replace("｜", "|").replace("¦", "|").replace("‖", "|")
    s = s.replace("→", ">").replace("⇒", ">").replace("->", ">")

    bad_prefixes = [
        "antwort:", "antwort :", "lösung:", "lösung :", "loesung:", "loesung :",
        "die antwort ist", "die lösung ist", "die loesung ist",
        "aufgabe:", "aufgabe :", "frage:", "frage :", "titel:", "titel :",
        "task:", "task :", "question:", "question :", "title:", "title :",
        "final answer:", "final answer :", "answer:", "answer :", "solution:", "solution :",
    ]

    changed = True
    while changed:
        changed = False
        low = s.lower().strip()
        for prefix in bad_prefixes:
            if low.startswith(prefix):
                s = s[len(prefix):].strip()
                changed = True
                break

    if "|" in s:
        parts = [p.strip() for p in s.split("|") if p.strip()]
        if len(parts) > 1:
            first_low = parts[0].lower()
            if any(x in first_low for x in ("aufgabe", "frage", "heißt", "heisst", "title", "task", "question", "called")):
                s = " | ".join(parts[1:]).strip()

    if ":" in s:
        left, right = s.split(":", 1)
        left_clean = left.strip()
        right_clean = right.strip()
        left_low = left_clean.lower()
        looks_like_question = (
            "?" in left_clean
            or len(left_clean) > 18
            or any(x in left_low for x in ("aufgabe", "frage", "question", "task"))
            or left_low.startswith(("what ", "which ", "why ", "how ", "wer ", "was ", "wie ", "warum ", "welche "))
        )
        if looks_like_question and right_clean:
            s = right_clean

    return strip_wrapping_quotes(s)


def normalize_single_variant(text: str) -> str:
    p = strip_bad_ai_prefix(text)
    p = p.strip().lstrip("-").lstrip("*").lstrip("•").strip()
    p = re.sub(r"^\s*\d+\s*[\.)]\s*", "", p).strip()
    p = p.replace("**", "").replace("__", "").strip()
    return strip_bad_ai_prefix(p)


def normalize_ai_answer(text: str) -> str:
    s = "" if text is None else str(text)

    for key in ("response", "answer", "text", "message", "Message"):
        pattern = rf"""['"]{key}['"]\s*:\s*['"]([^'"]+)['"]"""
        match = re.search(pattern, s)
        if match:
            s = match.group(1)
            break

    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("｜", "|").replace("¦", "|").replace("‖", "|")
    s = s.replace("→", ">").replace("⇒", ">").replace("->", ">")
    s = re.sub(r"\n+", " | ", s)
    s = strip_bad_ai_prefix(s)

    if not s:
        return ""

    parts = [normalize_single_variant(p) for p in s.split("|")]
    parts = [p for p in parts if p]
    return " | ".join(parts) if parts else ""


def normalize_answer_text(text: str) -> str:
    return normalize_ai_answer(text)


def extract_gemini_error(response) -> str:
    raw = response.text or ""
    try:
        obj = response.json()
    except Exception:
        return normalize_ai_answer(raw) or raw[:300]

    if isinstance(obj, dict):
        err = obj.get("error")
        if isinstance(err, dict) and err.get("message"):
            return normalize_ai_answer(err.get("message")) or err.get("message")

    return normalize_ai_answer(raw) or raw[:300]


def extract_ki_text(response) -> str:
    raw = response.text or ""

    try:
        obj = response.json()
    except Exception:
        return normalize_ai_answer(raw)

    if isinstance(obj, str):
        return normalize_ai_answer(obj)

    if not isinstance(obj, dict):
        return normalize_ai_answer(raw)

    if "error" in obj:
        return extract_gemini_error(response)

    candidates = obj.get("candidates") or []
    if candidates:
        candidate = candidates[0] or {}
        parts = (candidate.get("content") or {}).get("parts") or []
        texts = []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
        if texts:
            return normalize_ai_answer(" ".join(texts))

        finish_reason = candidate.get("finishReason")
        if finish_reason:
            return normalize_ai_answer(f"Keine Antwort: {finish_reason}")

    prompt_feedback = obj.get("promptFeedback")
    if prompt_feedback:
        return normalize_ai_answer(f"Keine Antwort: {prompt_feedback}")

    return normalize_ai_answer(raw)


def build_gemini_payload(prompt: str, image_base64: str = None) -> dict:
    parts = []

    if image_base64:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_base64,
            }
        })

    parts.append({"text": prompt})

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "topP": 0.1,
            "topK": 1,
            "maxOutputTokens": 512,
        },
    }

    if GEMINI_USE_GOOGLE_SEARCH:
        payload["tools"] = [
            {
                "google_search": {}
            }
        ]

    return payload


def request_gemini(payload: dict, timeout=(5, 180)) -> str:
    if requests is None:
        return "requests nicht verfügbar"

    if not gemini_key_ok():
        return "GEMINI_API_KEY fehlt"

    try:
        response = requests.post(
            gemini_api_url(),
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )

        if response.status_code >= 400:
            msg = extract_gemini_error(response)
            log_error(f"Gemini HTTP {response.status_code}: {msg}")
            return f"Gemini HTTP {response.status_code}: {msg[:120]}"

        text = extract_ki_text(response)
        return text if text else "Keine Antwort"

    except requests.exceptions.Timeout:
        log_error("Gemini Timeout")
        return "Gemini Timeout"
    except requests.exceptions.RequestException as e:
        log_error(f"Gemini RequestException: {repr(e)}")
        return "Gemini nicht erreichbar"
    except Exception as e:
        log_error(f"Gemini Fehler: {repr(e)}")
        return f"Gemini Fehler: {type(e).__name__}"


def request_ki_text(question: str, timeout=(5, 120)) -> str:
    prompt = (
        f"{KI_QA_DEFAULT_INSTRUCTION}\n\n"
        "Nutze Google Search nur dann, wenn aktuelle Informationen oder externe Fakten nötig sind.\n\n"
        f"Aufgabe:\n{question}"
    )
    payload = build_gemini_payload(prompt)
    return request_gemini(payload, timeout=timeout)


def request_ki_image(question: str, bbox) -> str:
    if ImageGrab is None:
        return "ImageGrab nicht verfügbar"

    try:
        if not bbox or len(bbox) != 4:
            return "Screenshot-Auswahl ungültig"

        left, top, right, bottom = [int(v) for v in bbox]
        if right <= left or bottom <= top:
            return "Screenshot-Auswahl ungültig"
        if (right - left) < 5 or (bottom - top) < 5:
            return "Auswahl zu klein"

        img = ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        image_bytes = buf.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            f"{KI_QA_DEFAULT_INSTRUCTION}\n\n"
            "Du bekommst einen Screenshot. Lies nur den relevanten Aufgabeninhalt aus dem Bild. "
            "Ignoriere Überschriften, Fragetitel, Aufgabennamen und Einleitungstexte. "
            "Nutze Google Search nur dann, wenn aktuelle Informationen, Webseiten, Software-Dokumentation oder externe Fakten nötig sind. "
            "Gib ausschließlich das aus, was als finale Lösung eingetragen werden muss.\n\n"
            f"Aufgabe:\n{question or 'Löse die Aufgabe im Screenshot.'}"
        )

        payload = build_gemini_payload(prompt, image_base64=image_base64)
        return request_gemini(payload, timeout=(5, 180))

    except Exception as e:
        log_error(f"Gemini Vision Fehler: {repr(e)}")
        return f"Gemini Fehler: {type(e).__name__}"


def ask_ai_async(question: str):
    set_processing(True)

    def work():
        return request_ki_text(question)

    def done(answer):
        set_processing(False)
        set_answer_bindings()
        show_answer(answer)

    run_worker(work, done, fallback_error="KI Fehler")


# ------------------------------------------------------------
# POSITION / GEOMETRIE
# ------------------------------------------------------------

def compute_position(sw, sh, w, h):
    pos = POSITION
    if pos == "top_left":
        x, y = 0, 0
    elif pos == "top_center":
        x, y = (sw - w) // 2, 0
    elif pos == "top_right":
        x, y = sw - w, 0
    elif pos == "center_left":
        x, y = 0, (sh - h) // 2
    elif pos == "center":
        x, y = (sw - w) // 2, (sh - h) // 2
    elif pos == "center_right":
        x, y = sw - w, (sh - h) // 2
    elif pos == "bottom_left":
        x, y = 0, sh - h
    elif pos == "bottom_center":
        x, y = (sw - w) // 2, sh - h
    elif pos == "bottom_right":
        x, y = sw - w, sh - h
    else:
        x, y = sw - w, 0

    x += OFFSET_X
    y += OFFSET_Y
    x = max(0, min(sw - w, x))
    y = max(0, min(sh - h, y))
    return x, y


def recalc_overlay_geometry():
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()

    wrap = int(sw * MAX_WIDTH_RATIO)
    label.configure(wraplength=wrap)
    overlay.update_idletasks()

    w = max(label.winfo_reqwidth(), 40)
    h = max(label.winfo_reqheight(), FONT_SIZE + 8)

    bg_w = w if BACKGROUND_WIDTH is None else max(BACKGROUND_WIDTH, 40)
    bg_h = h if BACKGROUND_HEIGHT is None else max(BACKGROUND_HEIGHT, FONT_SIZE + 8)

    x, y = compute_position(sw, sh, bg_w, bg_h)
    overlay.geometry(f"{bg_w}x{bg_h}+{x}+{y}")


# ------------------------------------------------------------
# SCREEN CAPTURE / KI IMAGE
# ------------------------------------------------------------

def wait_for_two_clicks():
    if mouse is None:
        return "pynput nicht verfügbar"

    points = []
    print("Klicke Punkt 1 oben-links, danach Punkt 2 unten-rechts.")

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            points.append((x, y))
            print(f"Punkt {len(points)}: {x}, {y}")
            if len(points) >= 2:
                return False
        return None

    try:
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
    except Exception as e:
        log_error(f"Mouse Listener Fehler: {repr(e)}")
        return "Mausauswahl Fehler"

    if len(points) < 2:
        return "Auswahl abgebrochen"

    (x1, y1), (x2, y2) = points
    left, right = sorted([x1, x2])
    top, bottom = sorted([y1, y2])

    if right - left < 5 or bottom - top < 5:
        return "Auswahl zu klein"

    return left, top, right, bottom


def start_mouse_capture_and_ocr_async():
    global listening, buffer, current_letter, app_mode, image_capture_running

    if image_capture_running:
        return "break"

    app_mode = MODE_AI_IMAGE
    image_capture_running = True
    listening = False
    buffer = ""
    current_letter = "a"

    clear_mode_bindings()
    overlay.withdraw()
    set_status(MAGENTA)

    def work():
        bbox = wait_for_two_clicks()
        if isinstance(bbox, str):
            return bbox

        prompt = (
            "Löse die Aufgabe im Screenshot. "
            "Gib ausschließlich die finale Lösung aus. "
            "Wiederhole keine Frage und keinen Aufgabentitel. "
            "Schreibe keine Erklärung. "
            "Mehrere Antworten exakt mit | trennen. "
            "Zuordnungen exakt im Format Teil1 > Teil2 | Teil3 > Teil4."
            "Es kann auch sein, dass die Auswahl im Screenshot falsch ist und du sollst das Überprüfen bzw die Korrekte Antwort geben."
        )
        return request_ki_image(prompt, bbox)

    def done(answer):
        global app_mode, image_capture_running
        image_capture_running = False
        app_mode = MODE_IDLE
        set_status(ORANGE)
        set_answer_bindings()
        show_answer(answer if answer else "Keine Antwort von Gemini")

    run_worker(work, done, fallback_error="KI Fehler")
    return "break"


# ------------------------------------------------------------
# ANSWER STATE
# ------------------------------------------------------------

current_answers = []
current_answer_index = 0
current_variants = []
current_variant_index = 0

MODE_IDLE = "idle"
MODE_WRITE = "write"
MODE_AI_TEXT = "ai_text"
MODE_AI_IMAGE = "ai_image"

app_mode = MODE_IDLE
image_capture_running = False

listening = False
buffer = ""
current_letter = "a"


def split_variants(text: str) -> list[str]:
    text = normalize_ai_answer(text)
    if not text:
        return ["Keine Antwort"]
    if "|" not in text:
        return [text.strip()]

    parts = []
    for p in text.split("|"):
        p = normalize_ai_answer(p)
        if p:
            parts.append(p)

    return parts if parts else ["Keine Antwort"]


def load_answer_at(index: int, variant_index: int = 0):
    global current_answer_index, current_variants, current_variant_index

    if not current_answers:
        current_answer_index = 0
        current_variants = []
        current_variant_index = 0
        return

    current_answer_index = index % len(current_answers)
    current_variants = split_variants(current_answers[current_answer_index])
    current_variant_index = max(0, min(variant_index, len(current_variants) - 1))


def update_label_with_current_variant():
    if not current_answers:
        label.configure(text="(keine Antwort)", anchor="w", fg=RED)
        return

    total_q = len(current_answers)
    q_idx = current_answer_index + 1

    base_txt = current_variants[current_variant_index] if current_variants else "Keine Antwort"
    total_v = len(current_variants) if current_variants else 1
    v_idx = current_variant_index + 1

    prefix = ""
    if total_q > 1:
        prefix += f"Q: {q_idx}/{total_q}  "
    if total_v > 1:
        prefix += f"{v_idx}/{total_v}  "

    label.configure(text=prefix + base_txt, anchor="w", fg=TEXT_COLOR)


def force_show_overlay():
    try:
        recalc_overlay_geometry()
        overlay.deiconify()
        overlay.update_idletasks()
        overlay.attributes("-topmost", False)
        overlay.attributes("-topmost", True)
        overlay.lift()
        overlay.focus_force()
    except Exception as e:
        log_error(f"force_show_overlay Fehler: {repr(e)}")


def show_answer(answers):
    global current_answers

    try:
        log_error(f"RAW ANSWER: {repr(answers)}")

        if answers is None:
            current_answers = []
        elif isinstance(answers, list):
            current_answers = [normalize_answer_text(a) for a in answers if normalize_answer_text(a)]
        else:
            cleaned = normalize_answer_text(answers)
            current_answers = [cleaned] if cleaned else []

        if not current_answers:
            current_answers = ["Keine Antwort vom Server"]

        load_answer_at(0, 0)
        update_label_with_current_variant()
        force_show_overlay()

    except Exception as e:
        log_error(f"show_answer Fehler: {repr(e)}")
        label.configure(text=f"Anzeige Fehler: {type(e).__name__}", anchor="w", fg=RED)
        force_show_overlay()


def refresh_answer_view():
    try:
        update_label_with_current_variant()
        force_show_overlay()
    except Exception as e:
        log_error(f"refresh_answer_view Fehler: {repr(e)}")


def next_answer(event=None):
    if not current_answers:
        return "break"
    load_answer_at(current_answer_index + 1, 0)
    refresh_answer_view()
    return "break"


def prev_answer(event=None):
    if not current_answers:
        return "break"
    load_answer_at(current_answer_index - 1, 0)
    refresh_answer_view()
    return "break"


def next_variant(event=None):
    global current_variant_index
    if not current_answers:
        return "break"
    if current_variant_index < len(current_variants) - 1:
        current_variant_index += 1
    else:
        load_answer_at(current_answer_index + 1, 0)
    refresh_answer_view()
    return "break"


def prev_variant(event=None):
    global current_variant_index
    if not current_answers:
        return "break"
    if current_variant_index > 0:
        current_variant_index -= 1
    else:
        previous_answer_index = (current_answer_index - 1) % len(current_answers)
        previous_variants = split_variants(current_answers[previous_answer_index])
        load_answer_at(previous_answer_index, len(previous_variants) - 1)
    refresh_answer_view()
    return "break"


def scroll_answers(event):
    num = getattr(event, "num", None)
    delta = getattr(event, "delta", 0)
    if delta < 0 or num == 5:
        return next_variant()
    return prev_variant()


# ------------------------------------------------------------
# BINDINGS
# ------------------------------------------------------------

MODE_BINDINGS = [
    "<KeyPress>", "<MouseWheel>", "<Button-2>", "<Button-3>", "<Button-4>", "<Button-5>",
    "<Return>", "<KP_Enter>", "<Right>", "<Left>", "<Shift_R>",
]


def clear_mode_bindings():
    for seq in MODE_BINDINGS:
        try:
            root.unbind_all(seq)
        except Exception:
            pass


def set_answer_bindings():
    clear_mode_bindings()
    root.bind_all("<MouseWheel>", scroll_answers)
    root.bind_all("<Button-4>", scroll_answers)
    root.bind_all("<Button-5>", scroll_answers)
    root.bind_all("<Button-2>", next_answer)
    root.bind_all("<Button-3>", next_answer)
    root.bind_all("<Return>", next_answer)
    root.bind_all("<KP_Enter>", next_answer)
    root.bind_all("<Right>", next_variant)
    root.bind_all("<Left>", prev_variant)
    root.bind_all("<Shift_R>", close_app)


def set_search_bindings():
    clear_mode_bindings()
    root.bind_all("<KeyPress>", handle_key)
    root.bind_all("<MouseWheel>", on_scroll)
    root.bind_all("<Button-4>", on_scroll)
    root.bind_all("<Button-5>", on_scroll)
    root.bind_all("<Button-3>", lambda event: handle_search_query(buffer))
    root.bind_all("<Return>", lambda event: handle_search_query(buffer))
    root.bind_all("<KP_Enter>", lambda event: handle_search_query(buffer))
    root.bind_all("<Shift_R>", close_app)


# ------------------------------------------------------------
# SEARCH / NORMALIZE
# ------------------------------------------------------------

def normalize(s: str) -> str:
    return " ".join(str(s).lower().split())


def get_initials(s):
    words = [w for w in str(s).split() if w and w[0].isalpha()]
    return "".join(w[0].lower() for w in words)


def find_answer(query):
    answers = []
    q = normalize(query)
    if not q:
        return answers

    if " " in q:
        for key in QA:
            if q in normalize(key):
                answers.append(QA[key])
        return answers

    if len(q) >= 2 and q.isalpha():
        for key in QA:
            if get_initials(key).startswith(q):
                answers.append(QA[key])

    return answers


# ------------------------------------------------------------
# LISTENING OVERLAY
# ------------------------------------------------------------

def update_overlay_text(text: str):
    label.configure(text=text, fg=TEXT_COLOR)
    overlay.update_idletasks()
    recalc_overlay_geometry()
    overlay.deiconify()
    overlay.lift()


def update_listening_overlay():
    if app_mode == MODE_AI_TEXT:
        update_overlay_text(f"KI: {buffer}{current_letter}")
        return

    n = len(find_answer(buffer)) if buffer else 0
    update_overlay_text(f"{buffer}{current_letter} | A: {n}")


def start_listening():
    global app_mode, listening, buffer, current_letter
    app_mode = MODE_WRITE
    listening = True
    buffer = ""
    current_letter = "a"
    set_status(GREEN)
    set_search_bindings()
    update_listening_overlay()
    overlay.deiconify()
    overlay.lift()
    overlay.focus_force()


def start_ai_text_mode():
    global app_mode, listening, buffer, current_letter
    app_mode = MODE_AI_TEXT
    listening = True
    buffer = ""
    current_letter = "a"
    set_status(BLUE)
    set_search_bindings()
    update_listening_overlay()
    overlay.deiconify()
    overlay.lift()
    overlay.focus_force()


def stop_listening():
    global app_mode, listening, buffer, current_letter
    app_mode = MODE_IDLE
    listening = False
    buffer = ""
    current_letter = "a"
    clear_mode_bindings()
    set_status(ORANGE)
    overlay.withdraw()


def on_status_click(event=None):
    global app_mode

    if image_capture_running:
        # Während die Screenshot-Auswahl läuft, wird nicht weitergeschaltet,
        # damit der Status-Klick nicht versehentlich als Auswahlpunkt zählt.
        return "break"

    if app_mode == MODE_IDLE:
        start_listening()
    elif app_mode == MODE_WRITE:
        start_ai_text_mode()
    elif app_mode == MODE_AI_TEXT:
        # Kleiner Abstand, damit der Klick auf den Status-Button
        # nicht als erster Screenshot-Punkt aufgenommen wird.
        set_status(MAGENTA)
        overlay.withdraw()
        root.after(150, start_mouse_capture_and_ocr_async)
    else:
        stop_listening()

    return "break"


def set_status_win_binds():
    status_win.bind("<Button-1>", on_status_click)
    status_win.bind("<Shift_R>", close_app)


# ------------------------------------------------------------
# LETTER CONTROL
# ------------------------------------------------------------

def get_next_letter(s: str) -> str:
    if not s:
        return s
    last_char = s[-1]
    if last_char.isalpha():
        if last_char == "z":
            return s[:-1] + "a"
        if last_char == "Z":
            return s[:-1] + "A"
        return s[:-1] + chr(ord(last_char) + 1)
    return s


def get_prev_letter(s: str) -> str:
    if not s:
        return s
    last_char = s[-1]
    if last_char.isalpha():
        if last_char == "a":
            return s[:-1] + "z"
        if last_char == "A":
            return s[:-1] + "Z"
        return s[:-1] + chr(ord(last_char) - 1)
    return s


def next_letter(event=None):
    global current_letter
    current_letter = get_next_letter(current_letter)
    if listening:
        update_listening_overlay()
    return "break"


def prev_letter(event=None):
    global current_letter
    current_letter = get_prev_letter(current_letter)
    if listening:
        update_listening_overlay()
    return "break"


def on_scroll(event):
    num = getattr(event, "num", None)
    delta = getattr(event, "delta", 0)
    if delta < 0 or num == 5:
        return next_letter()
    return prev_letter()


# ------------------------------------------------------------
# KI REQUEST CHECK / KEY HANDLING
# ------------------------------------------------------------

def is_ki_request(text: str) -> tuple[bool, str]:
    text = str(text)
    if text.endswith("?") and boolean_ki_enabled:
        print("KI enabled.")
        return True, text[:-1].strip()
    print("Not a KI request.", boolean_ki_enabled)
    return False, text


def handle_key(event):
    global listening, buffer, current_letter

    if not listening:
        return "break"

    ks = getattr(event, "keysym", "")
    ch = getattr(event, "char", "")

    if ks in ("space", "Space") or ch == " ":
        buffer += " "
        update_listening_overlay()
        return "break"

    if ks == "Right":
        current_letter = get_next_letter(current_letter)
        update_listening_overlay()
        return "break"

    if ks == "Left":
        current_letter = get_prev_letter(current_letter)
        update_listening_overlay()
        return "break"

    if ks == "Up":
        buffer += current_letter
        current_letter = "a"
        update_listening_overlay()
        return "break"

    if ks == "Down":
        start_mouse_capture_and_ocr_async()
        return "break"

    if ks == "BackSpace":
        if buffer:
            buffer = buffer[:-1]
        current_letter = "a"
        update_listening_overlay()
        return "break"

    if ks == "semicolon" or ch == ";":
        handle_search_query(buffer)
        return "break"

    if ch and ch.isprintable() and len(ch) == 1:
        buffer += ch.lower()
        current_letter = "a"
        update_listening_overlay()
        return "break"

    return "break"


def handle_search_query(query_text: str):
    global app_mode, listening, buffer, current_letter

    final_text = str(query_text).strip()
    submit_mode = app_mode

    app_mode = MODE_IDLE
    listening = False
    buffer = ""
    current_letter = "a"
    overlay.withdraw()

    if final_text.lower() == "delete":
        return close_app()

    if submit_mode == MODE_AI_TEXT:
        if final_text:
            ask_ai_async(final_text)
        else:
            clear_mode_bindings()
            set_status(RED)
            status_win.after(600, lambda: set_status(ORANGE))
        return "break"

    is_ki, question = is_ki_request(final_text)
    if is_ki:
        ask_ai_async(question)
        return "break"

    ans = find_answer(final_text)
    if ans:
        set_status(ORANGE)
        set_answer_bindings()
        show_answer(ans)
    else:
        clear_mode_bindings()
        set_status(RED)
        status_win.after(600, lambda: set_status(ORANGE))

    return "break"


# ------------------------------------------------------------
# START
# ------------------------------------------------------------

set_status(ORANGE)
set_status_win_binds()
status_refresher()
root.mainloop()