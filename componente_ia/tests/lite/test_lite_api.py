"""The Flask boundary must preserve the public contract and lazy full mode."""

import os
from pathlib import Path
import subprocess
import sys
import types

import pytest


@pytest.fixture
def client(assistant, monkeypatch):
    monkeypatch.setenv("TRANSALCA_AI_MODE", "lite")
    from componente_ia import ai_mode, api_asistente

    monkeypatch.setattr(ai_mode, "get_default_orchestrator", lambda: assistant)
    monkeypatch.setattr(api_asistente, "get_default_orchestrator", lambda: assistant)
    monkeypatch.setattr(api_asistente, "RATE_LIMIT_MAX_REQUESTS", 0)
    app = api_asistente.create_app()
    app.config.update(TESTING=True, SECRET_KEY="isolated-lite-test")
    return app.test_client()


def test_lite_message_api_preserves_frontend_contract(client):
    response = client.post("/api/asistente/mensaje", json={
        "mensaje": "¿Tienen 265/65R17?", "session_id": "session-lite-api-01",
    })
    assert response.status_code == 200
    payload = response.get_json()
    assert {
        "status", "respuesta", "message", "intent", "primary_intent",
        "secondary_intents", "confidence", "needs_clarification", "matches",
        "sources", "diagnostics", "session_id", "request_id", "timestamp",
    } <= payload.keys()
    assert payload["respuesta"] == payload["message"]
    assert payload["diagnostics"]["ai_mode"] == "lite"
    assert payload["engine_module"] == "lite_assistant"
    assert payload["matches"]


def test_api_reset_clears_only_named_lite_session(client, assistant):
    client.post("/api/asistente/mensaje", json={"mensaje": "265/65R17", "session_id": "session-to-reset"})
    response = client.post("/api/asistente/reset", json={"session_id": "session-to-reset"})
    assert response.status_code == 200
    assert not assistant.state_store.get("session-to-reset")["tire_size"]


@pytest.mark.parametrize("session_id", [None, "", "short", "../unsafe", "x" * 81, 100])
def test_api_reset_rejects_invalid_session_ids(client, session_id):
    assert client.post("/api/asistente/reset", json={"session_id": session_id}).status_code == 400


def test_reset_is_not_exposed_as_full_session_mutation(client, monkeypatch):
    monkeypatch.setenv("TRANSALCA_AI_MODE", "full")
    assert client.post("/api/asistente/reset", json={"session_id": "session-to-reset"}).status_code == 404


@pytest.mark.parametrize("message", ["", "x" * 1001])
def test_api_message_length_validation(client, message):
    assert client.post("/api/asistente/mensaje", json={"mensaje": message}).status_code == 400


def test_lite_health_and_metrics_do_not_need_model_identity(client):
    health = client.get("/api/asistente/health")
    assert health.status_code == 200
    assert health.get_json()["engine_module"] == "lite_assistant"
    assert health.get_json()["build_id"] == "lite-v1"
    assert client.get("/api/asistente/metrics").status_code == 200


@pytest.mark.parametrize("path", ["/", "/componente_ia/chat_widget.js", "/componente_ia/chat_widget.css"])
def test_standalone_lite_demo_routes_remain_available(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("mode", [None, "full"])
def test_unset_and_full_delegate_to_existing_full_entrypoint(monkeypatch, mode):
    from componente_ia import ai_mode

    if mode is None:
        monkeypatch.delenv("TRANSALCA_AI_MODE", raising=False)
    else:
        monkeypatch.setenv("TRANSALCA_AI_MODE", mode)
    calls = []
    stub = types.ModuleType("componente_ia.assistant_orchestrator")
    stub.build_response = lambda *args, **kwargs: (calls.append((args, kwargs)) or ({"full": True}, 200))
    monkeypatch.setitem(sys.modules, "componente_ia.assistant_orchestrator", stub)
    assert ai_mode.build_response("hola", session_id="full-control") == ({"full": True}, 200)
    assert calls == [(("hola",), {"session_id": "full-control", "history": None})]


def test_lite_runs_when_full_candidate_imports_and_registry_initialization_are_forbidden():
    project = Path(__file__).resolve().parents[3]
    script = r'''
import importlib.abc
import os
import sys

os.environ["TRANSALCA_AI_MODE"] = "lite"
os.environ["ASSISTANT_WEB_ENABLED"] = "0"
os.environ["ASSISTANT_RATE_LIMIT"] = "0"

class BlockFull(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {
            "componente_ia.assistant_orchestrator",
            "componente_ia.candidate_runtime",
            "componente_ia.candidate_shadow",
        } or ".candidates." in fullname:
            raise AssertionError("Lite loaded a full/candidate module: " + fullname)
        return None

sys.meta_path.insert(0, BlockFull())
from componente_ia.model_registry import ModelRegistry
registry_calls = []
def forbidden_registry(*args, **kwargs):
    registry_calls.append(True)
    raise AssertionError("Lite initialized ModelRegistry")
ModelRegistry.__init__ = forbidden_registry

def prohibit_candidate_reads(event, args):
    if event == "open":
        path = str(args[0]).replace("\\", "/").lower()
        if "/candidates/" in path or "/runtimepack/" in path:
            raise AssertionError("Lite read sealed candidate files")
sys.addaudithook(prohibit_candidate_reads)

from componente_ia.api_asistente import create_app
client = create_app().test_client()
result = client.post("/api/asistente/mensaje", json={"mensaje": "Hola", "session_id": "isolated-lite-01"})
assert result.status_code == 200, result.get_json()
assert result.get_json()["diagnostics"]["ai_mode"] == "lite"
assert client.get("/api/asistente/health").status_code == 200
assert not registry_calls
assert "componente_ia.assistant_orchestrator" not in sys.modules
print("lite-isolation-ok")
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TRANSALCA_AI_MODE="lite")
    completed = subprocess.run([sys.executable, "-c", script], cwd=project, env=env,
                               capture_output=True, text=True, timeout=40)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "lite-isolation-ok" in completed.stdout
