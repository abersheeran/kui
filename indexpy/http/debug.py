import asyncio
import html
import inspect
import pprint
import traceback
import typing

from starlette.concurrency import run_in_threadpool

from indexpy.types import ASGIApp, Message, Receive, Scope, Send
from indexpy.http.request import Request
from indexpy.http.responses import Response, HTMLResponse, PlainTextResponse

STYLES = """
:root {
    font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
}
* {
    box-sizing: border-box;
}
code, pre, .code {
    font-family: "Biaodian Pro Sans CNS", Menlo, Consolas, Courier, "Zhuyin Heiti", "Han Heiti", monospace;
}
.traceback-container {
    border: 1px solid #038BB8;
}
.traceback-title {
    background-color: #038BB8;
    color: lemonchiffon;
    padding: 15px;
    font-size: 20px;
    margin: 0px;
}
.frame {
    position: relative;
}
.frame .more {
    display: block;
    height: 100%;
    width: 100%;
    opacity: 0;
    position: absolute;
    z-index: 1;
    top: 0;
}
.frame .more + .detail {
    display: none;
    position: relative;
    z-index: 2;
}
.frame .more:checked + .detail {
    display: block;
}
.frame-line {
    padding-left: 10px;
}
.center-line {
    background-color: #038BB8;
    color: #f9f6e1;
    padding: 5px 0px 5px 5px;
}
.lineno {
    margin-right: 5px;
}
.frame-title {
    font-weight: unset;
    padding: 15px 10px;
    margin: 0px;
    color: #191f21;
    font-size: 17px;
    border-top: 1px solid #038BB8;
}
.source {
  font-size: small;
}
table {
    width: 100%;
    border-spacing: 0px;
    padding: 0 10px;
    margin-top: 25px;
}
table pre {
    white-space: pre-wrap;
}
table td {
    padding: 10px;
    border-top: 1px solid #c7dce8;
}
table tr td:nth-child(1) {
    padding-left: 0px;
}
table tr td:nth-last-child(1) {
    background-color: #f7f7f7;
}
"""

TEMPLATE = """
<html>
    <head>
        <style type='text/css'>
            {styles}
        </style>
        <title>Index.py Debugger</title>
    </head>
    <body>
        <h1>500 Server Error</h1>
        <h2>{error}</h2>
        <div class="traceback-container">
            <p class="traceback-title">Traceback</p>
            <div>{exc_html}</div>
        </div>
    </body>
</html>
"""

FRAME_TEMPLATE = """
<div class="frame">
    <p class="frame-title"><code class="frame-filename">{frame_filename}</code>
    in <b><code>{frame_name}</code></b> at line {frame_lineno}</p>
    <input type="radio" name="more" {checked} class="more"/>
    <div class="detail">
        <div id="{frame_filename}-{frame_lineno}" class="source">
            {code_context}
        </div>
        {locals}
    </div>
</div>
"""

VARS = """
<table>
    <tbody>
        {vars}
    </tbody>
</table>
"""

LINE = """
<p><span class="frame-line code">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""

CENTER_LINE = """
<p class="center-line"><span class="frame-line center-line code">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""


class ServerErrorMiddleware:
    """
    Handles returning 500 responses when a server error occurs.

    If 'debug' is set, then traceback responses will be returned,
    otherwise the designated 'handler' will be called.

    This middleware class should generally be used to wrap *everything*
    else up, so that unhandled exceptions anywhere in the stack
    always result in an appropriate 500 response.
    """

    def __init__(
        self, app: ASGIApp, handler: typing.Callable = None, debug: bool = False
    ) -> None:
        self.app = app
        self.handler = handler
        self.debug = debug

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Message) -> None:
            nonlocal response_started, send

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as exc:
            if not response_started:
                request = scope["app"].factory_class.http(scope)
                if self.debug:
                    # In debug mode, return traceback responses.
                    response = self.debug_response(request, exc)
                elif self.handler is None:
                    # Use our default 500 error handler.
                    response = self.error_response(request, exc)
                else:
                    # Use an installed 500 error handler.
                    if asyncio.iscoroutinefunction(self.handler):
                        response = await self.handler(request, exc)
                    else:
                        response = await run_in_threadpool(self.handler, request, exc)

                await response(scope, receive, send)

            # We always continue to raise the exception.
            # This allows servers to log the error, or allows test clients
            # to optionally raise the error within the test case.
            raise exc from None

    def format_line(
        self, index: int, line: str, frame_lineno: int, frame_index: int
    ) -> str:
        values = {
            # HTML escape - line could contain < or >
            "line": html.escape(line).replace(" ", "&nbsp"),
            "lineno": (frame_lineno - frame_index) + index,
        }

        if index != frame_index:
            return LINE.format(**values)
        return CENTER_LINE.format(**values)

    def generate_frame_html(self, frame: inspect.FrameInfo, is_collapsed: bool) -> str:
        code_context = "".join(
            self.format_line(index, line, frame.lineno, frame.index)  # type: ignore
            for index, line in enumerate(frame.code_context or [])
        )
        _locals_vars = frame.frame.f_locals.copy()
        locals_var = VARS.format(
            title="locals",
            vars="".join(
                [
                    "<tr><td><pre>{name}</pre></td><td><pre>{value}</pre></td></tr>".format(
                        name=name, value=html.escape(pprint.pformat(value))
                    )
                    for name, value in _locals_vars.items()
                ]
            ),
        )

        values = {
            # HTML escape - filename could contain < or >, especially if it's a virtual file e.g. <stdin> in the REPL
            "frame_filename": html.escape(frame.filename),
            "frame_lineno": frame.lineno,
            # HTML escape - if you try very hard it's possible to name a function with < or >
            "frame_name": html.escape(frame.function),
            "code_context": code_context,
            "checked": "checked" if not is_collapsed else "",
            "locals": locals_var,
        }
        return FRAME_TEMPLATE.format(**values)

    def generate_html(self, exc: Exception, limit: int = 7) -> str:
        traceback_obj = traceback.TracebackException.from_exception(
            exc, capture_locals=True
        )
        frames = inspect.getinnerframes(
            traceback_obj.exc_traceback, limit  # type: ignore
        )

        exc_html = ""
        is_collapsed = False
        for frame in reversed(frames):
            exc_html += self.generate_frame_html(frame, is_collapsed)
            is_collapsed = True

        # escape error class and text
        error = f"{html.escape(traceback_obj.exc_type.__name__)}: {html.escape(str(traceback_obj))}"

        return TEMPLATE.format(styles=STYLES, error=error, exc_html=exc_html)

    def generate_plain_text(self, exc: Exception) -> str:
        return "".join(traceback.format_tb(exc.__traceback__))

    def debug_response(self, request: Request, exc: Exception) -> Response:
        accept = request.headers.get("accept", "")

        if "text/html" in accept:
            content = self.generate_html(exc)
            return HTMLResponse(content, status_code=500)
        content = self.generate_plain_text(exc)
        return PlainTextResponse(content, status_code=500)

    def error_response(self, request: Request, exc: Exception) -> Response:
        return PlainTextResponse("Internal Server Error", status_code=500)
