"""Pipeline local y revisable para aprendizaje continuo.

Los comandos de este modulo administran candidatos; nunca entrenan dentro de una
peticion, alteran el modelo activo ni aplican fitment, precios o politicas. La unica
ruta soportada hacia el dataset es una aprobacion humana completa seguida de
``build-dataset`` y del pipeline offline de entrenamiento/evaluacion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from componente_ia.feedback_anonymizer import FeedbackAnonymizer, anonymize_text, placeholders_in
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from componente_ia.feedback_anonymizer import FeedbackAnonymizer, anonymize_text, placeholders_in


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_FEEDBACK = DATA_DIR / "production_feedback.jsonl"
LEGACY_FEEDBACK = DATA_DIR / "feedback_queue.jsonl"
DEFAULT_REVIEW = DATA_DIR / "learning_review_queue.jsonl"
DEFAULT_APPROVED = DATA_DIR / "approved_feedback_cases.jsonl"
DEFAULT_REJECTED = DATA_DIR / "rejected_feedback_cases.jsonl"
TOKEN_RE = re.compile(r"[a-záéíóúñ0-9][a-záéíóúñ0-9/.-]*", re.I)
CRITICAL_TOPICS = {
    "fitment", "compatibilidad", "medida oem", "precio", "garantia", "garantía",
    "politica", "política", "seguridad", "credito", "crédito", "pago", "stock",
}
STOPWORDS = {
    "a", "al", "algo", "con", "cual", "de", "del", "dime", "el", "en", "es",
    "esa", "ese", "la", "las", "lo", "los", "me", "mi", "para", "por", "que",
    "se", "si", "su", "tengo", "tienen", "un", "una", "y",
}
REVIEW_STATES = {"pending_review", "approved", "rejected", "needs_edit", "promoted"}
ANNOTATION_FIELDS = {
    "intent", "secondary_intents", "entities", "expected_behavior", "must_include",
    "must_not_include", "category", "critical", "generate_variations",
}
EDITABLE_FIELDS = ANNOTATION_FIELDS | {"message_anonymized", "history_anonymized", "answer", "review_notes"}
_ANONYMIZER = FeedbackAnonymizer()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                value["_source_line"] = number
                rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            clean = {key: value for key, value in row.items() if not key.startswith("_source_")}
            stream.write(json.dumps(clean, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    temporary.replace(path)
    return count


def append_unique(path: Path, row: dict[str, Any], identity: str = "review_id") -> None:
    rows = read_jsonl(path)
    target = str(row.get(identity) or "")
    rows = [item for item in rows if str(item.get(identity) or "") != target]
    rows.append(row)
    write_jsonl(path, rows)


def _intent(row: Mapping[str, Any]) -> str:
    return str(row.get("intent_predicted") or row.get("intent") or "unknown")[:80]


def _entities(row: Mapping[str, Any]) -> dict[str, Any]:
    value = row.get("entities_predicted", row.get("entities"))
    return dict(value) if isinstance(value, Mapping) else {}


def _confidence(row: Mapping[str, Any]) -> float:
    try:
        return max(0.0, min(1.0, float(row.get("intent_confidence", row.get("confidence", 0.0)))))
    except (TypeError, ValueError):
        return 0.0


def _reasons(row: Mapping[str, Any]) -> list[str]:
    values = row.get("candidate_reason", row.get("signals", []))
    return sorted({str(value)[:80] for value in values}) if isinstance(values, list) else []


def normalize_signature(message: str) -> str:
    tokens = [token.lower().strip(".,;:!?¡¿") for token in TOKEN_RE.findall(message or "")]
    return " ".join("<num>" if token.isdigit() and len(token) >= 4 else token for token in tokens)


def token_set(message: str) -> set[str]:
    return {token for token in normalize_signature(message).split() if token not in STOPWORDS}


def similarity(left: str, right: str) -> float:
    a, b = token_set(left), token_set(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def valid_feedback(row: dict[str, Any]) -> tuple[bool, str]:
    message = str(row.get("message_anonymized") or "").strip()
    if not message:
        return False, "mensaje_vacio"
    if len(message) > 1600:
        return False, "mensaje_excede_limite"
    history = row.get("history_anonymized") or []
    if not isinstance(history, list):
        return False, "historial_invalido"
    protected_values = [message, str(row.get("answer") or ""), *history]
    if placeholders_in(protected_values):
        return False, "contiene_marcador_privado"
    for value in protected_values:
        if not _ANONYMIZER.anonymize(value, 1800).safe:
            return False, "anonimizacion_no_segura"
    if str(row.get("operator_rating") or "").lower() == "good" and not row.get("candidate_for_training"):
        return False, "sin_senal_de_mejora"
    status = str(row.get("status") or "pending_review")
    if status not in REVIEW_STATES | {"pending"}:
        return False, "estado_invalido"
    return True, "ok"


def deduplicate(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    duplicates = 0
    for row in rows:
        key = (normalize_signature(str(row.get("message_anonymized") or "")), _intent(row))
        if not key[0]:
            continue
        prior = selected.get(key)
        if prior is None:
            selected[key] = row
            continue
        duplicates += 1
        prior_score = (bool(prior.get("operator_rating")), len(_reasons(prior)), -_confidence(prior))
        new_score = (bool(row.get("operator_rating")), len(_reasons(row)), -_confidence(row))
        if new_score > prior_score:
            selected[key] = row
    return list(selected.values()), duplicates


def cluster_cases(rows: list[dict[str, Any]], threshold: float = 0.62) -> list[list[dict[str, Any]]]:
    clusters: list[list[dict[str, Any]]] = []
    representatives: list[str] = []
    for row in sorted(rows, key=lambda item: (_intent(item), str(item.get("message_anonymized")))):
        message = str(row.get("message_anonymized") or "")
        best_idx, best_score = -1, 0.0
        for idx, representative in enumerate(representatives):
            if _intent(clusters[idx][0]) != _intent(row):
                continue
            score = similarity(message, representative)
            if score > best_score:
                best_idx, best_score = idx, score
        if best_idx >= 0 and best_score >= threshold:
            clusters[best_idx].append(row)
        else:
            representatives.append(message)
            clusters.append([row])
    return clusters


def known_vocabulary() -> set[str]:
    vocabulary: set[str] = set(STOPWORDS)
    for path in (DATA_DIR / "intent_examples.jsonl", DATA_DIR / "vehicle_aliases.json", DATA_DIR / "vocabulary.json"):
        if path.exists():
            vocabulary.update(token.lower() for token in TOKEN_RE.findall(path.read_text(encoding="utf-8", errors="ignore")))
    return vocabulary


def detect_new_vocabulary(rows: Iterable[dict[str, Any]], minimum: int = 2) -> list[dict[str, Any]]:
    known = known_vocabulary()
    counts: Counter[str] = Counter()
    examples: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        message = str(row.get("message_anonymized") or "")
        for token in token_set(message):
            if token in known or len(token) < 3 or token.startswith("["):
                continue
            counts[token] += 1
            if len(examples[token]) < 3:
                examples[token].append(message[:240])
    return [
        {"term": term, "frequency": count, "count": count, "examples": examples[term], "status": "pending_review"}
        for term, count in counts.most_common() if count >= minimum
    ][:100]


def is_critical(row: dict[str, Any]) -> bool:
    text = " ".join((str(row.get("message_anonymized") or ""), str(row.get("answer") or ""), _intent(row))).lower()
    return any(topic in text for topic in CRITICAL_TOPICS)


def proposed_kind(row: dict[str, Any], novel_terms: set[str]) -> str:
    if token_set(str(row.get("message_anonymized") or "")) & novel_terms:
        return "vehicle_alias_or_intent_example" if _intent(row) in {
            "tire_size_lookup", "tire_recommendation", "truck_tire_advice"
        } else "vocabulary_or_intent_example"
    return "intent_example_or_faq" if row.get("fallback") or _confidence(row) < 0.45 else "training_case"


@dataclass(slots=True)
class LearningSummary:
    input_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    duplicates: int = 0
    clusters: int = 0
    review_candidates: int = 0
    novel_terms: int = 0

    def as_dict(self) -> dict[str, int]:
        return {field: int(getattr(self, field)) for field in self.__dataclass_fields__}


def collect(path: Path = DEFAULT_FEEDBACK) -> dict[str, Any]:
    if path == DEFAULT_FEEDBACK and not path.exists() and LEGACY_FEEDBACK.exists():
        path = LEGACY_FEEDBACK
    rows = read_jsonl(path)
    reasons: Counter[str] = Counter()
    candidates = 0
    for row in rows:
        valid, reason = valid_feedback(row)
        reasons[reason] += 1
        if valid and row.get("candidate_for_training", True):
            candidates += 1
    return {
        "status": "ok", "source": str(path), "records": len(rows),
        "candidate_records": candidates, "validation": dict(reasons),
        "note": "No se entrenó ni promovió ningún cambio.",
    }


def _stable_review_id(cluster: list[dict[str, Any]]) -> str:
    keys = sorted(str(row.get("case_id") or normalize_signature(str(row.get("message_anonymized")))) for row in cluster)
    digest = hashlib.sha256("|".join(keys).encode("utf-8")).hexdigest()[:16].upper()
    return f"REVIEW-{digest}"


def review(input_path: Path = DEFAULT_FEEDBACK, output_path: Path = DEFAULT_REVIEW) -> dict[str, Any]:
    source_rows = read_jsonl(input_path)
    summary = LearningSummary(input_rows=len(source_rows))
    rejected: Counter[str] = Counter()
    valid_rows: list[dict[str, Any]] = []
    for row in source_rows:
        valid, reason = valid_feedback(row)
        if valid and row.get("candidate_for_training", True):
            valid_rows.append(row)
        else:
            rejected[reason] += 1
    summary.valid_rows = len(valid_rows)
    summary.rejected_rows = len(source_rows) - len(valid_rows)
    unique, summary.duplicates = deduplicate(valid_rows)
    clusters = cluster_cases(unique)
    summary.clusters = len(clusters)
    vocabulary = detect_new_vocabulary(unique)
    summary.novel_terms = len(vocabulary)
    novel_terms = {entry["term"] for entry in vocabulary}
    previous = {str(row.get("review_id")): row for row in read_jsonl(output_path)}
    candidates: list[dict[str, Any]] = []
    for cluster in clusters:
        representative = min(cluster, key=lambda item: (_confidence(item), str(item.get("case_id"))))
        review_id = _stable_review_id(cluster)
        retained = previous.get(review_id, {})
        candidate = {
            "review_id": review_id,
            "created_at": retained.get("created_at") or now_iso(),

            "status": retained.get("status") or "pending",
            "workflow_status": retained.get("workflow_status") or "pending_review",
            "requires_human_approval": True,
            "critical": bool(retained.get("critical", any(is_critical(row) for row in cluster))),
            "critical_change_auto_allowed": False,
            "proposal_type": proposed_kind(representative, novel_terms),
            "intent": retained.get("intent") or _intent(representative),
            "secondary_intents": retained.get("secondary_intents") or [],
            "message_anonymized": anonymize_text(representative.get("message_anonymized")),
            "history_anonymized": representative.get("history_anonymized") or [],
            "answer": anonymize_text(representative.get("answer"), 1800),
            "entities": retained.get("entities") or _entities(representative),
            "signals": sorted({signal for row in cluster for signal in _reasons(row)}),
            "cluster_size": len(cluster),
            "source_case_ids": [str(row.get("case_id")) for row in cluster[:25]],
            "expected_behavior": retained.get("expected_behavior") or "",
            "must_include": retained.get("must_include") or [],
            "must_not_include": retained.get("must_not_include") or [],
            "category": retained.get("category") or "",
            "generate_variations": retained.get("generate_variations"),
            "review_notes": retained.get("review_notes") or "",
            "suggested_action": "corregir la anotación y aprobar explícitamente; nunca aplicar directamente",
        }
        candidates.append(candidate)
    summary.review_candidates = write_jsonl(output_path, candidates)
    vocabulary_path = output_path.with_name("learning_vocabulary_proposals.json")
    vocabulary_path.write_text(json.dumps(vocabulary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "ok", **summary.as_dict(), "rejected_reasons": dict(rejected),
        "review_queue": str(output_path), "vocabulary_proposals": str(vocabulary_path),
        "auto_applied": 0,
    }


def _canonical_status(status: str) -> str:
    return "pending_review" if status == "pending" else status


def update_review_status(path: Path, review_ids: set[str], status: str) -> int:
    canonical = _canonical_status(status)
    if canonical not in REVIEW_STATES:
        raise ValueError("Estado de revisión inválido")
    rows = read_jsonl(path)
    changed = 0
    for row in rows:
        if str(row.get("review_id")) in review_ids:
            row["status"] = "pending" if canonical == "pending_review" else canonical
            row["workflow_status"] = canonical
            row["reviewed_at"] = now_iso()
            changed += 1
    write_jsonl(path, rows)
    return changed


def list_pending_cases(path: Path = DEFAULT_REVIEW, limit: int = 100) -> list[dict[str, Any]]:
    rows = read_jsonl(path)
    pending = [row for row in rows if _canonical_status(str(row.get("workflow_status") or row.get("status") or "pending")) in {"pending_review", "needs_edit"}]
    return [
        {
            "review_id": row.get("review_id"), "status": row.get("workflow_status") or row.get("status"),
            "message_anonymized": row.get("message_anonymized"), "intent": row.get("intent"),
            "critical": bool(row.get("critical")), "signals": row.get("signals") or [],
        }
        for row in pending[: max(1, min(1000, int(limit)))]
    ]


def inspect_case(path: Path, case_id: str) -> dict[str, Any] | None:
    for row in read_jsonl(path):
        identifiers = {str(row.get("review_id") or ""), str(row.get("case_id") or ""), *map(str, row.get("source_case_ids") or [])}
        if case_id in identifiers:
            return {key: value for key, value in row.items() if not key.startswith("_source_")}
    return None


def _validate_annotation(row: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    if not str(row.get("intent") or "").strip() or str(row.get("intent")) == "unknown":
        missing.append("intent")
    if not isinstance(row.get("secondary_intents"), list):
        missing.append("secondary_intents")
    if not isinstance(row.get("entities"), Mapping):
        missing.append("entities")
    if not str(row.get("expected_behavior") or "").strip():
        missing.append("expected_behavior")
    if not isinstance(row.get("must_include"), list):
        missing.append("must_include")
    if not isinstance(row.get("must_not_include"), list):
        missing.append("must_not_include")
    if not str(row.get("category") or "").strip():
        missing.append("category")
    if not isinstance(row.get("critical"), bool):
        missing.append("critical")
    if not isinstance(row.get("generate_variations"), bool):
        missing.append("generate_variations")
    valid, reason = valid_feedback({**row, "candidate_for_training": True, "status": "pending_review"})
    if not valid:
        missing.append(f"privacy:{reason}")
    return sorted(set(missing))


def edit_case(path: Path, case_id: str, updates: Mapping[str, Any]) -> dict[str, Any]:
    unknown = set(updates) - EDITABLE_FIELDS
    if unknown:
        return {"status": "error", "error": "campos_no_editables", "fields": sorted(unknown)}
    rows = read_jsonl(path)
    changed: dict[str, Any] | None = None
    for row in rows:
        if str(row.get("review_id")) != case_id:
            continue
        for key, value in updates.items():
            if key in {"message_anonymized", "answer", "review_notes"}:
                result = _ANONYMIZER.anonymize(value, 1800)
                if not result.safe or _ANONYMIZER.has_private_placeholder(result.text):
                    return {"status": "error", "error": "contenido_privado_o_incierto", "field": key}
                value = result.text
            elif key == "history_anonymized":
                value, safe, _ = _ANONYMIZER.anonymize_history(value)
                if not safe or placeholders_in(value):
                    return {"status": "error", "error": "historial_privado_o_incierto"}
            row[key] = value
        row["status"] = "needs_edit"
        row["workflow_status"] = "needs_edit"
        row["edited_at"] = now_iso()
        changed = row
        break
    if changed is None:
        return {"status": "error", "error": "caso_no_encontrado", "case": case_id}
    write_jsonl(path, rows)
    missing = _validate_annotation(changed)
    return {"status": "ok", "case": case_id, "missing_for_approval": missing}


def approve_case(path: Path, case_id: str) -> dict[str, Any]:
    rows = read_jsonl(path)
    target: dict[str, Any] | None = None
    for row in rows:
        if str(row.get("review_id")) == case_id:
            target = row
            break
    if target is None:
        return {"status": "error", "error": "caso_no_encontrado", "case": case_id}
    missing = _validate_annotation(target)
    if missing:
        target["status"] = "needs_edit"
        target["workflow_status"] = "needs_edit"
        write_jsonl(path, rows)
        return {"status": "needs_edit", "case": case_id, "missing": missing, "promoted": False}
    target["status"] = "approved"
    target["workflow_status"] = "approved"
    target["approved_at"] = now_iso()
    target["requires_human_approval"] = False
    write_jsonl(path, rows)
    return {"status": "approved", "case": case_id, "promoted": False, "trained": False}


def reject_case(path: Path, case_id: str, reason: str, rejected_path: Path = DEFAULT_REJECTED) -> dict[str, Any]:
    rows = read_jsonl(path)
    target: dict[str, Any] | None = None
    for row in rows:
        if str(row.get("review_id")) == case_id:
            target = row
            break
    if target is None:
        return {"status": "error", "error": "caso_no_encontrado", "case": case_id}
    clean_reason = _ANONYMIZER.anonymize(reason or "rechazado_por_operador", 400)
    if not clean_reason.safe or _ANONYMIZER.has_private_placeholder(clean_reason.text):
        return {"status": "error", "error": "razon_privada_o_incierta"}
    target["status"] = "rejected"
    target["workflow_status"] = "rejected"
    target["rejected_at"] = now_iso()
    target["rejection_reason"] = clean_reason.text
    write_jsonl(path, rows)
    append_unique(rejected_path, {key: value for key, value in target.items() if not key.startswith("_source_")})
    return {"status": "rejected", "case": case_id, "promoted": False}


def build_dataset(review_path: Path = DEFAULT_REVIEW, output_path: Path = DEFAULT_APPROVED) -> dict[str, Any]:
    rows = read_jsonl(review_path)
    approved = [row for row in rows if _canonical_status(str(row.get("workflow_status") or row.get("status") or "")) == "approved"]
    cases: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for row in approved:
        valid, reason = valid_feedback({**row, "candidate_for_training": True, "status": "approved"})
        if not valid:
            skipped[reason] += 1
            continue


        expected = str(row.get("expected_behavior") or "Responder con evidencia; pedir el dato mínimo si no puede confirmarse.")
        review_id = str(row.get("review_id") or "")
        digest = hashlib.sha256(review_id.encode("utf-8")).hexdigest()[:12].upper()
        cases.append({
            "id": f"REAL-{digest}",
            "category": row.get("category") or "continuous_learning_reviewed",
            "message": row.get("message_anonymized", ""),
            "history": row.get("history_anonymized") or [],
            "intent": row.get("intent", "clarification"),
            "secondary_intents": row.get("secondary_intents") or [],
            "entities": row.get("entities") or {},
            "expected_behavior": expected,
            "must_include": row.get("must_include") or [],
            "must_not_include": row.get("must_not_include") or ["inventar precio", "inventar stock", "inventar compatibilidad"],
            "source": "real_anonymized",
            "critical": bool(row.get("critical")),
            "generate_variations": bool(row.get("generate_variations", False)),
            "split": "train",
            "review_id": review_id,
        })
    count = write_jsonl(output_path, cases)
    return {
        "status": "ok", "approved_reviews": len(approved), "written_cases": count,
        "skipped": dict(skipped), "output": str(output_path),
        "note": "Aún requiere entrenamiento y evaluación offline; no se promovió nada.",
    }


def _updates_from_args(args: argparse.Namespace) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if getattr(args, "data_file", None):
        updates.update(json.loads(args.data_file.read_text(encoding="utf-8")))
    if getattr(args, "data_json", None):
        updates.update(json.loads(args.data_json))
    return updates


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Aprendizaje local controlado de componente_ia")
    sub = root.add_subparsers(dest="command", required=True)
    collect_cmd = sub.add_parser("collect", help="Resumir feedback ya anonimizado")
    collect_cmd.add_argument("--input", type=Path, default=DEFAULT_FEEDBACK)
    review_cmd = sub.add_parser("review", help="Construir cola revisable")
    review_cmd.add_argument("--input", type=Path, default=DEFAULT_FEEDBACK)
    review_cmd.add_argument("--output", type=Path, default=DEFAULT_REVIEW)
    review_cmd.add_argument("--approve", action="append", default=[])
    review_cmd.add_argument("--reject", action="append", default=[])
    list_cmd = sub.add_parser("list-pending", help="Listar candidatos sin exponer mensajes crudos")
    list_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    list_cmd.add_argument("--limit", type=int, default=100)
    inspect_cmd = sub.add_parser("inspect", help="Inspeccionar un candidato anonimizado")
    inspect_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    inspect_cmd.add_argument("--case", required=True)
    approve_cmd = sub.add_parser("approve", help="Aprobar solo una anotacion humana completa")
    approve_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    approve_cmd.add_argument("--case", required=True)
    reject_cmd = sub.add_parser("reject", help="Rechazar un candidato")
    reject_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    reject_cmd.add_argument("--case", required=True)
    reject_cmd.add_argument("--reason", default="rechazado_por_operador")
    reject_cmd.add_argument("--output", type=Path, default=DEFAULT_REJECTED)
    edit_cmd = sub.add_parser("edit", help="Corregir la anotacion mediante JSON")
    edit_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    edit_cmd.add_argument("--case", required=True)
    edit_cmd.add_argument("--data-json")
    edit_cmd.add_argument("--data-file", type=Path)
    build_cmd = sub.add_parser("build-dataset", help="Exportar solo casos aprobados")
    build_cmd.add_argument("--input", type=Path, default=DEFAULT_REVIEW)
    build_cmd.add_argument("--output", type=Path, default=DEFAULT_APPROVED)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "collect":
            result = collect(args.input)
        elif args.command == "review":
            if args.approve or args.reject:
                changed = update_review_status(args.output, set(args.approve), "approved") if args.approve else 0
                changed += update_review_status(args.output, set(args.reject), "rejected") if args.reject else 0
                result = {"status": "ok", "reviews_changed": changed, "review_queue": str(args.output)}
            else:
                result = review(args.input, args.output)
        elif args.command == "list-pending":
            cases = list_pending_cases(args.input, args.limit)
            result = {"status": "ok", "count": len(cases), "cases": cases}
        elif args.command == "inspect":
            case = inspect_case(args.input, args.case)
            result = {"status": "ok", "case": case} if case else {"status": "error", "error": "caso_no_encontrado"}
        elif args.command == "approve":
            result = approve_case(args.input, args.case)
        elif args.command == "reject":
            result = reject_case(args.input, args.case, args.reason, args.output)
        elif args.command == "edit":
            updates = _updates_from_args(args)
            result = edit_case(args.input, args.case, updates) if updates else {
                "status": "error", "error": "se_requiere_data_json_o_data_file"
            }
        else:
            result = build_dataset(args.input, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "error", "error": exc.__class__.__name__, "message": str(exc)[:240]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") not in {"error", "needs_edit"} else 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "approve_case", "build_dataset", "cluster_cases", "collect", "deduplicate",
    "detect_new_vocabulary", "edit_case", "inspect_case", "list_pending_cases", "main",
    "reject_case", "review", "similarity", "update_review_status", "valid_feedback",
]
