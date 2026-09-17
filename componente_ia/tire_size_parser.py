from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable

@dataclass(frozen=True)
class ParsedTireSize:

    raw: str
    normalized: str
    width: int | float
    aspect_ratio: int | None
    construction: str
    rim: int | float
    prefix: str | None
    format: str
    overall_diameter_in: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

TireSize = ParsedTireSize

_PREFIX = r"(?P<prefix>LT|P)?"
_SUFFIX_PREFIX = r"(?P<suffix_prefix>LT|P)?"
_METRIC_STANDARD = re.compile(
    rf"(?<![A-Z0-9]){_PREFIX}\s*(?P<width>\d{{3}})\s*[/ .-]\s*"
    rf"(?P<aspect>\d{{2}})\s*(?:R\s*|[/ .-]\s*)"
    rf"(?P<rim>\d{{2}}(?:\.5)?)\s*{_SUFFIX_PREFIX}\s*(?P<service>C)?(?![A-Z0-9])",
    re.IGNORECASE,
)
_METRIC_COMPACT_R = re.compile(
    rf"(?<![A-Z0-9]){_PREFIX}\s*(?P<width>\d{{3}})(?P<aspect>\d{{2}})"
    rf"R(?P<rim>\d{{2}}(?:\.5)?)\s*{_SUFFIX_PREFIX}\s*(?P<service>C)?(?![A-Z0-9])",
    re.IGNORECASE,
)
_METRIC_COMPACT = re.compile(
    rf"(?<![A-Z0-9]){_PREFIX}\s*(?P<width>\d{{3}})(?P<aspect>\d{{2}})"
    rf"(?P<rim>\d{{2}})\s*{_SUFFIX_PREFIX}(?![A-Z0-9])",
    re.IGNORECASE,
)
_RIM_FIRST = re.compile(
    rf"(?<![A-Z0-9])(?:R(?:IN)?|ARO)\s*(?P<rim>\d{{2}}(?:\.5)?)\s*[,;:-]?\s*"
    rf"{_PREFIX}\s*(?P<width>\d{{3}})\s*[/ .-]\s*(?P<aspect>\d{{2}})"
    rf"\s*{_SUFFIX_PREFIX}(?![A-Z0-9])",
    re.IGNORECASE,
)
_FLOTATION = re.compile(
    r"(?<![A-Z0-9.])(?P<prefix>LT)?\s*(?P<diameter>\d{2}(?:\.\d{1,2})?)\s*[Xx]\s*"
    r"(?P<width>\d{1,2}(?:\.\d{1,2})?)\s*(?:R|-)?\s*"
    r"(?P<rim>\d{2}(?:\.5)?)\s*(?P<suffix_prefix>LT)?(?![A-Z0-9])",
    re.IGNORECASE,
)
_COMMERCIAL_DECIMAL = re.compile(
    r"(?<![A-Z0-9.])(?P<prefix>LT)?\s*(?P<width>\d{1,2}(?:\.\d{1,2})?)\s*(?:R|-)\s*"
    r"(?P<rim>\d{2}(?:\.5)?)(?![A-Z0-9])",
    re.IGNORECASE,
)
_COMMERCIAL_COMPACT = re.compile(
    r"(?<![A-Z0-9])(?P<prefix>LT)?\s*(?P<width>\d{3,4})\s*R\s*(?P<rim>\d{2}(?:\.5)?)(?![A-Z0-9])",
    re.IGNORECASE,
)
_METRIC_NO_ASPECT_C = re.compile(
    r"(?<![A-Z0-9])(?P<prefix>LT|P)?\s*(?P<width>\d{3})\s*R\s*"
    r"(?P<rim>\d{2}(?:\.5)?)\s*(?P<service>C)(?![A-Z0-9])",
    re.IGNORECASE,
)

def _ascii(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii")

def _number(value: str | int | float) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number

def _rim_text(value: int | float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{float(value):g}"

def _valid_rim(value: float) -> bool:
    return 10 <= value <= 26 and (value.is_integer() or value % 1 == 0.5)

def _valid_metric(width: int, aspect: int, rim: float) -> bool:
    return 125 <= width <= 445 and 20 <= aspect <= 95 and _valid_rim(rim)

def _prefix(match: re.Match[str]) -> str | None:
    before = (match.groupdict().get("prefix") or "").upper()
    after = (match.groupdict().get("suffix_prefix") or "").upper()
    if before and after and before != after:
        return None
    return before or after or None

def _metric_result(match: re.Match[str], raw: str | None = None) -> ParsedTireSize | None:
    width = int(match.group("width"))
    aspect = int(match.group("aspect"))
    rim_number = float(match.group("rim"))
    if not _valid_metric(width, aspect, rim_number):
        return None
    prefix = _prefix(match)
    service_suffix = (match.groupdict().get("service") or "").upper()
    rim = _number(rim_number)
    diameter = round((2 * width * (aspect / 100.0) / 25.4) + rim_number, 3)
    return ParsedTireSize(
        raw=(raw if raw is not None else match.group(0)).strip(),
        normalized=f"{prefix or ''}{width}/{aspect}R{_rim_text(rim)}{service_suffix}",
        width=width,
        aspect_ratio=aspect,
        construction="R",
        rim=rim,
        prefix=prefix,
        format="metric",
        overall_diameter_in=diameter,
    )

def _commercial_width_text(raw_width: str, *, compact: bool) -> tuple[str, float]:
    if compact:
        value = int(raw_width) / 100.0
        return f"{value:.2f}", value
    value = float(raw_width)
    if "." in raw_width:
        return f"{value:.2f}", value
    return str(int(value)), value

def _overlaps(start: int, end: int, occupied: Iterable[tuple[int, int]]) -> bool:
    return any(start < other_end and end > other_start for other_start, other_end in occupied)

def extract_tire_sizes(value: Any) -> list[ParsedTireSize]:

    text = _ascii(value).upper()
    found: list[tuple[int, int, ParsedTireSize]] = []
    occupied: list[tuple[int, int]] = []

    for pattern in (_RIM_FIRST, _METRIC_STANDARD, _METRIC_COMPACT_R, _METRIC_COMPACT):
        for match in pattern.finditer(text):
            if _overlaps(match.start(), match.end(), occupied):
                continue
            parsed = _metric_result(match)
            if parsed is None:
                continue
            found.append((match.start(), match.end(), parsed))
            occupied.append((match.start(), match.end()))

    for match in _FLOTATION.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        diameter = float(match.group("diameter"))
        width = float(match.group("width"))
        rim_number = float(match.group("rim"))
        if not (25 <= diameter <= 54 and 6 <= width <= 24 and _valid_rim(rim_number)):
            continue
        rim = _number(rim_number)
        diameter_value = _number(diameter)
        width_value = _number(width)
        prefix = (match.group("prefix") or match.group("suffix_prefix") or "").upper() or None
        normalized = f"{prefix or ''}{diameter_value}X{width_value}R{_rim_text(rim)}"
        parsed = ParsedTireSize(
            raw=match.group(0).strip(), normalized=normalized, width=width_value,
            aspect_ratio=None, construction="R", rim=rim, prefix=prefix,
            format="flotation", overall_diameter_in=diameter,
        )
        found.append((match.start(), match.end(), parsed))
        occupied.append((match.start(), match.end()))

    for match in _METRIC_NO_ASPECT_C.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        width = int(match.group("width"))
        rim_number = float(match.group("rim"))
        if not (125 <= width <= 445 and _valid_rim(rim_number)):
            continue
        rim = _number(rim_number)
        prefix = (match.group("prefix") or "").upper() or None
        parsed = ParsedTireSize(
            raw=match.group(0).strip(),
            normalized=f"{prefix or ''}{width}R{_rim_text(rim)}C",
            width=width, aspect_ratio=None, construction="R", rim=rim,
            prefix=prefix, format="commercial_metric", overall_diameter_in=None,
        )
        found.append((match.start(), match.end(), parsed))
        occupied.append((match.start(), match.end()))

    for pattern, compact in ((_COMMERCIAL_DECIMAL, False), (_COMMERCIAL_COMPACT, True)):
        for match in pattern.finditer(text):
            if _overlaps(match.start(), match.end(), occupied):
                continue
            raw_width = match.group("width")
            width_text, width = _commercial_width_text(raw_width, compact=compact)
            rim_number = float(match.group("rim"))
            if not (5 <= width <= 14 and _valid_rim(rim_number)):
                continue
            rim = _number(rim_number)
            prefix = (match.groupdict().get("prefix") or "").upper() or None
            parsed = ParsedTireSize(
                raw=match.group(0).strip(), normalized=f"{prefix or ''}{width_text}R{_rim_text(rim)}",
                width=width, aspect_ratio=None, construction="R", rim=rim,
                prefix=prefix, format="commercial", overall_diameter_in=None,
            )
            found.append((match.start(), match.end(), parsed))
            occupied.append((match.start(), match.end()))

    unique: list[ParsedTireSize] = []
    seen: set[str] = set()
    for _, _, parsed in sorted(found, key=lambda row: row[0]):
        if parsed.normalized not in seen:
            seen.add(parsed.normalized)
            unique.append(parsed)
    return unique

def parse_tire_size(value: Any) -> ParsedTireSize | None:

    sizes = extract_tire_sizes(value)
    return sizes[0] if sizes else None

def normalize_tire_size(value: Any) -> str | None:
    parsed = parse_tire_size(value)
    return parsed.normalized if parsed else None

def explain_tire_size(value: Any) -> dict[str, Any] | None:

    parsed = parse_tire_size(value)
    if parsed is None:
        return None
    result = parsed.to_dict()
    if parsed.format == "metric":
        result["meaning"] = {
            "width": f"{parsed.width} mm de ancho",
            "aspect_ratio": f"perfil {parsed.aspect_ratio}%",
            "construction": "construccion radial",
            "rim": f"rin {_rim_text(parsed.rim)}",
        }
    elif parsed.format == "flotation":
        result["meaning"] = {
            "overall_diameter": f"diametro aproximado {parsed.overall_diameter_in:g} pulgadas",
            "section_width": f"ancho {parsed.width:g} pulgadas",
            "construction": "construccion radial",
            "rim": f"rin {_rim_text(parsed.rim)}",
        }
    else:
        result["meaning"] = {
            "nominal_width": f"ancho nominal {parsed.width:g} pulgadas",
            "construction": "construccion radial",
            "rim": f"rin {_rim_text(parsed.rim)}",
        }
    return result

parse = parse_tire_size
extract = extract_tire_sizes
extract_tire_size = parse_tire_size

class TireSizeParser:

    parse = staticmethod(parse_tire_size)
    extract = staticmethod(extract_tire_sizes)
    normalize = staticmethod(normalize_tire_size)
    explain = staticmethod(explain_tire_size)

__all__ = [
    "ParsedTireSize", "TireSize", "TireSizeParser", "parse_tire_size", "normalize_tire_size",
    "extract_tire_size", "extract_tire_sizes", "explain_tire_size", "parse", "extract",
]
