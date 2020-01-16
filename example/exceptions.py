from index import app
from index.types import Request, Response
from index.responses import PlainTextResponse


@app.exception_handler(404)
def not_found(request: Request, exc: Exception) -> Response:
    return PlainTextResponse("what do you want to do?")
