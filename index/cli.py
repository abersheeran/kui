import os
import sys
import time
import signal
import logging
import traceback
import subprocess
from typing import Optional
from multiprocessing import cpu_count

import click

from .config import LOG_LEVELS, config, logger
from .__version__ import __version__


def execute(command: str):
    click.echo("Execute command: ", nl=False)
    click.secho(command, fg="green")

    process = subprocess.Popen(command, shell=True)

    def sigterm_handler(signo, frame):
        process.terminate()
        process.wait()

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    while process.poll() is None:
        time.sleep(1)


@click.group(help=f"Index.py {__version__}")
@click.option("--env", default=config.ENV, help="set config.ENV")
@click.option("--debug/--no-debug", default=config.DEBUG, help="set config.DEBUG")
def main(env, debug):
    # change config
    config["env"] = env
    config["debug"] = debug
    # set index logger level
    logger.setLevel(LOG_LEVELS[config.log_level])


@main.command(help="use only uvicorn to deploy")
def serve():
    import uvicorn

    from . import app

    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        debug=config.DEBUG,
        lifespan="on",
    )


@main.command(help="use uvicorn to deploy by gunicorn")
@click.option("--workers", "-w", default=cpu_count())
@click.option("--daemon", "-d", default=False, is_flag=True)
@click.option("--configuration", "-c")
@click.argument("method")
def gunicorn(workers, daemon, configuration, method):
    if sys.platform in ("win32", "cygwin", "msys"):
        raise RuntimeError("gunicorn can't run on windows system.")
    if method == "start":
        command = (
            f"gunicorn -k uvicorn.workers.UvicornWorker"
            f" --bind {config.HOST}:{config.PORT}"
            f" --chdir {config.path}"
            f" --pid {os.path.join(config.path, '.pid')}"
            f" --log-level {config.LOG_LEVEL}"
            f"{' -D --log-file log.index' if daemon else ''}"
            f" -w {workers}"
            f"{' -c ' + configuration if configuration else ''}"
            f" index:app"
        )
        execute(command)
    elif method == "stop":
        execute("kill -TERM `cat .pid`")
    elif method == "reload":
        execute("kill -HUP `cat .pid`")


@main.command(help="run test in views")
@click.option(
    "--throw",
    default=False,
    is_flag=True,
    help="If there is an exception, throw it directly.",
)
@click.argument("path", default="--all")
def test(throw: bool, path: str):
    # import app
    from . import app
    from .test import TestClient
    from .applications import Filepath

    logging.basicConfig(
        format='[%(levelname)s] "%(pathname)s", line %(lineno)d, in %(funcName)s\n  Message: %(message)s',
        level=LOG_LEVELS[config.log_level],
    )
    logger.setLevel(logging.DEBUG)

    has_exception = False

    def run_test(view, uri: str, name: Optional[str] = None):
        """
        run test and print message
        """
        nonlocal has_exception

        for func in filter(
            lambda func: name == func.__name__ if name else True,
            view.Test(app, uri).all_test,
        ):
            # write to log file
            print("\n\n" + "=" * 24 + f"{uri} - {func.__name__}")

            printf(f" - {func.__name__} ", nl=False)
            try:
                func()
                printf("√", fg="green")
            except:
                printf("×", fg="red")
                if throw:
                    se()  # enable print to sys.stderr/stdout
                    traceback.print_exc()
                    st()
                else:
                    traceback.print_exc()
                has_exception = True

    with open(os.path.join(config.path, "index.test.log"), "w+") as logfile:
        # hack sys.stdout/stderr to log file
        setattr(sys.stdout, "_write_", sys.stdout.write)
        setattr(sys.stderr, "_write_", sys.stderr.write)

        def st():
            sys.stdout.flush()
            sys.stderr.flush()
            setattr(sys.stdout, "write", logfile.write)
            setattr(sys.stderr, "write", logfile.write)

        def se():
            sys.stdout.flush()
            sys.stderr.flush()
            setattr(sys.stdout, "write", sys.stdout._write_)
            setattr(sys.stderr, "write", sys.stderr._write_)

        def printf(message, **kwargs) -> None:
            se()
            click.secho(message, **kwargs)
            st()

        printf("Start test :)")
        with TestClient(app) as _:
            if path == "--all":
                for view, uri in Filepath.get_views():
                    printf(uri, fg="blue")
                    if not hasattr(view, "Test"):
                        printf(f" - No test. ?", fg="yellow")
                        continue
                    run_test(view, uri)
            else:
                printf(f"{path}", fg="blue")
                run_test(
                    Filepath.get_view(path.split(".")[0]),  # module
                    path.split(".")[0],  # uri
                    path.split(".")[1] if len(path.split(".")) == 2 else None,
                )

            print("\n")

    if has_exception:
        sys.exit(1)
    else:
        sys.exit(0)


@main.command(help="check .py files in program")
def check():
    from .autoreload import _import

    for root, dirs, files in os.walk(config.path):
        for file in files:
            if not file.endswith(".py"):
                continue
            abspath = os.path.join(root, file).replace("\\", "/")
            module = _import(abspath, nosleep=True)
