import typing

from indexpy.http.responses import automatic, Response, JSONResponse


@automatic.register(list)
@automatic.register(dict)
def json_response(
    body: typing.Union[list, dict], status: int = 200, headers: dict = None
) -> Response:
    return JSONResponse(body, status, headers)
