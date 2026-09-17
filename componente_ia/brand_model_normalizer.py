from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable

KNOWN_BRANDS: tuple[str, ...] = (
    "BFGOODRICH", "BRIDGESTONE", "CONTINENTAL", "DOUBLESTAR",
    "FIRESTONE", "GOODYEAR", "MICHELIN", "PIRELLI", "YOKOHAMA",
    "ROYAL BLACK", "TDI TIRES", "V-RICH", "SUPERMEALLIR",
    "POWERTRAC", "ROCKBLADE", "CROSSLEADER", "DOUBLEKING",
    "NOVAMAXX", "NOVAMAX", "MAXTREK", "HABILEAD", "ROADSHINE",
    "MILEKING", "AMBERSTONE", "TAITONG", "CHENSHANG", "AOQISHI",
    "DURINGON", "EVERLAND", "WIDEWAY", "HEADWAY", "HONOUR",
    "ANNAITE", "ANCHEE", "KOBATA", "ECOSAVER", "ROADCRUZA",
    "HILO", "RAPID", "ALIX", "HAIDA",

    "DURACELL", "EXTREME", "EXTREMA", "MOURA", "GULF", "ARO",
)

KNOWN_PRODUCT_MODELS: tuple[str, ...] = (
    "DESTINATION", "WILDRANGER", "SU-830", "RA1100",
)

BRAND_ALIASES: dict[str, str] = {
    "POWERTAC": "POWERTRAC",
    "DURACEL": "DURACELL",
    "GUL": "GULF",
}

_SIZE_RE = re.compile(
    r"(?<![A-Z0-9])(?:LT|P)?(?:"
    r"\d{3}\s*[/ .-]\s*\d{2}\s*R\s*\d{2}(?:\.5)?C?|"
    r"\d{1,2}(?:\.\d{1,2})?\s*[X]\s*\d{1,2}(?:\.\d{1,2})?\s*R\s*\d{2}(?:\.5)?|"
    r"\d{1,2}(?:\.\d{1,2})?\s*R\s*\d{2}(?:\.5)?C?"
    r")(?![A-Z0-9])",
    re.IGNORECASE,
)
_TYPE_RE = re.compile(
    r"(?<![A-Z0-9])(?:A\s*[/.-]?\s*T|H\s*[/.-]?\s*T|R\s*[/.-]?\s*T|"
    r"M\s*[/.-]?\s*T|ALL[ -]?TERRAIN|MUD[ -]?TERRAIN|HIGHWAY[ -]?TERRAIN)"
    r"(?![A-Z0-9])",
    re.IGNORECASE,
)
_NON_MODEL_RE = re.compile(
    r"\b(?:CAUCHOS?|NEUMATICOS?|LLANTAS?|GOMAS?|RADIAL|RIN|ARO|"
    r"\d{1,2}\s*PR|SET|DIRECCIONAL|TRACCION|MIXTO)\b",
    re.IGNORECASE,
)

@dataclass(frozen=True)
class BrandModelResolution:
    display_name: str
    original_brand: str | None
    original_model: str | None
    normalized_brand: str | None
    normalized_model: str | None
    confidence: float
    status: str
    source: str
    candidates: tuple[str, ...] = ()
    review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidates"] = list(self.candidates)
        return payload

def _ascii(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii")

def _display(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())

def _key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", _ascii(value).upper()).strip()

def _brand_matches(text: str, brands: Iterable[str]) -> list[str]:
    padded = f" {_key(text)} "
    matches: list[str] = []
    for brand in brands:
        key = _key(brand)
        if key and f" {key} " in padded:
            canonical = BRAND_ALIASES.get(key, brand)
            if canonical not in matches:
                matches.append(canonical)
    for alias, canonical in BRAND_ALIASES.items():
        if f" {alias} " in padded and canonical not in matches:
            matches.append(canonical)

    return sorted(matches, key=lambda value: (-len(_key(value).split()), -len(value), value))

def _remove_brand(text: str, brand: str) -> str:
    variants = [brand, *(alias for alias, value in BRAND_ALIASES.items() if value == brand)]
    result = text
    for value in variants:
        pattern = r"(?<![A-Z0-9])" + r"[\s_-]+".join(
            re.escape(token) for token in _key(value).split()
        ) + r"(?![A-Z0-9])"
        result = re.sub(pattern, " ", result, count=1, flags=re.IGNORECASE)
    return result

def _model_candidate(*values: str, brand: str) -> str | None:
    for raw in values:
        candidate = _display(raw)
        if not candidate:
            continue
        candidate = _SIZE_RE.sub(" ", candidate)
        candidate = _remove_brand(candidate, brand)
        candidate = _TYPE_RE.sub(" ", candidate)
        candidate = _NON_MODEL_RE.sub(" ", candidate)

        candidate = re.sub(r"^\s*\d{3,4}\s*AMP\b", " ", candidate, flags=re.I)
        candidate = re.sub(r"^\s*ACEITE\s+\d{1,2}W\d{2}\b", " ", candidate, flags=re.I)
        candidate = re.sub(r"\b(?:MINERAL|SEMI\s+SINTETICO|SINTETICO)\b", " ", candidate, flags=re.I)
        candidate = re.sub(r"\s+", " ", candidate).strip(" -/:,()")
        if candidate and _key(candidate) != _key(brand):
            return candidate.upper()
    return None

def normalize_brand_model(
    display_name: Any,
    *,
    brand: Any = None,
    model: Any = None,
    known_brands: Iterable[str] = KNOWN_BRANDS,
) -> BrandModelResolution:

    name = _display(display_name)
    original_brand = _display(brand) or None
    original_model = _display(model) or None
    search = " ".join(value for value in (original_brand, name) if value)
    matches = _brand_matches(search, known_brands)
    if not matches:
        return BrandModelResolution(
            display_name=name,
            original_brand=original_brand,
            original_model=original_model,
            normalized_brand=None,
            normalized_model=None,
            confidence=0.0,
            status="unresolved",
            source="no_dictionary_match",
            review_required=True,
        )

    distinct = [item for item in matches if _key(item) != _key(matches[0])]
    if distinct and not any(
        _key(item) in _key(matches[0]) or _key(matches[0]) in _key(item)
        for item in distinct
    ):
        return BrandModelResolution(
            display_name=name,
            original_brand=original_brand,
            original_model=original_model,
            normalized_brand=None,
            normalized_model=None,
            confidence=0.35,
            status="ambiguous",
            source="multiple_dictionary_matches",
            candidates=tuple(matches),
            review_required=True,
        )

    normalized_brand = matches[0]
    normalized_model = _model_candidate(
        original_model or "", original_brand or "", name, brand=normalized_brand
    )
    alias_used = _key(original_brand or name).find(_key(normalized_brand)) < 0
    confidence = 0.9 if alias_used else 0.98
    status = "resolved" if normalized_model else "brand_only"
    return BrandModelResolution(
        display_name=name,
        original_brand=original_brand,
        original_model=original_model,
        normalized_brand=normalized_brand,
        normalized_model=normalized_model,
        confidence=confidence,
        status=status,
        source="approved_alias" if alias_used else "brand_dictionary",
        candidates=(normalized_brand,),
        review_required=False,
    )

class BrandModelNormalizer:
    normalize = staticmethod(normalize_brand_model)

__all__ = [
    "BRAND_ALIASES", "KNOWN_BRANDS", "KNOWN_PRODUCT_MODELS", "BrandModelNormalizer",
    "BrandModelResolution", "normalize_brand_model",
]
