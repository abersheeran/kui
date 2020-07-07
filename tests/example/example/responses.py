from dataclasses import dataclass, asdict

from indexpy.http.responses import automatic, Response, JSONResponse


@dataclass
class Error:
    code: int = 0
    title: str = ""
    message: str = ""


@automatic.register(Error)
def _error_json(error: Error, status: int = 400) -> Response:
    return JSONResponse(asdict(error), status)
