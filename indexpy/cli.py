import os
import sys
import time
import signal
import logging
import importlib
import subprocess
from typing import List, Union
from multiprocessing import cpu_count

import click
import uvicorn

from .utils import _import_module
from .config import here, LOG_LEVELS, Config
from .applications import Index
from .test import cmd_test
from .autoreload import cmd_check
from .__version__ import __version__


config = Config()


def execute(command: Union[List[str], str]) -> int:
    if isinstance(command, str):
        command = [command]

    click.echo("Execute command: ", nl=False)
    click.secho(" ".join(command), fg="green")

    process = subprocess.Popen(" ".join(command), shell=True)

    def sigterm_handler(signo, frame):
        process.terminate()
        process.wait()

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    while process.poll() is None:
        time.sleep(1)

    return process.poll()


@click.group(help=f"Index.py {__version__}")
@click.option("--env", default=config.ENV, help="set config.ENV")
@click.option("--debug/--no-debug", default=config.DEBUG, help="set config.DEBUG")
def main(env, debug):
    # change config
    os.environ["INDEX_ENV"] = env
    os.environ["INDEX_DEBUG"] = "on" if debug else "off"
    config.import_from_environ()
    Index().rebuild_app()
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
@click.option(
    "--configuration",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument("method", type=click.Choice(["start", "stop", "reload"]))
@click.argument("application", default="indexpy:app")
def gunicorn(workers, daemon, configuration, method, application):
    if sys.platform in ("win32", "cygwin", "msys"):
        raise RuntimeError("gunicorn can't run on windows system.")

    if method == "start":
        command = [
            "gunicorn -k uvicorn.workers.UvicornWorker",
            f"--bind {config.HOST}:{config.PORT}",
            f"--chdir {here}",
            f"--workers {workers}",
            f"--pid {os.path.join(here, '.pid')}",
            f"--log-level {config.LOG_LEVEL}",
        ]
        if daemon:
            command.append("-D --log-file log.index")
        if config.AUTORELOAD:
            command.append("--reload")
        if configuration:
            command.append("-c " + configuration)
        command.append(application)

        execute(command)
    elif method == "stop":
        execute(["kill -TERM", "`cat .pid`"])
    elif method == "reload":
        execute(["kill -HUP", "`cat .pid`"])


main.command(name="test", help="run test")(cmd_test)
main.command(name="check", help="check .py file in program")(cmd_check)

_import_module("commands")
