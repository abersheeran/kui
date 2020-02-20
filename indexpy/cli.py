import os
import sys
import time
import signal
import logging
import importlib
import subprocess
from multiprocessing import cpu_count

import click
import uvicorn

from .utils import _import_module
from .config import LOG_LEVELS, config
from .applications import Index
from .test import cmd_test
from .autoreload import cmd_check
from .__version__ import __version__


def execute(command: str):
    click.echo("Execute command: ", nl=False)
    click.secho(command, fg="green")

    process = subprocess.Popen(command)

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
    Index().debug = debug
    # set index logger level
    logging.getLogger("index").setLevel(LOG_LEVELS[config.log_level])
    # loading preset functions
    importlib.import_module("indexpy.preset")
    _import_module("main")


@main.command(help="use only uvicorn to deploy")
def serve():
    uvicorn.run(
        "indexpy:app",
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        interface="asgi3",
        lifespan="on",
        reload=config.AUTORELOAD,
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
            f" {'--reload' if config.AUTORELOAD else ''}"
            f"{' -c ' + configuration if configuration else ''}"
            f" indexpy:app"
        )
        execute(command)
    elif method == "stop":
        execute("kill -TERM `cat .pid`")
    elif method == "reload":
        execute("kill -HUP `cat .pid`")


main.command(name="test", help="run test")(cmd_test)
main.command(name="check", help="check .py file in program")(cmd_check)

_import_module("commands")
