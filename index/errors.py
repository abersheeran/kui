from starlette.exceptions import HTTPException


class Http404(HTTPException):

    def __init__(self, detail: str = None) -> None:
        super().__init__(404, detail=detail)


class Http500(HTTPException):

    def __init__(self, detail: str = None) -> None:
        super().__init__(500, detail=detail)
