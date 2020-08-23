import os
import time
import signal
import logging
import subprocess
from typing import List, Union
from multiprocessing import cpu_count

import click

from .utils import import_module
from .config import here, LOG_LEVELS, Config


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

    return process.returncode


@click.group(help=f"Index.py {__version__}")
def main():
    # set index logger level
    indexpy_logger = logging.getLogger("indexpy")
    indexpy_logger.setLevel(LOG_LEVELS[config.LOG_LEVEL])


@main.command(help="use only uvicorn to deploy")
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


@main.command(help="use uvicorn to deploy by gunicorn")
@click.option("--workers", "-w", default=cpu_count())
@click.option("--daemon", "-d", default=False, is_flag=True)
@click.option(
    "--configuration",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument("method", type=click.Choice(["start", "stop", "reload"]))
@click.argument("application", default=lambda: config.APP)
def gunicorn(workers, daemon, configuration, method, application):
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


import_module("commands")
