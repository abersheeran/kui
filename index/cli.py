import os
import sys
import time
import signal
import logging
import subprocess
from multiprocessing import cpu_count

import click
import uvicorn

from .config import LOG_LEVELS, config
from .autoreload import _import
from .__version__ import __version__

from . import app

logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=LOG_LEVELS[config.log_level],
)


def execute(command: str):
    click.echo("Execute command: ", nl=False)
    click.secho(command, fg="green")
    os.system(command)


@click.group(help=f"Index.py {__version__}")
def main():
    pass


@main.command(help="use only uvicorn to deploy")
def serve():
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        # logger=logging.getLogger("index"),
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


@main.command(help="run gunicorn in docker")
@click.option("--workers", "-w", default=2)
@click.option("--configuration", "-c")
def docker(workers, configuration):
    command = (
        f"gunicorn -k uvicorn.workers.UvicornWorker"
        f" --bind {config.HOST}:{config.PORT}"
        f" --chdir {config.path}"
        f" --log-level {config.LOG_LEVEL}"
        f" -w {workers}"
        f"{' -c ' + configuration if configuration else ''}"
        f" index:app"
    )
    process = subprocess.Popen(command, shell=True)

    def sigterm_handler(signo, frame):
        process.terminate()
        process.wait()
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    while process.poll() is None:
        time.sleep(3.1)


@main.command(help="check .py files in program")
def check():
    views_path = os.path.join(config.path, "views/").replace("\\", "/")
    for root, dirs, files in os.walk(config.path):
        for file in files:
            if not file.endswith(".py"):
                continue
            abspath = os.path.join(root, file).replace("\\", "/")
            module = _import(abspath, nosleep=True)
            if abspath.startswith(views_path) and not abspath.endswith("__init__.py"):
                if not (hasattr(module, "HTTP") or hasattr(module, "Socket")):
                    print(f"- {module} must have HTTP or Socket")
