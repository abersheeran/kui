import os
import signal
import subprocess
import sys
import time
from multiprocessing import cpu_count
from typing import List, Union

import click

from .__version__ import __version__
from .conf import serve_config
from .utils import import_module


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
    pass


@index_cli.command(help="use uvicorn to run Index.py application")
@click.argument("application", default=lambda: serve_config.APP)
def serve(application):
    import uvicorn

    uvicorn.run(
        application,
        host=serve_config.HOST,
        port=serve_config.PORT,
        log_level=serve_config.LOG_LEVEL,
        interface="asgi3",
        lifespan="on",
        reload=serve_config.AUTORELOAD,
    )


@click.group(help="use gunicorn to run Index.py application")
def gunicorn():
    pass


@gunicorn.command(help="Run gunicorn")
@click.option("--workers", "-w", default=cpu_count())
@click.option("--worker-class", "-k", default="uvicorn.workers.UvicornWorker")
@click.option("--daemon", "-d", default=False, is_flag=True)
@click.option(
    "--configuration",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.argument("application", default=lambda: serve_config.APP)
def start(workers, worker_class, daemon, configuration, application):
    from gunicorn.app.wsgiapp import run as run_gunicorn

    command = (
        "gunicorn"
        + f" -k {worker_class}"
        + f" --bind {serve_config.HOST}:{serve_config.PORT}"
        + f" --chdir {os.getcwd()}"
        + f" --workers {workers}"
        + f" --pid {os.path.join(os.getcwd(), '.pid')}"
        + f" --log-level {serve_config.LOG_LEVEL}"
    )
    args = command.split(" ")
    if daemon:
        args.extend("-D --log-file log.index".split(" "))
    if serve_config.AUTORELOAD:
        args.append("--reload")
    if configuration:
        args.append("-c")
        args.append(configuration.strip())
    args.append(application)

    sys.argv = args
    run_gunicorn()


@gunicorn.command(help="Stop daemon gunicorn processes")
def stop():
    execute(["kill -TERM", "`cat .pid`"])


@gunicorn.command(help="Reload daemon gunicorn processes")
def reload():
    execute(["kill -HUP", "`cat .pid`"])


index_cli.add_command(gunicorn, "gunicorn")

import_module("commands")
