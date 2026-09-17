from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Iterable, Mapping

PASSENGER_TYPES = frozenset({"H/T", "A/T", "R/T", "M/T", "TOURING", "UHP"})
COMMERCIAL_TYPES = frozenset({"COMMERCIAL", "HIGHWAY"})
COMMERCIAL_APPLICATIONS = frozenset({"STEER", "DRIVE", "TRAILER"})
KNOWN_TIRE_TYPES = PASSENGER_TYPES | COMMERCIAL_TYPES

def _ascii(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return normalized.encode("ascii", "ignore").decode("ascii")

def _normal_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _ascii(value).strip().lower())

@dataclass(frozen=True)
class TireTypeProfile:

    code: str
    label: str
    recommended_for: tuple[str, ...]
    limitations: tuple[str, ...]
    relative_road_noise: str | None
    vehicle_scope: str

@dataclass(frozen=True)
class TireTypeResolution:

    primary_type: str | None
    types: tuple[str, ...]
    applications: tuple[str, ...]
    matched_terms: tuple[str, ...]
    confidence: float
    source: str = "approved_local_type_rules"

    @property
    def found(self) -> bool:
        return bool(self.types or self.applications)

    @property
    def is_commercial(self) -> bool:
        return bool(set(self.types) & COMMERCIAL_TYPES or self.applications)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_type": self.primary_type,
            "types": list(self.types),
            "applications": list(self.applications),
            "matched_terms": list(self.matched_terms),
            "confidence": self.confidence,
            "source": self.source,
        }

@dataclass(frozen=True)
class TypeRecommendation:

    tire_type: str
    rank: int
    score: float
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    source: str = "approved_local_usage_rules"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tire_type": self.tire_type,
            "rank": self.rank,
            "score": self.score,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
            "source": self.source,
        }

TYPE_PROFILES: Mapping[str, TireTypeProfile] = {
    "H/T": TireTypeProfile(
        "H/T", "Highway Terrain",
        ("ciudad", "autopista", "carretera", "confort"),
        ("capacidad limitada en barro y trocha fuerte",),
        "habitualmente menor que A/T, R/T o M/T; depende del modelo",
        "liviano",
    ),
    "A/T": TireTypeProfile(
        "A/T", "All Terrain",
        ("carretera y tierra", "grava", "uso mixto diario"),
        ("no equivale a M/T en barro profundo", "puede comprometer ruido frente a H/T"),
        "habitualmente moderado; depende del modelo",
        "liviano",
    ),
    "R/T": TireTypeProfile(
        "R/T", "Rugged Terrain",
        ("off-road mas agresivo con uso diario", "trocha", "piedra y tierra"),
        ("normalmente compromete mas ruido y confort que A/T",),
        "habitualmente mayor que A/T; depende del modelo",
        "liviano",
    ),
    "M/T": TireTypeProfile(
        "M/T", "Mud Terrain",
        ("barro fuerte", "trocha exigente", "off-road prioritario"),
        ("normalmente mas ruido y menor confort en asfalto", "no es primera opcion si prima silencio"),
        "habitualmente alto; depende del modelo",
        "liviano",
    ),
    "TOURING": TireTypeProfile(
        "TOURING", "Touring",
        ("ciudad", "autopista", "confort", "viajes"),
        ("no es una categoria off-road",),
        "habitualmente bajo; depende del modelo",
        "liviano",
    ),
    "UHP": TireTypeProfile(
        "UHP", "Ultra High Performance",
        ("respuesta en asfalto", "conduccion de alto desempeno"),
        ("no implica aptitud off-road", "debe respetar carga y velocidad requeridas"),
        None,
        "liviano",
    ),
    "COMMERCIAL": TireTypeProfile(
        "COMMERCIAL", "Commercial",
        ("carga", "camiones", "autobuses", "flotas"),
        ("requiere validar eje, carga, ruta, medida e indices",),
        None,
        "carga",
    ),
    "HIGHWAY": TireTypeProfile(
        "HIGHWAY", "Highway",
        ("ruta pavimentada de carga", "larga distancia"),
        ("la aplicacion Steer/Drive/Trailer debe confirmarse por separado",),
        None,
        "carga",
    ),
}

_TYPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("M/T", re.compile(r"(?<![a-z0-9])(?:m\s*[/.-]\s*t|mt|mud[ -]?terrain)(?![a-z0-9])", re.I)),
    ("R/T", re.compile(r"(?<![a-z0-9])(?:r\s*[/.-]\s*t|rt|rugged[ -]?terrain)(?![a-z0-9])", re.I)),
    ("A/T", re.compile(r"(?<![a-z0-9])(?:a\s*[/.-]\s*t|at|all[ -]?terrain|todo[ -]?terreno)(?![a-z0-9])", re.I)),
    ("H/T", re.compile(r"(?<![a-z0-9])(?:h\s*[/.-]\s*t|ht|highway[ -]?terrain)(?![a-z0-9])", re.I)),
    ("UHP", re.compile(r"(?<![a-z0-9])(?:uhp|ultra[ -]?high[ -]?performance)(?![a-z0-9])", re.I)),
    ("TOURING", re.compile(r"(?<![a-z0-9])(?:touring|turismo)(?![a-z0-9])", re.I)),
    ("COMMERCIAL", re.compile(r"(?<![a-z0-9])(?:commercial|comercial|caucho(?:s)? de carga)(?![a-z0-9])", re.I)),

    ("HIGHWAY", re.compile(r"(?<![a-z0-9])highway(?!\s*terrain)(?![a-z0-9])", re.I)),
)

_APPLICATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("STEER", re.compile(r"(?<![a-z0-9])(?:steer|steering|direccional|direccion|eje delantero)(?![a-z0-9])", re.I)),
    ("DRIVE", re.compile(r"(?<![a-z0-9])(?:drive|traction|traccion|motriz|eje de traccion)(?![a-z0-9])", re.I)),
    ("TRAILER", re.compile(r"(?<![a-z0-9])(?:trailer|remolque|semi[ -]?remolque)(?![a-z0-9])", re.I)),
)

_USAGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("quiet", re.compile(r"\b(?:silencioso|silenciosa|silencio|poco ruido|bajo ruido|menos ruido|sin ruido|no haga ruido|que no haga ruido|confort)\b")),
    ("city", re.compile(r"\b(?:ciudad|urbano|urbana)\b")),
    ("highway", re.compile(r"\b(?:autopista|carretera|asfalto|highway|viajes?|ruta)\b")),
    ("daily", re.compile(r"\b(?:diario|diaria|todos los dias|uso diario)\b")),
    ("mixed", re.compile(r"\b(?:mixto|mixta|carretera y tierra|asfalto y tierra)\b")),
    ("dirt", re.compile(r"\b(?:tierra|grava|granzon|camino rural)\b")),
    ("mud", re.compile(r"\b(?:barro|pantano|lodo)\b")),
    ("offroad", re.compile(r"\b(?:off[ -]?road|rustiquear|rustiqueo|trocha|montana|monte|4x4)\b")),
    ("aggressive", re.compile(r"\b(?:trocha fuerte|off[ -]?road agresivo|rustiqueo fuerte|extremo|piedra)\b")),
    ("performance", re.compile(r"\b(?:performance|alto desempeno|deportivo|pista)\b")),
    ("load", re.compile(r"\b(?:carga|camion|gandola|autobus|flota|comercial)\b")),
    ("steer", _APPLICATION_PATTERNS[0][1]),
    ("drive", _APPLICATION_PATTERNS[1][1]),
    ("trailer", _APPLICATION_PATTERNS[2][1]),
)

class TireTypeResolver:

    def resolve(self, value: Any) -> TireTypeResolution:
        text = _normal_text(value)
        matched: list[tuple[int, str, str]] = []
        applications: list[tuple[int, str, str]] = []
        for code, pattern in _TYPE_PATTERNS:
            for hit in pattern.finditer(text):
                matched.append((hit.start(), code, hit.group(0)))
        for code, pattern in _APPLICATION_PATTERNS:
            for hit in pattern.finditer(text):
                applications.append((hit.start(), code, hit.group(0)))

        matched.sort(key=lambda row: row[0])
        applications.sort(key=lambda row: row[0])
        types = tuple(dict.fromkeys(code for _, code, _ in matched))
        app_codes = tuple(dict.fromkeys(code for _, code, _ in applications))

        if app_codes and not types:
            types = ("COMMERCIAL",)
        terms = tuple(dict.fromkeys(term for _, _, term in (*matched, *applications)))
        confidence = 0.99 if matched else 0.96 if applications else 0.0
        return TireTypeResolution(
            primary_type=types[0] if types else None,
            types=types,
            applications=app_codes,
            matched_terms=terms,
            confidence=confidence,
        )

    def normalize_usage(self, usage: str | Iterable[str] | None) -> frozenset[str]:
        if usage is None:
            return frozenset()
        values = (usage,) if isinstance(usage, str) else tuple(str(item) for item in usage)
        found: set[str] = set()
        for value in values:
            normalized = _normal_text(value)

            canonical = normalized.replace("-", "")
            direct = {
                "quiet": "quiet", "city": "city", "highway": "highway",
                "daily": "daily", "mixed": "mixed", "dirt": "dirt",
                "mud": "mud", "offroad": "offroad", "performance": "performance",
                "aggressive": "aggressive",
                "load": "load", "steer": "steer", "drive": "drive",
                "trailer": "trailer",
            }.get(canonical)
            if direct:
                found.add(direct)
            for key, pattern in _USAGE_PATTERNS:
                if pattern.search(normalized):
                    found.add(key)
        return frozenset(found)

    def profile(self, tire_type: str | None) -> TireTypeProfile | None:
        if not tire_type:
            return None
        resolution = self.resolve(tire_type)
        code = resolution.primary_type or str(tire_type).upper()
        return TYPE_PROFILES.get(code)

    def recommend(
        self,
        usage: str | Iterable[str] | None,
        *,
        prioritize_quiet: bool = False,
        heavy_vehicle: bool = False,
    ) -> tuple[TypeRecommendation, ...]:

        uses = set(self.normalize_usage(usage))
        prioritize_quiet = prioritize_quiet or "quiet" in uses
        heavy_vehicle = heavy_vehicle or "load" in uses or bool(uses & {"steer", "drive", "trailer"})

        ranked: list[tuple[str, float, tuple[str, ...]]] = []
        if heavy_vehicle:
            applications = [code.upper() for code in ("steer", "drive", "trailer") if code in uses]
            if applications:
                for index, application in enumerate(applications):
                    ranked.append((application, 100.0 - index, (f"aplicacion declarada: {application.lower()}",)))
            else:
                ranked.append(("COMMERCIAL", 80.0, ("vehiculo o uso de carga",)))
            if "highway" in uses:
                ranked.append(("HIGHWAY", 75.0, ("ruta principalmente pavimentada",)))
            return self._recommendation_rows(ranked)

        if "performance" in uses and not uses & {"dirt", "offroad", "mud"}:
            ranked.append(("UHP", 95.0, ("prioridad de respuesta en asfalto",)))

        if "mud" in uses:
            if prioritize_quiet:
                ranked.extend((
                    ("A/T", 88.0, ("uso diario con prioridad de silencio", "capacidad limitada en barro fuerte")),
                    ("R/T", 82.0, ("mayor agarre fuera de carretera", "compromete mas ruido que A/T")),
                    ("M/T", 70.0, ("mejor orientado a barro fuerte", "no es primera opcion por la prioridad de silencio")),
                ))
            else:
                ranked.extend((
                    ("M/T", 98.0, ("barro o lodo fuerte",)),
                    ("R/T", 82.0, ("alternativa para off-road agresivo y uso diario",)),
                    ("A/T", 60.0, ("alternativa mixta para barro ligero",)),
                ))
        elif "offroad" in uses and "daily" in uses:
            ranked.extend((
                ("R/T", 96.0, ("off-road agresivo con uso diario",)),
                ("A/T", 84.0, ("opcion mixta con menor compromiso vial",)),
                ("M/T", 70.0, ("solo si el barro fuerte es prioritario",)),
            ))
        elif "aggressive" in uses:
            if prioritize_quiet:
                ranked.extend((
                    ("A/T", 86.0, ("prioridad de silencio con uso fuera de carretera moderado",)),
                    ("R/T", 82.0, ("mayor capacidad de trocha con compromiso de ruido",)),
                    ("M/T", 70.0, ("trocha fuerte, pero no primero por la prioridad de silencio",)),
                ))
            else:
                ranked.extend((
                    ("M/T", 96.0, ("trocha fuerte u off-road extremo",)),
                    ("R/T", 84.0, ("alternativa agresiva con mejor compromiso vial",)),
                    ("A/T", 60.0, ("alternativa solo si la exigencia fuera de carretera es moderada",)),
                ))
        elif uses & {"offroad", "dirt", "mixed"}:
            ranked.extend((
                ("A/T", 94.0, ("uso combinado de carretera y tierra",)),
                ("R/T", 80.0, ("alternativa si la trocha es mas exigente",)),
            ))
        elif uses & {"city", "highway", "quiet"}:
            ranked.extend((
                ("H/T", 94.0, ("ciudad o autopista", "prioridad de confort")),
                ("TOURING", 92.0, ("carretera y confort",)),
            ))
        elif not ranked:
            return ()

        dedup: dict[str, tuple[str, float, tuple[str, ...]]] = {}
        for row in ranked:
            if row[0] not in dedup or row[1] > dedup[row[0]][1]:
                dedup[row[0]] = row
        return self._recommendation_rows(sorted(dedup.values(), key=lambda row: -row[1]))

    @staticmethod
    def _recommendation_rows(
        ranked: Iterable[tuple[str, float, tuple[str, ...]]],
    ) -> tuple[TypeRecommendation, ...]:
        output: list[TypeRecommendation] = []
        for index, (code, score, reasons) in enumerate(ranked, start=1):
            profile = TYPE_PROFILES.get(code)
            limitations = profile.limitations if profile else (
                "validar eje, carga, medida e indice con la ficha del fabricante",
            )
            output.append(TypeRecommendation(code, index, score, reasons, limitations))
        return tuple(output)

    def usage_score(self, tire_type: str | None, usage: str | Iterable[str] | None) -> float | None:

        resolution = self.resolve(tire_type)
        code = resolution.primary_type
        if not code:
            return None
        recommendations = self.recommend(
            usage,
            heavy_vehicle=code in COMMERCIAL_TYPES or bool(resolution.applications),
        )
        for recommendation in recommendations:
            if recommendation.tire_type == code:
                return recommendation.score
            if code == "COMMERCIAL" and recommendation.tire_type in COMMERCIAL_APPLICATIONS:
                return recommendation.score - 5.0
        return 10.0 if recommendations else 50.0

_DEFAULT_RESOLVER = TireTypeResolver()

def resolve_tire_type(value: Any) -> TireTypeResolution:
    return _DEFAULT_RESOLVER.resolve(value)

def recommend_tire_types(
    usage: str | Iterable[str] | None,
    *,
    prioritize_quiet: bool = False,
    heavy_vehicle: bool = False,
) -> tuple[TypeRecommendation, ...]:
    return _DEFAULT_RESOLVER.recommend(
        usage,
        prioritize_quiet=prioritize_quiet,
        heavy_vehicle=heavy_vehicle,
    )

__all__ = [
    "COMMERCIAL_APPLICATIONS", "COMMERCIAL_TYPES", "KNOWN_TIRE_TYPES",
    "PASSENGER_TYPES", "TYPE_PROFILES", "TireTypeProfile",
    "TireTypeRecommendation", "TireTypeResolution", "TireTypeResolver",
    "TypeRecommendation", "recommend_tire_types", "resolve_tire_type",
]

TireTypeRecommendation = TypeRecommendation
