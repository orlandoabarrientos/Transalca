"""Registro local y revisable de vocabulario emergente.

Detectar no equivale a incorporar. Toda propuesta nace ``pending_review`` y solo
una accion administrativa explicita puede marcarla como aprobada o rechazada.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from typing import Any, Iterable, Mapping

from .feedback_anonymizer import FeedbackAnonymizer


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PATH = BASE_DIR / "data" / "vocabulary.json"
TOKEN_RE = re.compile(r"[a-záéíóúñ][a-záéíóúñ0-9.-]{2,}", re.I)
VALID_CATEGORIES = {"make", "model", "vehicle_alias", "service", "product", "typo", "regional", "expression"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


class VocabularyManager:
    def __init__(self, path: Path | str = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.anonymizer = FeedbackAnonymizer()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "updated_at": None, "terms": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": 1, "updated_at": None, "terms": []}
        if not isinstance(value, dict) or not isinstance(value.get("terms", []), list):
            return {"schema_version": 1, "updated_at": None, "terms": []}
        value.setdefault("schema_version", 1)
        value.setdefault("terms", [])
        return value

    def save(self, value: Mapping[str, Any]) -> None:
        payload = dict(value)
        payload["schema_version"] = 1
        payload["updated_at"] = _now()
        payload["terms"] = sorted(payload.get("terms") or [], key=lambda item: (_normalize(item.get("term")), item.get("status", "")))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def detect(
        self,
        messages: Iterable[str],
        known_terms: Iterable[str],
        minimum_frequency: int = 2,
    ) -> list[dict[str, Any]]:
        """Return deterministic proposals without modifying the registry."""

        known = sorted({_normalize(term) for term in known_terms if _normalize(term)})
        known_tokens = {token for term in known for token in TOKEN_RE.findall(term)}
        counts: Counter[str] = Counter()
        examples: defaultdict[str, list[str]] = defaultdict(list)
        for raw_message in messages:
            result = self.anonymizer.anonymize(raw_message)
            if not result.safe or self.anonymizer.has_private_placeholder(result.text):
                continue
            for token in {_normalize(match) for match in TOKEN_RE.findall(result.text)}:
                if token in known_tokens or token.startswith("["):
                    continue
                counts[token] += 1
                if len(examples[token]) < 3:
                    examples[token].append(result.text[:240])
        proposals: list[dict[str, Any]] = []
        for term, frequency in counts.most_common():
            if frequency < max(1, int(minimum_frequency)):
                continue
            matches = get_close_matches(term, known_tokens, n=1, cutoff=0.68)
            suggestion = matches[0] if matches else None
            similarity = SequenceMatcher(None, term, suggestion or "").ratio() if suggestion else 0.0
            confidence = round(min(0.99, similarity * 0.85 + min(frequency, 20) / 20 * 0.14), 4)
            proposals.append({
                "term": term,
                "suggested": suggestion,
                "frequency": frequency,
                "confidence": confidence,
                "category": "typo" if suggestion else "expression",
                "examples": examples[term],
                "status": "pending_review",
                "auto_applied": False,
            })
        return proposals[:250]

    def merge_proposals(self, proposals: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        registry = self.load()
        by_term = {_normalize(row.get("term")): dict(row) for row in registry.get("terms", []) if _normalize(row.get("term"))}
        inserted = updated = rejected_private = 0
        for proposal in proposals:
            term_result = self.anonymizer.anonymize(proposal.get("term"), 100)
            suggested_result = self.anonymizer.anonymize(proposal.get("suggested"), 100)
            if not term_result.safe or not suggested_result.safe or self.anonymizer.has_private_placeholder(term_result.text):
                rejected_private += 1
                continue
            term = _normalize(term_result.text)
            if not term:
                continue
            prior = by_term.get(term)
            if prior and prior.get("status") in {"approved", "rejected"}:
                continue
            clean = {
                "term": term,
                "suggested": _normalize(suggested_result.text) or None,
                "frequency": max(int(proposal.get("frequency") or 1), int((prior or {}).get("frequency") or 0)),
                "confidence": round(max(0.0, min(1.0, float(proposal.get("confidence") or 0.0))), 4),
                "category": proposal.get("category") if proposal.get("category") in VALID_CATEGORIES else "expression",
                "examples": list(proposal.get("examples") or [])[:3],
                "status": "pending_review",
                "auto_applied": False,
                "proposed_at": (prior or {}).get("proposed_at") or _now(),
            }
            if prior:
                updated += 1
            else:
                inserted += 1
            by_term[term] = clean
        registry["terms"] = list(by_term.values())
        self.save(registry)
        return {"inserted": inserted, "updated": updated, "rejected_private": rejected_private, "auto_applied": 0}

    def approve(self, term: str, *, suggested: str, category: str, reviewer: str) -> bool:
        """Approval changes only this registry; aliases/knowledge require another review."""

        if category not in VALID_CATEGORIES or not reviewer.strip() or not suggested.strip():
            return False
        registry = self.load()
        target = _normalize(term)
        for row in registry.get("terms", []):
            if _normalize(row.get("term")) != target:
                continue
            row.update({
                "suggested": _normalize(suggested), "category": category, "status": "approved",
                "reviewed_at": _now(), "reviewer": reviewer.strip()[:80], "auto_applied": False,
            })
            self.save(registry)
            return True
        return False

    def reject(self, term: str, *, reason: str, reviewer: str) -> bool:
        if not reviewer.strip():
            return False
        registry = self.load()
        target = _normalize(term)
        for row in registry.get("terms", []):
            if _normalize(row.get("term")) != target:
                continue
            clean_reason = self.anonymizer.anonymize(reason, 240)
            if not clean_reason.safe or self.anonymizer.has_private_placeholder(clean_reason.text):
                return False
            row.update({
                "status": "rejected", "rejection_reason": clean_reason.text,
                "reviewed_at": _now(), "reviewer": reviewer.strip()[:80], "auto_applied": False,
            })
            self.save(registry)
            return True
        return False

    def approved_aliases(self) -> dict[str, str]:
        return {
            _normalize(row.get("term")): _normalize(row.get("suggested"))
            for row in self.load().get("terms", [])
            if row.get("status") == "approved" and row.get("suggested")
        }


__all__ = ["VocabularyManager", "VALID_CATEGORIES"]
