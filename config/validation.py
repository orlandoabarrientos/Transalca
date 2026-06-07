import re
import time
from decimal import Decimal, InvalidOperation
from html import escape


PHONE_RE = re.compile(r"^04\d{9}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PERSON_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$", re.UNICODE)
SAFE_TEXT_RE = re.compile(r"^[^<>]{1,}$")
BAD_INPUT_RE = re.compile(r"(<\s*/?\s*script|<[^>]+>|on[a-z]+\s*=|javascript:|data:text/html)", re.IGNORECASE)
SERIAL_LIKE_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9\-]{8,}$")

DOCUMENT_PREFIXES = {"V", "E", "J", "G", "P"}
RIF_PREFIXES = {"J", "G", "V", "E", "P"}
SELECT_TAMPER_MESSAGE = "El valor seleccionado no es valido. Recargue la pagina e intentelo nuevamente."


def clean_string(value):
    if value is None:
        return ""
    return str(value).strip()


def has_unsafe_content(value):
    return bool(BAD_INPUT_RE.search(clean_string(value)))


def safe_display(value):
    return escape(clean_string(value), quote=True)


def require_text(errors, field, value, label, min_len=1, max_len=100, person=False, allow_serial=False):
    text = clean_string(value)
    if not text:
        errors[field] = f"{label} es obligatorio."
        return ""
    if len(text) < min_len:
        errors[field] = f"{label} debe tener al menos {min_len} caracteres."
        return ""
    if len(text) > max_len:
        errors[field] = f"{label} no puede superar {max_len} caracteres."
        return ""
    if has_unsafe_content(text) or not SAFE_TEXT_RE.match(text):
        errors[field] = f"{label} contiene caracteres no permitidos."
        return ""
    if person and not PERSON_RE.match(text):
        errors[field] = f"{label} solo puede contener letras y espacios."
        return ""
    if not person and not allow_serial and SERIAL_LIKE_RE.match(text):
        errors[field] = f"{label} no puede parecer un serial."
        return ""
    return text


def optional_text(errors, field, value, label, max_len=300, allow_serial=True, person=False):
    text = clean_string(value)
    if not text:
        return ""
    if len(text) > max_len:
        errors[field] = f"{label} no puede superar {max_len} caracteres."
        return ""
    if has_unsafe_content(text) or not SAFE_TEXT_RE.match(text):
        errors[field] = f"{label} contiene caracteres no permitidos."
        return ""
    if person and not PERSON_RE.match(text):
        errors[field] = f"{label} solo puede contener letras y espacios."
        return ""
    if not allow_serial and SERIAL_LIKE_RE.match(text):
        errors[field] = f"{label} no puede parecer un serial."
        return ""
    return text


def normalize_phone(errors, value, field="telefono", required=True):
    phone = re.sub(r"[\s\-\(\)]", "", clean_string(value))
    if not phone:
        if required:
            errors[field] = "El telefono es obligatorio."
        return ""
    if not PHONE_RE.match(phone):
        errors[field] = "El telefono debe tener 11 digitos y comenzar por 04. Ejemplo: 04121234567."
        return ""
    return phone


def normalize_email(errors, value, field="email", required=True):
    email = clean_string(value).lower()
    if not email:
        if required:
            errors[field] = "El correo es obligatorio."
        return ""
    if len(email) > 150 or not EMAIL_RE.match(email) or has_unsafe_content(email):
        errors[field] = "Ingrese un correo valido."
        return ""
    return email


def _split_document(raw):
    text = clean_string(raw).upper().replace(".", "")
    if not text:
        return "", ""
    compact = re.sub(r"[^A-Z0-9]", "", text)
    if len(compact) < 2:
        return "", ""
    return compact[0], compact[1:]


def normalize_cedula(errors, data, field="cedula", required=True):
    prefix = clean_string(data.get(f"{field}_prefijo") or data.get("cedula_prefijo")).upper()
    number = re.sub(r"\D", "", clean_string(data.get(f"{field}_numero") or data.get("cedula_numero")))
    raw = data.get(field)
    if raw and (not prefix or not number):
        prefix, number = _split_document(raw)
    if not prefix and not number:
        if required:
            errors[field] = "La cedula es obligatoria."
        return "", "", ""
    if prefix not in DOCUMENT_PREFIXES or not re.fullmatch(r"\d{7,8}", number or ""):
        errors[field] = "La cedula debe tener prefijo valido y 7 u 8 digitos."
        return "", "", ""
    return f"{prefix}-{number}", prefix, number


def normalize_rif(errors, data, field="rif", required=True):
    prefix = clean_string(data.get(f"{field}_prefijo") or data.get("rif_prefijo")).upper()
    number = re.sub(r"\D", "", clean_string(data.get(f"{field}_numero") or data.get("rif_numero")))
    raw = clean_string(data.get(field)).upper()
    if raw and (not prefix or not number):
        prefix, number = _split_document(raw)
    if not prefix and not number:
        if required:
            errors[field] = "El rif es obligatorio."
        return "", "", ""
    if prefix not in RIF_PREFIXES or not re.fullmatch(r"\d{9}", number or ""):
        errors[field] = "El rif debe tener prefijo valido y 9 digitos. Ejemplo: J-12345678-9."
        return "", "", ""
    return f"{prefix}-{number[:8]}-{number[8]}", prefix, number


def normalize_decimal(errors, field, value, label, min_value=Decimal("0.01"), max_value=Decimal("99999999.99")):
    raw = clean_string(value)
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        errors[field] = f"{label} debe ser numerico."
        return None
    if amount < min_value or amount > max_value:
        errors[field] = f"{label} debe ser mayor a {min_value}."
        return None
    if amount.as_tuple().exponent < -2:
        errors[field] = f"{label} puede tener maximo dos decimales."
        return None
    return amount


def normalize_int(errors, field, value, label, min_value=1, max_value=999999):
    raw = clean_string(value)
    try:
        number = int(raw)
    except (ValueError, TypeError):
        errors[field] = f"{label} debe ser un numero entero."
        return None
    if number < min_value or number > max_value:
        errors[field] = f"{label} debe estar entre {min_value} y {max_value}."
        return None
    return number


def validate_choice(errors, field, value, allowed):
    text = clean_string(value)
    if text not in allowed:
        errors[field] = SELECT_TAMPER_MESSAGE
        return ""
    return text


class LoginThrottle:
    def __init__(self, max_attempts=5, window_seconds=600):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = {}

    def key(self, ip, email):
        return f"{ip or 'unknown'}:{clean_string(email).lower()}"

    def is_locked(self, ip, email):
        key = self.key(ip, email)
        now = time.time()
        attempts = [ts for ts in self._attempts.get(key, []) if now - ts < self.window_seconds]
        self._attempts[key] = attempts
        return len(attempts) >= self.max_attempts

    def register_failure(self, ip, email):
        key = self.key(ip, email)
        now = time.time()
        attempts = [ts for ts in self._attempts.get(key, []) if now - ts < self.window_seconds]
        attempts.append(now)
        self._attempts[key] = attempts

    def clear(self, ip, email):
        self._attempts.pop(self.key(ip, email), None)
