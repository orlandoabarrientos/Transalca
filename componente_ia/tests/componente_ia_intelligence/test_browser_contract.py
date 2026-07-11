from pathlib import Path

from componente_ia.api_asistente import create_app


COMPONENT = Path(__file__).resolve().parents[2]


def test_widget_script_and_styles_are_served_by_standalone_app():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    page = client.get("/")
    js = client.get("/componente_ia/chat_widget.js")
    css = client.get("/componente_ia/chat_widget.css")
    assert page.status_code == js.status_code == css.status_code == 200
    assert "/api/asistente/mensaje" in js.get_data(as_text=True)
    assert "chatToggleBtn" in js.get_data(as_text=True)
    assert "chat-toggle" in css.get_data(as_text=True)


def test_widget_uses_json_contract_timeout_and_bounded_history():
    script = (COMPONENT / "chat_widget.js").read_text(encoding="utf-8")
    assert "Content-Type': 'application/json'" in script
    assert "AbortController" in script
    assert "messages.slice(-7)" in script
    assert "data.respuesta || data.message" in script
    assert "data.sources || []" in script
    assert "credentials: 'same-origin'" in script


def test_widget_escapes_dynamic_text_before_inserting_html():
    script = (COMPONENT / "chat_widget.js").read_text(encoding="utf-8")


    assert "text.textContent = msg.text" in script
    assert "item.textContent = domain ?" in script
    assert "parsed.protocol === 'http:' || parsed.protocol === 'https:'" in script
    assert "item.rel = 'noopener noreferrer'" in script
