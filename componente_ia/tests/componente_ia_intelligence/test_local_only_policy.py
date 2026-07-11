from pathlib import Path

from componente_ia.assistant_orchestrator import AssistantOrchestrator
from componente_ia.entity_extractor import extract
from componente_ia.intent_router import IntentResult

def test_no_external_provider_module_exists():
    path = Path(__file__).resolve().parents[2] / "providers" / "external_llm_provider.py"
    assert not path.exists()


def test_router_and_plan_have_no_external_generation_layer():
    assistant = AssistantOrchestrator()
    entities = extract("Tengo una Hilux 2020 y quiero cauchos A/T rin 17")
    plan = assistant.build_plan(
        IntentResult("tire_recommendation", confidence=0.01), entities, context={},
    )
    assert all("external" not in action and "llm" not in action for action in plan.actions)
    assert assistant.health()["generation"]["provider"] == "local_only"


def test_orchestrator_and_router_sources_have_no_remote_model_configuration():
    root = Path(__file__).resolve().parents[2]
    source = "\n".join(
        (root / name).read_text(encoding="utf-8").lower()
        for name in ("assistant_orchestrator.py", "intent_router.py", ".env.example")
    )
    assert "assistant_llm_" not in source
    assert "compose_with_external" not in source
    assert "llm_provider" not in source
