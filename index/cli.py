import os
import re
import sys
import logging
import subprocess
from multiprocessing import cpu_count

import click
import uvicorn

from . import app, Config
from .config import LOG_LEVELS

config = Config()
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOG_LEVELS[config.log_level]
)


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
        logger=logging.getLogger("index"),
        debug=config.DEBUG,
        lifespan="on"
    )


@main.command(help="deploy by gunicorn")
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
