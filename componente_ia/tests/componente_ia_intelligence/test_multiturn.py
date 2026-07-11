from componente_ia.conversation_memory import ConversationMemory
from componente_ia.entity_extractor import extract


def test_followup_inherits_vehicle_and_adds_year():
    memory = ConversationMemory()
    memory.update("session-a", extract("Tengo una Jeep Grand Cherokee"), intent="tire_size_lookup")
    context = memory.resolve("session-a", entities=extract("Es 2018"))
    assert context.entities["make"] == "jeep"
    assert context.entities["model"] == "grand cherokee"
    assert context.entities["year"] == 2018
    assert {"make", "model"} <= set(context["inherited_fields"])


def test_vehicle_correction_clears_tire_and_previous_products():
    memory = ConversationMemory()
    memory.update(
        "session-a",
        extract("Hilux 2020 rin 17 A/T"),
        evidence={"inventory": [{"name": "Producto anterior"}]},
        intent="tire_recommendation",
    )
    memory.update("session-a", extract("En realidad es una Prado"), intent="tire_size_lookup")
    state = memory.get("session-a")
    assert state["vehicle"]["model"] == "prado"
    assert state["tire"] == {}
    assert state["last_products"] == []


def test_sessions_are_strictly_isolated():
    memory = ConversationMemory()
    memory.update("session-a", extract("Toyota Hilux 2020"), intent="tire_size_lookup")
    memory.update("session-b", extract("Ford Explorer 2018"), intent="tire_size_lookup")
    a = memory.resolve("session-a", entities=extract("rin 17"))
    b = memory.resolve("session-b", entities=extract("rin 20"))
    assert (a.entities["make"], a.entities["model"], a.entities["year"]) == ("toyota", "hilux", 2020)
    assert (b.entities["make"], b.entities["model"], b.entities["year"]) == ("ford", "explorer", 2018)
    assert a.entities["requested_rim"] == 17
    assert b.entities["requested_rim"] == 20


def test_ttl_expires_session_without_sleeping():
    now = [100.0]
    memory = ConversationMemory(ttl_seconds=10, clock=lambda: now[0])
    memory.update("session-a", extract("Hilux 2020"), intent="tire_size_lookup")
    now[0] = 111.0
    context = memory.resolve("session-a", entities=extract("rin 17"))
    assert context.entities["model"] is None
    assert memory.stats()["sessions"] == 0


def test_capacity_evicts_least_recent_session():
    memory = ConversationMemory(max_sessions=2)
    memory.update("session-a", extract("Hilux"))
    memory.update("session-b", extract("Explorer"))
    memory.update("session-c", extract("Corolla"))
    assert memory.get("session-a") is None
    assert memory.get("session-b")["vehicle"]["model"] == "explorer"
    assert memory.get("session-c")["vehicle"]["model"] == "corolla"


def test_client_history_uses_only_user_messages():
    memory = ConversationMemory()
    history = [
        {"role": "assistant", "content": "Toyota Hilux 2020"},
        {"role": "user", "content": "Tengo una Explorer 2018"},
    ]
    context = memory.resolve("new-session", history=history, entities=extract("rin 20"))
    assert context.entities["make"] == "ford"
    assert context.entities["model"] == "explorer"


def test_orchestrator_out_of_scope_does_not_reuse_previous_vehicle(assistant):
    assistant.handle("Tengo una Hilux 2020 rin 17", session_id="scope-session")
    payload, _ = assistant.handle("¿Quién ganó el partido?", session_id="scope-session")
    assert payload["intent"] == "out_of_scope"
    assert "hilux" not in payload["respuesta"].lower()


def test_orchestrator_incremental_year_and_vehicle_correction(assistant):
    assistant.handle("Tengo una Jeep Grand Cherokee", session_id="follow-session")
    year_payload, _ = assistant.handle("Es 2018", session_id="follow-session")
    assert year_payload["entities"]["year"] == 2018
    assistant.handle("En realidad es una Hilux", session_id="follow-session")
    state = assistant.memory.get("follow-session")
    assert state["vehicle"]["model"] == "hilux"
    assert state["tire"] == {}


def test_product_reference_followup_rechecks_catalog_for_branch_and_first_item(assistant):
    assistant.handle(
        "Tengo una Hilux 2020 rin 17, ¿qué A/T tienen?", session_id="product-followup",
    )
    branch, _ = assistant.handle("¿En qué sucursal?", session_id="product-followup")
    assert branch["intent"] == "branch"
    assert "RoadMax 265/65R17 A/T" in branch["respuesta"]
    assert "sucursal Centro" in branch["respuesta"]
    first, _ = assistant.handle("¿El primero?", session_id="product-followup")
    assert "RoadMax 265/65R17 A/T" in first["respuesta"]
    assert "Datos verificados nuevamente" in first["respuesta"]
