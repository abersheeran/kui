import os
import re
import sys
import subprocess

import click
import uvicorn

from . import app, Config
from .config import logger

config = Config()


def execute(command: str):
    click.echo("Execute command: ", nl=False)
    click.secho(command, fg="green")
    os.system(command)


@click.group()
def main():
    pass


@main.command(help='use only uvicorn')
def dev():
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        debug=config.DEBUG,
        logger=logger
    )


@main.command(help="deploy by gunicorn")
@click.option("--workers", "-w", default=1)
@click.option("--daemon", "-d", default=False, is_flag=True)
@click.argument("method")
def gunicorn(workers, daemon, method):
    if sys.platform != "linux":
        raise RuntimeError("gunicorn can only run on Linux.")
    if method == "start":
        command = (
            f"gunicorn -k uvicorn.workers.UvicornWorker"
            f" --bind {config.HOST}:{config.PORT}"
            f" --chdir {config.path}"
            f" --pid {os.path.join(config.path, '.pid')}"
            f" --log-level {config.LOG_LEVEL}"
            f" {'-D --log-file log.index' if daemon else ''}"
            f" -w {workers}"
            f" index:app"
        )
        execute(command)
    elif method == "stop":
        execute("kill -TERM `cat .pid`")
