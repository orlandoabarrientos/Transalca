import json

from componente_ia.feedback_store import FeedbackStore, anonymize_text
from componente_ia.learning_pipeline import build_dataset, collect, review, update_review_status


def _read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_feedback_is_anonymized_and_persistence_is_opt_in(tmp_path):
    path = tmp_path / "feedback.jsonl"
    store = FeedbackStore(path=path, persist=False)
    record = store.capture_passive_signal(
        "Mi correo es cliente@example.com, teléfono 0412-123-45-67 y busco 265/65R17",
        intent="tire_inventory",
        entities={"requested_tire_size": "265/65R17", "order_reference": "PRIVATE-123"},
        answer="No hay evidencia de inventario.",
        confidence=0.4,
        fallback=True,
    )
    assert "cliente@example.com" not in record["message_anonymized"]
    assert "0412" not in record["message_anonymized"]
    assert record["entities"] == {"requested_tire_size": "265/65R17"}
    assert not path.exists()


def test_persistent_feedback_never_writes_raw_private_data(tmp_path):
    path = tmp_path / "feedback.jsonl"
    store = FeedbackStore(path=path, persist=True)
    store.capture_passive_signal(
        "pedido ABCD-9911, clave=supersecreta, email persona@example.org",
        intent="order_status",
        fallback=True,
    )
    raw = path.read_text(encoding="utf-8")
    assert "supersecreta" not in raw
    assert "persona@example.org" not in raw
    assert "ABCD-9911" not in raw


def test_anonymizer_preserves_automotive_measurements():
    clean = anonymize_text("LT265/70R17 121/118S, 295/80R22.5 y 11R22.5")
    assert "LT265/70R17" in clean
    assert "121/118S" in clean
    assert "295/80R22.5" in clean
    assert "11R22.5" in clean


def test_review_deduplicates_and_requires_explicit_approval(tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    queue = tmp_path / "review.jsonl"
    approved = tmp_path / "approved.jsonl"
    store = FeedbackStore(path=feedback, persist=True)
    for message in ("No entendiste, busco cauchos de gandola", "No entendiste, busco cauchos de gandola"):
        store.capture_passive_signal(
            message,
            intent="truck_tire_advice",
            answer="Necesito más datos.",
            confidence=0.2,
            fallback=True,
            signals=["user_correction"],
        )
    summary = review(feedback, queue)
    assert summary["duplicates"] == 1
    assert summary["auto_applied"] == 0
    pending = _read(queue)
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"
    assert pending[0]["requires_human_approval"] is True
    before = build_dataset(queue, approved)
    assert before["written_cases"] == 0
    assert update_review_status(queue, {pending[0]["review_id"]}, "approved") == 1
    after = build_dataset(queue, approved)
    assert after["written_cases"] == 1
    assert _read(approved)[0]["source"] == "real_anonymized"


def test_private_placeholders_are_rejected_from_training(tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    feedback.write_text(
        json.dumps({
            "case_id": "CASE-1",
            "message_anonymized": "mi correo [EMAIL] y necesito cauchos",
            "intent": "tire_inventory",
            "candidate_for_training": True,
        }) + "\n",
        encoding="utf-8",
    )
    stats = collect(feedback)
    assert stats["candidate_records"] == 0
    assert stats["validation"]["contiene_marcador_privado"] == 1

