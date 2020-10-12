import logging
import os
import signal
import subprocess
import sys
import time
from multiprocessing import cpu_count
from typing import List, Union

import click

from .__version__ import __version__
from .config import LOG_LEVELS, Config, here
from .utils import import_module

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

    return process.returncode


@click.group(help=f"Index.py {__version__}")
def index_cli():
    # set index logger level
    indexpy_logger = logging.getLogger("indexpy")
    indexpy_logger.setLevel(LOG_LEVELS[config.LOG_LEVEL])


@index_cli.command(help="use uvicorn to run Index.py")
@click.argument("application", default=lambda: config.APP)
def serve(application):
    import uvicorn

    uvicorn.run(
        application,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        interface="asgi3",
        lifespan="on",
        reload=config.AUTORELOAD,
    )


@click.group(help="use gunicorn to run Index.py")
def gunicorn():
    pass


@gunicorn.command()
@click.option("--workers", "-w", default=cpu_count())
@click.option("--worker-class", "-k", default="uvicorn.workers.UvicornWorker")
@click.option("--daemon", "-d", default=False, is_flag=True)
@click.option(
    "--configuration",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument("application", default=lambda: config.APP)
def start(workers, worker_class, daemon, configuration, application):
    from gunicorn.app.wsgiapp import run

    command = (
        "gunicorn"
        + f" -k {worker_class}"
        + f" --bind {config.HOST}:{config.PORT}"
        + f" --chdir {here}"
        + f" --workers {workers}"
        + f" --pid {os.path.join(here, '.pid')}"
        + f" --log-level {config.LOG_LEVEL}"
    )
    args = command.split(" ")
    if daemon:
        args.extend("-D --log-file log.index".split(" "))
    if config.AUTORELOAD:
        args.append("--reload")
    if configuration:
        args.append("-c")
        args.append(configuration.strip())
    args.append(application)

    sys.argv = args
    run()


@gunicorn.command("")
def stop():
    execute(["kill -TERM", "`cat .pid`"])


@gunicorn.command()
def reload():
    execute(["kill -HUP", "`cat .pid`"])


index_cli.add_command(gunicorn, "gunicorn")

import_module("commands")
