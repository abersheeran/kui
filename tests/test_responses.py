from kui.asgi import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    SendEventResponse,
    StreamResponse,
)


def test_html_response():
    assert HTMLResponse[200] == {
        "200": {
            "content": {"text/html": {"schema": {"type": "string"}}},
            "description": "Request fulfilled, document follows",
            "headers": {},
        }
    }
    assert HTMLResponse[
        200,
        {
            "Location": {
                "description": "URL of created resource",
                "schema": {"type": "string"},
            }
        },
    ] == {
        "200": {
            "content": {"text/html": {"schema": {"type": "string"}}},
            "description": "Request fulfilled, document follows",
            "headers": {
                "Location": {
                    "description": "URL of created resource",
                    "schema": {"type": "string"},
                }
            },
        }
    }


def test_plain_text_response():
    assert PlainTextResponse[200] == {
        "200": {
            "content": {"text/plain": {"schema": {"type": "string"}}},
            "description": "Request fulfilled, document follows",
            "headers": {},
        }
    }
    assert PlainTextResponse[
        200,
        {
            "Location": {
                "description": "URL of created resource",
                "schema": {"type": "string"},
            }
        },
    ] == {
        "200": {
            "content": {"text/plain": {"schema": {"type": "string"}}},
            "description": "Request fulfilled, document follows",
            "headers": {
                "Location": {
                    "description": "URL of created resource",
                    "schema": {"type": "string"},
                }
            },
        }
    }


def test_json_response():
    assert JSONResponse[200] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "headers": {},
        }
    }
    assert JSONResponse[
        200,
        {
            "Location": {
                "description": "URL of created resource",
                "schema": {"type": "string"},
            }
        },
    ] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "headers": {
                "Location": {
                    "description": "URL of created resource",
                    "schema": {"type": "string"},
                }
            },
        }
    }


def test_redirect_response():
    assert RedirectResponse[200] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "headers": {"Location": {"schema": {"type": "string"}}},
        }
    }
    assert RedirectResponse[
        200,
        {
            "Location": {
                "description": "URL of created resource",
                "schema": {"type": "string"},
            }
        },
    ] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "headers": {
                "Location": {
                    "description": "URL of created resource",
                    "schema": {"type": "string"},
                }
            },
        }
    }


def test_file_response():
    assert FileResponse["text/html"] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "content": {
                "text/html": {"schema": {"type": "string", "format": "binary"}}
            },
            "headers": {},
        },
        "206": {
            "description": "Partial content follows",
            "content": {
                "text/html": {"schema": {"type": "string", "format": "binary"}}
            },
            "headers": {},
        },
    }


def test_send_event_response():
    assert SendEventResponse[200] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
            "headers": {},
        }
    }


def test_stream_response():
    assert StreamResponse[200] == {
        "200": {
            "description": "Request fulfilled, document follows",
            "headers": {
                "Transfer-Encoding": {
                    "schema": {"type": "string"},
                    "description": "chunked",
                },
            },
        }
    }
