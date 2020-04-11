import os
import sys
import typing
import logging
import traceback

import click
import requests
from requests import Response
from uvicorn.importer import import_from_string
from starlette.testclient import TestClient as _TestClient, ASGI2App, ASGI3App
from starlette.types import ASGIApp

from .applications import Index
from .config import here, LOG_LEVELS, Config


class TestClient:
    def __init__(
        self,
        app: typing.Union[ASGI2App, ASGI3App],
        uri: str = "",
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
    ) -> None:
        self.uri = uri
        self.__client = _TestClient(app, base_url, raise_server_exceptions, root_path)

    def get(self, *args, **kwargs) -> Response:
        return self.__client.get(self.uri, *args, **kwargs)

    def options(self, *args, **kwargs) -> Response:
        return self.__client.options(self.uri, *args, **kwargs)

    def head(self, *args, **kwargs) -> Response:
        return self.__client.head(self.uri, *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        return self.__client.post(self.uri, *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self.__client.put(self.uri, *args, **kwargs)

    def patch(self, *args, **kwargs) -> Response:
        return self.__client.patch(self.uri, *args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        return self.__client.delete(self.uri, *args, **kwargs)

    def websocket_connect(
        self, subprotocols: typing.Sequence[str] = None, **kwargs: typing.Any
    ) -> typing.Any:
        return self.__client.websocket_connect(
            self.uri, subprotocols=subprotocols, **kwargs
        )

    def __enter__(self) -> requests.Session:
        return self.__client.__enter__()

    def __exit__(self, *args: typing.Any) -> None:
        return self.__client.__exit__()


class TestView:
    @property
    def client(self) -> TestClient:
        app = Index()
        path = app.indexfile.get_path_from_module_name(self.__class__.__module__)
        if path is None:
            raise Exception("What's wrong with you?")
        return TestClient(app, path)

    @property
    def all_test(self) -> typing.List[typing.Callable]:
        return [
            getattr(self, name)
            for name in dir(self)
            if name.startswith("test_") and callable(getattr(self, name))
        ]


@click.option(
    "--throw",
    default=False,
    is_flag=True,
    help="If there is an exception, throw it directly.",
)
@click.option(
    "-app",
    "--application",
    default="indexpy:app",
    help="ASGI Application, like: main:app",
)
@click.argument("path", default="--all")
def cmd_test(throw: bool, application: str, path: str):

    app: Index = import_from_string(application)

    logging.basicConfig(
        format='[%(levelname)s] "%(pathname)s:%(lineno)d", in %(funcName)s\n>: %(message)s',
        level=LOG_LEVELS[Config().log_level],
    )
    logging.getLogger("index").setLevel(logging.DEBUG)

    has_exception = False

    def run_test(view, uri: str, name: typing.Optional[str] = None):
        """
        run test and print message
        """
        nonlocal has_exception

        for func in filter(
            lambda func: name == func.__name__ if name else True, view.Test().all_test,
        ):
            # write to log file
            print(
                "\n\n"
                + f"{uri} - {func.__name__}"
                + " "
                + "<" * (89 - len(f"{uri} - {func.__name__}"))
            )

            printf(f" - {func.__name__} ", nl=False)
            try:
                func()
                printf("PASS", fg="green")
            except:
                import inspect

                printf("ERROR", fg="red")
                traceback.print_exc()
                has_exception = True

    with open(os.path.join(here, "index.test.log"), "w+", encoding="utf8") as logfile:
        # hack sys.stdout/stderr to log file
        stdout_write = sys.stdout.write
        stderr_write = sys.stderr.write

        def st():
            sys.stdout.flush()
            sys.stderr.flush()
            setattr(sys.stdout, "write", logfile.write)
            setattr(sys.stderr, "write", logfile.write)

        def se():
            sys.stdout.flush()
            sys.stderr.flush()
            setattr(sys.stdout, "write", stdout_write)
            setattr(sys.stderr, "write", stderr_write)

        def printf(message, **kwargs) -> None:
            se()
            click.secho(message, **kwargs)
            st()

        print_traceback = traceback.print_exc

        if throw:

            def print_exc(limit=None, file=None, chain=True):
                se()
                print_traceback(limit, file, chain)
                st()

            traceback.print_exc = print_exc

        printf(f"Start {'all' if path=='--all' else path} test (^-^)")
        try:
            with TestClient(app):
                if path == "--all":
                    for view, uri in app.indexfile.get_views():
                        if not hasattr(view, "Test"):
                            printf(uri, fg="blue", nl=False)
                            printf(f" No Test?", fg="yellow")
                            continue
                        printf(uri, fg="blue")
                        run_test(view, uri)
                else:
                    printf(f"{path}", fg="blue")
                    run_test(
                        app.indexfile.get_view(path.split(".")[0]),  # module
                        path.split(".")[0],  # uri
                        path.split(".")[1] if len(path.split(".")) == 2 else None,
                    )
                print("\n")
        except:
            printf("Error in events", fg="red")
            traceback.print_exc()

        printf("End test.")

    if has_exception:
        sys.exit(1)
    else:
        sys.exit(0)
