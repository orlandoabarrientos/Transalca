"""Registro local, versionado y transaccional de modelos de intenciones.

El registro no entrena ni evalúa modelos. Su única responsabilidad es mantener
la separación física entre candidatos, activo, archivados y rechazados, además
de ofrecer promoción y rollback atómicos. Todos los artefactos permanecen en el
servidor local; nunca se descargan ni se envían a servicios externos.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_MODELS_DIR = PACKAGE_DIR / "models"
DEFAULT_REGISTRY_PATH = DEFAULT_MODELS_DIR / "registry.json"
DEFAULT_LEGACY_ACTIVE = DEFAULT_MODELS_DIR / "intent_model.active.json"
REGISTRY_SCHEMA_VERSION = 1
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as reader:
            shutil.copyfileobj(reader, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


def _safe_version(version: str) -> str:
    value = str(version or "").strip()
    if not _VERSION_RE.fullmatch(value):
        raise ValueError("Versión de modelo inválida")
    return value


def record_from_artifact(
    artifact: dict[str, Any],
    *,
    status: str,
    artifact_path: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construye el registro estable a partir de un artefacto entrenado."""

    version = _safe_version(str(artifact.get("version") or ""))
    metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
    dataset = artifact.get("dataset") if isinstance(artifact.get("dataset"), dict) else {}
    train = metrics.get("train") if isinstance(metrics.get("train"), dict) else {}
    release = artifact.get("release_evidence") if isinstance(artifact.get("release_evidence"), dict) else {}
    record: dict[str, Any] = {
        "version": version,
        "dataset_hash": str(dataset.get("sha256") or ""),
        "train_cases": int(train.get("total") or 0),
        "validation_metrics": metrics.get("validation") or {},
        "test_metrics": metrics.get("test") or {},
        "holdout_metrics": metrics.get("holdout") or {},
        "latency": {
            key: release.get(key)
            for key in ("performance_p95_ms", "catalog_p95_ms", "web_p95_ms")
            if isinstance(release.get(key), (int, float))
        },
        "memory": {
            key: release.get(key)
            for key in ("memory_bytes", "memory_peak_bytes", "model_bytes")
            if isinstance(release.get(key), (int, float))
        },
        "status": status,
        "artifact_path": artifact_path.replace("\\", "/"),
        "created_at": str(artifact.get("created_at") or utc_now()),
        "updated_at": utc_now(),
    }
    if extra:
        record.update(extra)
    return record


class ModelRegistry:
    """Administra artefactos locales sin tocar un activo hasta promoción explícita."""

    STATUSES = frozenset({"active", "candidate", "archived", "rejected"})

    def __init__(
        self,
        models_dir: Path = DEFAULT_MODELS_DIR,
        *,
        registry_path: Path | None = None,
        legacy_active_path: Path | None = None,
    ) -> None:
        self.models_dir = Path(models_dir)
        self.registry_path = Path(registry_path or self.models_dir / "registry.json")
        self.legacy_active_path = Path(legacy_active_path or self.models_dir / "intent_model.active.json")
        self.active_dir = self.models_dir / "active"
        self.candidates_dir = self.models_dir / "candidates"
        self.archived_dir = self.models_dir / "archived"
        self.rejected_dir = self.models_dir / "rejected"
        self.ensure_layout()

    def ensure_layout(self) -> None:
        for directory in (
            self.active_dir,
            self.candidates_dir,
            self.archived_dir,
            self.rejected_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self._write({
                "schema_version": REGISTRY_SCHEMA_VERSION,
                "updated_at": utc_now(),
                "active_version": None,
                "models": {},
                "events": [],
            })

    def _read(self) -> dict[str, Any]:
        with _LOCK:
            try:
                payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError("Registro de modelos inválido") from exc
            if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
                raise RuntimeError("Versión de registro no soportada")
            if not isinstance(payload.get("models"), dict):
                raise RuntimeError("Registro de modelos sin colección válida")
            return payload

    def _write(self, payload: dict[str, Any]) -> None:
        payload["updated_at"] = utc_now()
        _atomic_json(self.registry_path, payload)

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.models_dir.resolve())).replace("\\", "/")
        except ValueError as exc:
            raise ValueError("El artefacto debe quedar dentro del directorio de modelos") from exc

    def _path_for_record(self, record: dict[str, Any]) -> Path:
        relative = Path(str(record.get("artifact_path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Ruta insegura en el registro de modelos")
        result = (self.models_dir / relative).resolve()
        if self.models_dir.resolve() not in result.parents:
            raise RuntimeError("Ruta de artefacto fuera del registro")
        return result

    def bootstrap_legacy_active(self) -> dict[str, Any] | None:
        """Importa una sola vez el alias activo previo, sin cambiar su contenido."""

        with _LOCK:
            registry = self._read()
            if registry.get("active_version") or not self.legacy_active_path.exists():
                active = registry.get("active_version")
                return registry["models"].get(active) if active else None
            artifact = json.loads(self.legacy_active_path.read_text(encoding="utf-8"))
            version = _safe_version(str(artifact.get("version") or ""))
            target = self.active_dir / f"{version}.json"
            _atomic_copy(self.legacy_active_path, target)
            record = record_from_artifact(
                artifact,
                status="active",
                artifact_path=self._relative(target),
                extra={"imported_from_legacy": True},
            )
            registry["models"][version] = record
            registry["active_version"] = version
            registry["events"].append({
                "timestamp": utc_now(), "action": "bootstrap", "version": version,
            })
            self._write(registry)
            return dict(record)

    def register_candidate(
        self,
        artifact_source: Path,
        *,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = Path(artifact_source)
        artifact = json.loads(source.read_text(encoding="utf-8"))
        version = _safe_version(str(artifact.get("version") or ""))
        target = self.candidates_dir / f"{version}.json"
        with _LOCK:
            registry = self._read()
            existing = registry["models"].get(version)
            if existing and existing.get("status") == "active":
                raise RuntimeError("La versión ya es el modelo activo")
            _atomic_copy(source, target)
            record = record_from_artifact(
                artifact,
                status="candidate",
                artifact_path=self._relative(target),
                extra=extra,
            )
            registry["models"][version] = record
            registry["events"].append({
                "timestamp": utc_now(), "action": "register_candidate", "version": version,
            })
            self._write(registry)
        return dict(record)

    def get(self, version: str) -> dict[str, Any]:
        version = _safe_version(version)
        record = self._read()["models"].get(version)
        if not record:
            raise KeyError(f"Versión no registrada: {version}")
        return dict(record)

    def artifact_path(self, version: str) -> Path:
        record = self.get(version)
        path = self._path_for_record(record)
        if not path.is_file():
            raise RuntimeError(f"Artefacto ausente para {version}")
        return path

    def list_models(self, statuses: Iterable[str] | None = None) -> list[dict[str, Any]]:
        registry = self._read()
        allowed = set(statuses or self.STATUSES)
        unknown = allowed - self.STATUSES
        if unknown:
            raise ValueError(f"Estados desconocidos: {sorted(unknown)}")
        records = [dict(item) for item in registry["models"].values() if item.get("status") in allowed]
        return sorted(records, key=lambda item: (str(item.get("created_at")), item["version"]), reverse=True)

    def active(self) -> dict[str, Any] | None:
        registry = self._read()
        version = registry.get("active_version")
        return dict(registry["models"][version]) if version in registry["models"] else None

    def _relocate(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            destination.unlink()
        os.replace(source, destination)

    def promote(self, version: str, *, event_extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Promueve una versión ya validada. Los gates viven en training_pipeline."""

        version = _safe_version(version)
        with _LOCK:
            registry = self._read()
            candidate = registry["models"].get(version)
            if not candidate or candidate.get("status") != "candidate":
                raise RuntimeError("Solo se puede promover un candidato registrado")
            source = self._path_for_record(candidate)
            if not source.is_file():
                raise RuntimeError("Artefacto candidato ausente")

            previous_version = registry.get("active_version")
            if previous_version:
                previous = registry["models"].get(previous_version)
                if not previous or previous.get("status") != "active":
                    raise RuntimeError("Estado activo inconsistente; promoción cancelada")
                previous_source = self._path_for_record(previous)
                archive_target = self.archived_dir / f"{previous_version}.json"
                self._relocate(previous_source, archive_target)
                previous.update({
                    "status": "archived",
                    "artifact_path": self._relative(archive_target),
                    "updated_at": utc_now(),
                })

            active_target = self.active_dir / f"{version}.json"
            self._relocate(source, active_target)
            candidate.update({
                "status": "active",
                "artifact_path": self._relative(active_target),
                "updated_at": utc_now(),
                "promoted_at": utc_now(),
            })
            registry["active_version"] = version
            event = {
                "timestamp": utc_now(),
                "action": "promote",
                "version": version,
                "previous_version": previous_version,
            }
            if event_extra:
                event.update(event_extra)
            registry["events"].append(event)
            self._write(registry)
            _atomic_copy(active_target, self.legacy_active_path)
            return event

    def reject(self, version: str, reasons: Iterable[str]) -> dict[str, Any]:
        version = _safe_version(version)
        reason_list = sorted({str(reason) for reason in reasons if str(reason)})
        if not reason_list:
            raise ValueError("Un rechazo debe registrar al menos una razón")
        with _LOCK:
            registry = self._read()
            record = registry["models"].get(version)
            if not record or record.get("status") != "candidate":
                raise RuntimeError("Solo se puede rechazar un candidato")
            source = self._path_for_record(record)
            target = self.rejected_dir / f"{version}.json"
            self._relocate(source, target)
            record.update({
                "status": "rejected",
                "artifact_path": self._relative(target),
                "rejection_reasons": reason_list,
                "updated_at": utc_now(),
            })
            event = {
                "timestamp": utc_now(), "action": "reject", "version": version,
                "reasons": reason_list,
            }
            registry["events"].append(event)
            self._write(registry)
            return event

    def rollback(self, version: str | None = None) -> dict[str, Any]:
        """Activa inmediatamente una versión archivada, por versión o la más reciente."""

        with _LOCK:
            registry = self._read()
            current_version = registry.get("active_version")
            archived = [
                item for item in registry["models"].values() if item.get("status") == "archived"
            ]
            if version is None:
                if not archived:
                    raise RuntimeError("No existe una versión archivada para rollback")
                target_record = max(archived, key=lambda item: str(item.get("updated_at") or ""))
                version = str(target_record["version"])
            version = _safe_version(version)
            target_record = registry["models"].get(version)
            if not target_record or target_record.get("status") != "archived":
                raise RuntimeError("El rollback requiere una versión archivada")
            target_source = self._path_for_record(target_record)
            if not target_source.is_file():
                raise RuntimeError("Artefacto archivado ausente")

            if current_version:
                current = registry["models"].get(current_version)
                if not current or current.get("status") != "active":
                    raise RuntimeError("Estado activo inconsistente; rollback cancelado")
                current_source = self._path_for_record(current)
                current_archive = self.archived_dir / f"{current_version}.json"
                self._relocate(current_source, current_archive)
                current.update({
                    "status": "archived",
                    "artifact_path": self._relative(current_archive),
                    "updated_at": utc_now(),
                })

            active_target = self.active_dir / f"{version}.json"
            self._relocate(target_source, active_target)
            target_record.update({
                "status": "active",
                "artifact_path": self._relative(active_target),
                "updated_at": utc_now(),
                "rollback_activated_at": utc_now(),
            })
            registry["active_version"] = version
            event = {
                "timestamp": utc_now(), "action": "rollback",
                "from_version": current_version, "to_version": version,
            }
            registry["events"].append(event)
            self._write(registry)
            _atomic_copy(active_target, self.legacy_active_path)
            return event

    def snapshot(self) -> dict[str, Any]:
        return self._read()


__all__ = [
    "DEFAULT_MODELS_DIR", "DEFAULT_REGISTRY_PATH", "ModelRegistry",
    "REGISTRY_SCHEMA_VERSION", "record_from_artifact",
]
