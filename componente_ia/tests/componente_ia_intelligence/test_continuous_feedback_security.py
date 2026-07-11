import json

from componente_ia.anomaly_detector import AnomalyDetector
from componente_ia.feedback_anonymizer import FeedbackAnonymizer, session_hash
from componente_ia.feedback_store import FeedbackStore
from componente_ia.knowledge_updater import KnowledgeUpdater
from componente_ia.learning_pipeline import (
    approve_case,
    build_dataset,
    edit_case,
    inspect_case,
    list_pending_cases,
    reject_case,
    review,
)
from componente_ia.vocabulary_manager import VocabularyManager


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_anonymizer_covers_private_identifiers_and_preserves_tire_data():
    result = FeedbackAnonymizer().anonymize(
        "Me llamo Ana Pérez, correo ana@example.com, teléfono 0412-123-45-67, "
        "cédula V-12345678, placa AB123CD, pedido TR-99122, coordenadas 10.4806,-66.9036; "
        "busco LT265/70R17 121/118S"
    )
    assert result.safe
    assert "Ana Pérez" not in result.text
    assert "ana@example.com" not in result.text
    assert "0412" not in result.text
    assert "12345678" not in result.text
    assert "AB123CD" not in result.text
    assert "TR-99122" not in result.text
    assert "10.4806" not in result.text
    assert "LT265/70R17" in result.text
    assert "121/118S" in result.text


def test_anonymizer_is_fail_closed_and_store_does_not_persist_uncertain_case(tmp_path):
    path = tmp_path / "feedback.jsonl"
    store = FeedbackStore(path=path, persist=True)
    record = store.capture_passive_signal("Mi identificador es 123456789", fallback=True)
    assert record == {}
    assert not path.exists()
    assert store.snapshot()["privacy_drops"] == 1


def test_session_hash_is_not_the_session_and_is_stable_in_process():
    assert session_hash("session-private") == session_hash("session-private")
    assert "session-private" not in session_hash("session-private")
    assert session_hash(None) == "anon"


def test_anomaly_detector_captures_correction_repeat_gaps_and_web_failure():
    detector = AnomalyDetector()
    result = detector.detect(
        message="No entendiste, en realidad es una gandola Mack",
        previous_message="No entendiste en realidad es una gandola Mack",
        intent="truck_tire_advice",
        confidence=0.3,
        entities={"make": "mack", "vehicle_type": "gandola"},
        answer="Necesito datos",
        web_attempted=True,
        web_sources=0,
        inventory_matches=0,
    )
    assert result.candidate
    assert {
        "low_confidence", "user_corrected", "repeated_question", "web_without_source",
        "inventory_without_results", "entities_incomplete",
    } <= set(result.reasons)


def test_feedback_record_has_v2_review_contract(tmp_path):
    store = FeedbackStore(path=tmp_path / "feedback.jsonl", persist=True)
    record = store.capture_passive_signal(
        "Me refiero a cauchos para una Hilux 2020",
        session_id="private-session",
        history=[{"role": "user", "content": "quiero cauchos"}],
        intent="tire_recommendation",
        entities={"make": "toyota", "model": "hilux", "year": 2020},
        answer="¿Qué rin usa?",
        confidence=0.4,
        user_corrected=True,
        web_attempted=False,
        inventory_matches=0,
    )
    expected = {
        "case_id", "timestamp", "session_hash", "message_anonymized", "history_anonymized",
        "intent_predicted", "intent_confidence", "entities_predicted", "answer", "fallback",
        "web_attempted", "inventory_matches", "service_matches", "user_reformulated",
        "user_corrected", "operator_rating", "candidate_reason", "status",
    }
    assert expected <= set(record)
    assert record["case_id"].startswith("FB-")
    assert record["status"] == "pending_review"
    assert record["session_hash"] != "private-session"


def test_human_review_requires_complete_annotation_then_builds_case(tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    queue = tmp_path / "review.jsonl"
    approved = tmp_path / "approved.jsonl"
    store = FeedbackStore(path=feedback, persist=True)
    store.capture_passive_signal(
        "Tengo una gandola Mack y quiero cauchos para carretera",
        intent="truck_tire_advice",
        entities={"vehicle_type": "gandola", "make": "mack", "usage": ["carretera"]},
        answer="Necesito modelo, eje, carga y medida actual.",
        confidence=0.4,
        fallback=True,
    )
    review(feedback, queue)
    review_id = list_pending_cases(queue)[0]["review_id"]
    incomplete = approve_case(queue, review_id)
    assert incomplete["status"] == "needs_edit"
    annotation = {
        "intent": "truck_tire_advice",
        "secondary_intents": [],
        "entities": {"vehicle_type": "gandola", "make": "mack", "usage": ["carretera"]},
        "expected_behavior": "Pedir modelo, eje, carga y medida actual sin inventar medida.",
        "must_include": ["modelo", "medida actual"],
        "must_not_include": ["usa 295/80R22.5"],
        "category": "truck_fitment",
        "critical": True,
        "generate_variations": True,
    }
    assert edit_case(queue, review_id, annotation)["missing_for_approval"] == []
    assert approve_case(queue, review_id)["status"] == "approved"
    assert inspect_case(queue, review_id)["workflow_status"] == "approved"
    result = build_dataset(queue, approved)
    assert result["written_cases"] == 1
    case = _jsonl(approved)[0]
    assert case["intent"] == "truck_tire_advice"
    assert case["critical"] is True
    assert case["generate_variations"] is True


def test_rejection_is_recorded_and_never_promoted(tmp_path):
    queue = tmp_path / "review.jsonl"
    rejected = tmp_path / "rejected.jsonl"
    queue.write_text(json.dumps({
        "review_id": "REVIEW-1", "message_anonymized": "cauchos", "history_anonymized": [],
        "answer": "", "intent": "tire_inventory", "status": "pending",
        "workflow_status": "pending_review",
    }) + "\n", encoding="utf-8")
    result = reject_case(queue, "REVIEW-1", "etiqueta incorrecta", rejected)
    assert result == {"status": "rejected", "case": "REVIEW-1", "promoted": False}
    assert _jsonl(rejected)[0]["workflow_status"] == "rejected"


def test_vocabulary_proposals_need_review(tmp_path):
    manager = VocabularyManager(tmp_path / "vocabulary.json")
    proposals = manager.detect(["busco cauxos", "necesito cauxos"], ["cauchos"], minimum_frequency=2)
    assert proposals[0]["term"] == "cauxos"
    assert proposals[0]["status"] == "pending_review"
    stats = manager.merge_proposals(proposals)
    assert stats["auto_applied"] == 0
    assert manager.approved_aliases() == {}
    assert manager.approve("cauxos", suggested="cauchos", category="typo", reviewer="admin")
    assert manager.approved_aliases() == {"cauxos": "cauchos"}


def test_knowledge_rejects_dynamic_data_and_web_fitment_single_source(tmp_path):
    updater = KnowledgeUpdater(tmp_path / "knowledge.jsonl")
    dynamic = updater.stage(
        kind="business_faq", payload={"stock": 9}, source_type="manual"
    )
    assert dynamic["error"] == "dato_dinamico_no_entrenable"
    fitment = updater.stage(
        kind="fitment",
        payload={"make": "toyota", "model": "hilux", "size": "265/65R17"},
        source_type="web_reviewed",
        sources=[{"url": "https://example.com/fitment", "quality": "technical"}],
    )
    assert fitment["error"] == "fitment_web_requiere_dos_fuentes_independientes"
    assert not (tmp_path / "knowledge.jsonl").exists()


def test_approved_vehicle_alias_still_needs_explicit_apply(tmp_path):
    queue = tmp_path / "knowledge.jsonl"
    aliases = tmp_path / "aliases.json"
    aliases.write_text(json.dumps({"models": {"autana": {"aliases": ["autana"]}}}), encoding="utf-8")
    updater = KnowledgeUpdater(queue)
    staged = updater.stage(
        kind="vehicle_alias", payload={"model": "autana", "alias": "autanna"},
        source_type="approved_feedback", source_case_ids=["FB-1"],
    )
    candidate = staged["candidate_id"]
    assert "autanna" not in aliases.read_text(encoding="utf-8")
    assert updater.approve(candidate, reviewer="admin", review_notes="Alias regional confirmado")["applied"] is False
    assert "autanna" not in aliases.read_text(encoding="utf-8")
    assert updater.apply_vehicle_alias(candidate, reviewer="admin", aliases_path=aliases)["status"] == "promoted"
    assert "autanna" in aliases.read_text(encoding="utf-8")
