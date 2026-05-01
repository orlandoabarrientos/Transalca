import re
import unicodedata
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rapidocr_onnxruntime import RapidOCR


class OCRError(RuntimeError):
    pass


_OCR_ENGINE = RapidOCR()

_FIELDS = [
    "placa",
    "marca",
    "modelo",
    "anio",
    "color",
    "tipo_vehiculo",
    "clase",
    "tipo_combustible",
    "vin",
    "serial_motor",
    "capacidad",
    "uso",
    "propietario_nombre",
    "propietario_cedula",
    "direccion",
]

_ALIASES = {
    "placa": ["placa"],
    "marca": ["marca"],
    "modelo": ["modelo", "mode lo"],
    "anio": ["ano", "año"],
    "color": ["color"],
    "tipo_vehiculo": ["tipo vehiculo", "tipo"],
    "clase": ["clase"],
    "tipo_combustible": ["combustible"],
    "vin": ["serial de carroceria", "serial carroceria", "vin"],
    "serial_motor": ["serial de motor", "motor"],
    "capacidad": ["capacidad"],
    "uso": ["uso"],
    "propietario_nombre": ["nombre"],
    "propietario_cedula": ["cedula de identidad", "cedula"],
    "direccion": ["direccion"],
}

_STOP_LABELS = [
    "placa",
    "marca",
    "modelo",
    "ano",
    "año",
    "color",
    "tipo",
    "clase",
    "combustible",
    "serial",
    "vin",
    "capacidad",
    "uso",
    "nombre",
    "cedula",
    "direccion",
]


def _strip_accents(value: str) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _plain(value: str) -> str:
    text = _strip_accents(value or "")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip().lower()


def _clean_spaces(value: str) -> str:
    return re.sub(r"\s{2,}", " ", (value or "").strip())


def _looks_like_label(text_plain: str) -> bool:
    if not text_plain:
        return True
    t = text_plain.strip(" :.-")
    if len(t) <= 1:
        return True
    for token in _STOP_LABELS:
        if t == token:
            return True
    if ":" in t and len(t) < 40:
        left = t.split(":", 1)[0].strip()
        for token in _STOP_LABELS:
            if token in left:
                return True
    return False


def _trim_with_next_labels(value: str) -> str:
    if not value:
        return ""
    raw = _clean_spaces(value)
    plain = _plain(raw)
    cut = len(raw)
    for token in _STOP_LABELS:
        idx = plain.find(token)
        if idx > 0:
            cut = min(cut, idx)
    trimmed = raw[:cut]
    trimmed = trimmed.strip(" -:;,.")
    return _clean_spaces(trimmed)


def _to_text_value(value: str) -> str:
    out = _trim_with_next_labels(value)
    out = re.sub(r"^[\-:]+", "", out).strip()
    return out


def _beautify_text(value: str) -> str:
    text = _clean_spaces(value)
    if not text:
        return ""
    words = []
    for w in text.split(" "):
        if not w:
            continue
        if any(ch.isdigit() for ch in w):
            words.append(w)
            continue
        words.append(w[:1].upper() + w[1:])
    return " ".join(words)


def _to_plate(value: str) -> str:
    text = (value or "").upper()
    match = re.search(r"\b([A-Z]{1,3}\s?-?\d{2,4}\s?-?[A-Z]{1,3})\b", text)
    if not match:
        match = re.search(r"\b([A-Z]{2}\d{3}[A-Z]{2})\b", text)
    if not match:
        return ""
    return re.sub(r"[^A-Z0-9]", "", match.group(1))


def _to_year(value: str):
    match = re.search(r"\b(19[5-9]\d|20\d{2}|21\d{2})\b", value or "")
    if not match:
        return None
    try:
        year = int(match.group(1))
        if 1950 <= year <= 2120:
            return year
    except ValueError:
        return None
    return None


def _to_fuel(value: str) -> str:
    t = _plain(value)
    if re.search(r"gas[o0]l?i+n?a", t):
        return "gasolina"
    if re.search(r"gas[o0]i+l", t) or "diesel" in t or "diésel" in t or "diesei" in t:
        return "gasoil"
    if "otro" in t:
        return "otro"
    return ""


def _to_cedula(value: str) -> str:
    text = (value or "").upper()
    text = text.replace(" ", "")
    match = re.search(r"\b([VEJG]-?\d{6,10})\b", text)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{6,10})\b", text)
    return match.group(1) if match else ""


def _to_vin(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
    if len(text) >= 8:
        return text
    return ""


def _normalize_for_field(field: str, value: str):
    if field == "placa":
        return _to_plate(value)
    if field == "anio":
        return _to_year(value)
    if field == "tipo_combustible":
        return _to_fuel(value)
    if field == "propietario_cedula":
        return _to_cedula(value)
    if field in ("vin", "serial_motor"):
        return _to_vin(value)
    out = _to_text_value(value)
    if not out:
        return ""
    if field in ("marca", "modelo", "color", "tipo_vehiculo", "clase", "capacidad", "uso", "propietario_nombre"):
        return _beautify_text(out)
    if field == "direccion":
        return _beautify_text(out)
    return _beautify_text(out)


def _field_weight(field: str) -> float:
    if field in ("placa", "marca", "modelo", "anio"):
        return 3.0
    if field in ("color", "tipo_vehiculo", "tipo_combustible"):
        return 2.0
    if field in ("vin", "serial_motor"):
        return 1.5
    return 1.0


def _extract_inline_for_alias(text_raw: str, text_plain: str, alias: str) -> str:
    a = alias.strip().lower()
    if a in text_plain and ":" in text_raw:
        right = text_raw.split(":", 1)[1].strip()
        if right:
            return right
    pattern = re.compile(rf"\b{re.escape(a)}\b\s*[:\-]?\s*(.+)$", re.IGNORECASE)
    match = pattern.search(text_plain)
    return match.group(1).strip() if match else ""


def _alias_match_score(text_plain: str, alias: str) -> float:
    a = alias.strip().lower()
    if text_plain == a or text_plain == f"{a}:":
        return 1.0
    if text_plain.startswith(a + ":") or text_plain.startswith(a + " "):
        return 0.95
    if a in text_plain:
        return 0.75
    return 0.0


def _entry_metrics(box):
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    x1, x2 = float(min(xs)), float(max(xs))
    y1, y2 = float(min(ys)), float(max(ys))
    return {
        "x1": x1,
        "x2": x2,
        "y1": y1,
        "y2": y2,
        "cx": (x1 + x2) / 2.0,
        "cy": (y1 + y2) / 2.0,
        "w": max(1.0, x2 - x1),
        "h": max(1.0, y2 - y1),
    }


def _ocr_entries(img_arr: np.ndarray) -> List[Dict]:
    try:
        result, _ = _OCR_ENGINE(img_arr)
    except Exception:
        return []
    if not result:
        return []
    entries = []
    for item in result:
        if not item or len(item) < 2:
            continue
        box = item[0]
        text_raw = _clean_spaces(str(item[1] or ""))
        if not text_raw:
            continue
        conf = 0.5
        if len(item) >= 3:
            try:
                conf = float(item[2])
            except Exception:
                conf = 0.5
        metrics = _entry_metrics(box)
        text_plain = _plain(text_raw)
        if not text_plain:
            continue
        entries.append({
            "raw": text_raw,
            "plain": text_plain,
            "conf": conf,
            **metrics,
        })
    return entries


def _nearest_value_right(label_entry: Dict, entries: List[Dict]):
    best = None
    best_score = -1e9
    max_y = max(20.0, label_entry["h"] * 1.2)
    for e in entries:
        if e is label_entry:
            continue
        if e["x1"] < label_entry["x2"] - 4:
            continue
        if abs(e["cy"] - label_entry["cy"]) > max_y:
            continue
        if _looks_like_label(e["plain"]):
            continue
        dx = e["x1"] - label_entry["x2"]
        dy = abs(e["cy"] - label_entry["cy"])
        score = (e["conf"] * 2.0) - (dx * 0.002) - (dy * 0.01)
        if score > best_score:
            best = e
            best_score = score
    return best


def _nearest_value_below(label_entry: Dict, entries: List[Dict]):
    best = None
    best_score = -1e9
    max_y_dist = max(35.0, label_entry["h"] * 3.2)
    max_x = max(120.0, label_entry["w"] * 0.8)
    for e in entries:
        if e is label_entry:
            continue
        if e["y1"] < label_entry["y2"] - 2:
            continue
        if (e["y1"] - label_entry["y2"]) > max_y_dist:
            continue
        if abs(e["cx"] - label_entry["cx"]) > max_x:
            continue
        if _looks_like_label(e["plain"]):
            continue
        dy = e["y1"] - label_entry["y2"]
        dx = abs(e["cx"] - label_entry["cx"])
        score = (e["conf"] * 2.0) - (dy * 0.03) - (dx * 0.01)
        if score > best_score:
            best = e
            best_score = score
    return best


def _build_variants(image_arr: np.ndarray) -> List[np.ndarray]:
    img = Image.fromarray(image_arr).convert("RGB")
    variants = []
    for angle in (0, 90, 180, 270):
        rotated = img.rotate(angle, expand=True)
        variants.append(np.array(rotated))
        gray = ImageOps.autocontrast(rotated.convert("L"))
        sharp = gray.filter(ImageFilter.SHARPEN)
        variants.append(np.array(sharp.convert("RGB")))
        high = ImageEnhance.Contrast(gray).enhance(1.8)
        bw = high.point(lambda px: 255 if px > 155 else 0).convert("RGB")
        variants.append(np.array(bw))
    return variants


def _combine_text(entries: List[Dict]) -> str:
    if not entries:
        return ""
    ordered = sorted(entries, key=lambda e: (round(e["cy"] / 18), e["x1"]))
    return "\n".join(e["raw"] for e in ordered)


def _extract_from_entries(entries: List[Dict]) -> Tuple[Dict, float, int]:
    candidates = {field: {"value": "", "score": -1.0} for field in _FIELDS}

    def set_candidate(field: str, value, score: float):
        if value is None or value == "":
            return
        current = candidates[field]
        if score > current["score"]:
            current["value"] = value
            current["score"] = score

    for e in entries:
        for field, aliases in _ALIASES.items():
            for alias in aliases:
                strength = _alias_match_score(e["plain"], alias)
                if strength <= 0:
                    continue
                inline = _extract_inline_for_alias(e["raw"], e["plain"], alias)
                if inline:
                    normalized = _normalize_for_field(field, inline)
                    set_candidate(field, normalized, e["conf"] + strength + 0.45)

    for e in entries:
        for field, aliases in _ALIASES.items():
            best_strength = 0.0
            for alias in aliases:
                best_strength = max(best_strength, _alias_match_score(e["plain"], alias))
            if best_strength < 0.75:
                continue
            right = _nearest_value_right(e, entries)
            if right:
                normalized = _normalize_for_field(field, right["raw"])
                set_candidate(field, normalized, (e["conf"] + right["conf"]) / 2.0 + best_strength + 0.3)
            below = _nearest_value_below(e, entries)
            if below:
                normalized = _normalize_for_field(field, below["raw"])
                set_candidate(field, normalized, (e["conf"] + below["conf"]) / 2.0 + best_strength)

    all_text = "\n".join(e["raw"] for e in entries)
    if not candidates["placa"]["value"]:
        set_candidate("placa", _to_plate(all_text), 0.45)
    if not candidates["anio"]["value"]:
        set_candidate("anio", _to_year(all_text), 0.45)
    if not candidates["tipo_combustible"]["value"]:
        set_candidate("tipo_combustible", _to_fuel(all_text), 0.35)
    if not candidates["vin"]["value"]:
        vin_match = re.search(r"\b([A-HJ-NPR-Z0-9]{11,20})\b", all_text.upper())
        if vin_match:
            set_candidate("vin", vin_match.group(1), 0.35)

    parsed = {field: candidates[field]["value"] for field in _FIELDS}
    if not parsed.get("tipo_vehiculo") and parsed.get("clase"):
        parsed["tipo_vehiculo"] = parsed["clase"]

    score = 0.0
    for field in _FIELDS:
        value = parsed.get(field)
        if value is None or value == "":
            continue
        weight = _field_weight(field)
        confidence = max(0.0, candidates[field]["score"])
        score += weight + min(confidence, 1.5) * 0.5

    core_fields = ("placa", "marca", "modelo", "anio", "color", "tipo_vehiculo", "tipo_combustible")
    core_filled = 0
    for field in core_fields:
        value = parsed.get(field)
        if value is None or value == "":
            continue
        core_filled += 1

    return parsed, score, core_filled


def _read_as_rgb_array(file_storage):
    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream).convert("RGB")
        return np.array(img)
    except Exception as exc:
        raise OCRError("No se pudo abrir la imagen para OCR") from exc


def parse_vehicle_title_image(file_storage) -> Tuple[Dict, str]:
    base = _read_as_rgb_array(file_storage)
    variants = _build_variants(base)
    best_data = None
    best_text = ""
    best_score = -1.0
    best_core = -1

    for arr in variants:
        entries = _ocr_entries(arr)
        if not entries:
            continue
        parsed, score, core_filled = _extract_from_entries(entries)
        text = _combine_text(entries)
        if core_filled > best_core or (core_filled == best_core and score > best_score):
            best_score = score
            best_core = core_filled
            best_data = parsed
            best_text = text
        if core_filled >= 7 and score >= 17.0:
            break

    if not best_data:
        raise OCRError("No se detecto texto en la imagen")

    if not any(best_data.get(k) for k in ("placa", "marca", "modelo", "anio", "tipo_combustible", "color")):
        raise OCRError("No se pudieron detectar datos del vehiculo")

    inferred_fuel = _to_fuel(best_text)
    current_fuel = (best_data.get("tipo_combustible") or "").strip().lower()
    if inferred_fuel in ("gasolina", "gasoil"):
        best_data["tipo_combustible"] = inferred_fuel
    elif not current_fuel:
        best_data["tipo_combustible"] = "gasolina"

    return best_data, best_text
