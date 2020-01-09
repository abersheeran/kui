import os
import sys
import time
import signal
import logging
import traceback
import subprocess
from multiprocessing import cpu_count

import click
import uvicorn

from .applications import Filepath
from .config import LOG_LEVELS, config, logger
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

    process = subprocess.Popen(command, shell=True)

    def sigterm_handler(signo, frame):
        process.terminate()
        process.wait()

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    while process.poll() is None:
        time.sleep(1)


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
@click.option("--env", default="test")
@click.argument("uri", default="--all")
def test(env, uri):
    # change config env
    config["env"] = env
    # define custom printf
    printf = lambda *args, **kwargs: click.secho(*args, **kwargs)

    def test_path(view, _uri):
        for func in view.Test(app, _uri).all_test:
            printf(f" - {func.__name__} ", nl=False)
            try:
                func()
                printf("√", fg="green")
            except:
                printf("×", fg="red")
                traceback.print_exc()

    if uri == "--all":
        for view, _uri in Filepath.get_views():
            printf(f"{_uri}", fg="blue")
            if not hasattr(view, "Test"):
                printf(f" - No test.", fg="yellow")
                continue
            test_path(view, _uri)
    else:
        printf(f"{uri}", fg="blue")
        test_path(Filepath.get_view(uri), uri)


@main.command(help="check .py files in program")
def check():
    for root, dirs, files in os.walk(config.path):
        for file in files:
            if not file.endswith(".py"):
                continue
            abspath = os.path.join(root, file).replace("\\", "/")
            module = _import(abspath, nosleep=True)
