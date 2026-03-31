from typing import Any

from kui.asgi import FileResponse, SendEventResponse, StreamResponse


def test_file_response_docs_with_content_type_and_headers() -> None:
    docs: Any = FileResponse[
        "application/pdf",
        {"Content-Disposition": {"schema": {"type": "string"}}},
    ]

    assert "200" in docs
    assert "206" in docs
    assert docs["200"]["headers"]["Content-Disposition"] == {
        "schema": {"type": "string"}
    }


def test_send_event_response_docs_with_status_and_headers() -> None:
    docs: Any = SendEventResponse[200, {"X-Stream": {"schema": {"type": "string"}}}]

    assert "200" in docs
    assert docs["200"]["headers"]["X-Stream"] == {"schema": {"type": "string"}}


def test_stream_response_docs_with_status_and_headers() -> None:
    docs: Any = StreamResponse[200, {"X-Stream": {"schema": {"type": "string"}}}]

    assert "200" in docs
    assert docs["200"]["headers"]["X-Stream"] == {"schema": {"type": "string"}}
