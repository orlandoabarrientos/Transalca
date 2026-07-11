"""Staging revisable para cambios de conocimiento local.

La web y el feedback solo pueden crear candidatos. Aplicar un alias requiere una
segunda accion humana explicita; fitment, FAQ, servicios y politicas nunca se
escriben automaticamente desde este modulo.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
from uuid import uuid4

from .feedback_anonymizer import FeedbackAnonymizer


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUEUE = BASE_DIR / "data" / "knowledge_review_queue.jsonl"
DEFAULT_ALIASES = BASE_DIR / "data" / "vehicle_aliases.json"
ALLOWED_KINDS = {"vehicle_alias", "fitment", "business_faq", "service_knowledge", "intent_example"}
ALLOWED_SOURCES = {"approved_feedback", "manual", "web_reviewed"}
DYNAMIC_KEYS = {
    "price", "precio", "stock", "inventory", "inventario", "promotion", "promocion",
    "promoción", "order_status", "estado_pedido", "branch_stock", "temporary_offer",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _write(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def _contains_dynamic(value: Any, parent: str = "") -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in DYNAMIC_KEYS or _contains_dynamic(nested, normalized):
                return True
    elif isinstance(value, list):
        return any(_contains_dynamic(item, parent) for item in value)
    return parent in DYNAMIC_KEYS


class KnowledgeUpdater:
    def __init__(self, queue_path: Path | str = DEFAULT_QUEUE) -> None:
        self.queue_path = Path(queue_path)
        self.anonymizer = FeedbackAnonymizer()

    def stage(
        self,
        *,
        kind: str,
        payload: Mapping[str, Any],
        source_type: str,
        source_case_ids: Iterable[str] = (),
        sources: Iterable[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        if kind not in ALLOWED_KINDS:
            return {"status": "error", "error": "tipo_no_permitido"}
        if source_type not in ALLOWED_SOURCES:
            return {"status": "error", "error": "fuente_no_permitida"}
        if _contains_dynamic(payload):
            return {"status": "error", "error": "dato_dinamico_no_entrenable"}
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        sanitized = self.anonymizer.anonymize(serialized, 5000)
        if not sanitized.safe or self.anonymizer.has_private_placeholder(sanitized.text):
            return {"status": "error", "error": "contenido_privado_o_incierto"}
        clean_payload = json.loads(sanitized.text)
        clean_sources = self._validate_sources(kind, source_type, list(sources))
        if isinstance(clean_sources, dict):
            return clean_sources
        candidate = {
            "candidate_id": f"KN-{uuid4().hex[:16].upper()}",
            "created_at": _now(),
            "kind": kind,
            "payload": clean_payload,
            "source_type": source_type,
            "source_case_ids": [str(case)[:80] for case in source_case_ids][:25],
            "sources": clean_sources,
            "status": "pending_review",
            "requires_human_approval": True,
            "auto_applied": False,
        }
        rows = _read(self.queue_path)
        rows.append(candidate)
        _write(self.queue_path, rows)
        return {"status": "pending_review", "candidate_id": candidate["candidate_id"], "auto_applied": False}

    def approve(self, candidate_id: str, *, reviewer: str, review_notes: str) -> dict[str, Any]:
        if not reviewer.strip() or not review_notes.strip():
            return {"status": "error", "error": "revision_humana_incompleta"}
        notes = self.anonymizer.anonymize(review_notes, 800)
        if not notes.safe or self.anonymizer.has_private_placeholder(notes.text):
            return {"status": "error", "error": "notas_privadas_o_inciertas"}
        rows = _read(self.queue_path)
        for row in rows:
            if row.get("candidate_id") != candidate_id:
                continue
            row.update({
                "status": "approved", "approved_at": _now(), "reviewer": reviewer.strip()[:80],
                "review_notes": notes.text, "auto_applied": False,
            })
            _write(self.queue_path, rows)
            return {"status": "approved", "candidate_id": candidate_id, "applied": False}
        return {"status": "error", "error": "candidato_no_encontrado"}

    def reject(self, candidate_id: str, *, reviewer: str, reason: str) -> dict[str, Any]:
        if not reviewer.strip() or not reason.strip():
            return {"status": "error", "error": "revision_humana_incompleta"}
        clean = self.anonymizer.anonymize(reason, 500)
        if not clean.safe or self.anonymizer.has_private_placeholder(clean.text):
            return {"status": "error", "error": "razon_privada_o_incierta"}
        rows = _read(self.queue_path)
        for row in rows:
            if row.get("candidate_id") != candidate_id:
                continue
            row.update({
                "status": "rejected", "rejected_at": _now(), "reviewer": reviewer.strip()[:80],
                "rejection_reason": clean.text, "auto_applied": False,
            })
            _write(self.queue_path, rows)
            return {"status": "rejected", "candidate_id": candidate_id, "applied": False}
        return {"status": "error", "error": "candidato_no_encontrado"}

    def apply_vehicle_alias(
        self,
        candidate_id: str,
        *,
        reviewer: str,
        aliases_path: Path | str = DEFAULT_ALIASES,
    ) -> dict[str, Any]:
        """Apply one already-approved alias; no other knowledge type is mutable here."""

        rows = _read(self.queue_path)
        candidate = next((row for row in rows if row.get("candidate_id") == candidate_id), None)
        if not candidate:
            return {"status": "error", "error": "candidato_no_encontrado"}
        if candidate.get("status") != "approved" or candidate.get("kind") != "vehicle_alias" or not reviewer.strip():
            return {"status": "error", "error": "candidato_no_aprobado_para_alias"}
        payload = candidate.get("payload") or {}
        model = str(payload.get("model") or "").strip().lower()
        alias = str(payload.get("alias") or "").strip().lower()
        if not model or not alias:
            return {"status": "error", "error": "alias_incompleto"}
        path = Path(aliases_path)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"status": "error", "error": "archivo_alias_invalido"}
        models = document.get("models") if isinstance(document, dict) else None
        if not isinstance(models, dict) or model not in models or not isinstance(models[model], dict):
            return {"status": "error", "error": "modelo_canonico_desconocido"}
        aliases = models[model].setdefault("aliases", [])
        if alias not in aliases:
            aliases.append(alias)
            aliases.sort()
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        candidate.update({
            "status": "promoted", "applied_at": _now(), "applied_by": reviewer.strip()[:80],
            "auto_applied": False,
        })
        _write(self.queue_path, rows)
        return {"status": "promoted", "candidate_id": candidate_id, "model": model, "alias": alias}

    @staticmethod
    def _validate_sources(kind: str, source_type: str, sources: list[Mapping[str, Any]]) -> list[dict[str, str]] | dict[str, Any]:
        cleaned: list[dict[str, str]] = []
        domains: set[str] = set()
        for source in sources[:10]:
            url = str(source.get("url") or "").strip()
            domain = (urlparse(url).hostname or "").lower()
            quality = str(source.get("quality") or "unknown").lower()
            if not url.startswith(("http://", "https://")) or not domain:
                continue
            domains.add(domain.removeprefix("www."))
            cleaned.append({"url": url[:500], "domain": domain, "quality": quality[:40]})
        if source_type == "web_reviewed" and kind == "fitment":
            trusted = [row for row in cleaned if row["quality"] in {"official", "manufacturer", "manual", "technical"}]
            if len({row["domain"].removeprefix("www.") for row in trusted}) < 2:
                return {"status": "error", "error": "fitment_web_requiere_dos_fuentes_independientes"}
        return cleaned


__all__ = ["KnowledgeUpdater"]
