from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from multiprocessing import cpu_count
from typing import List, Union

import click

from .__version__ import __version__
from .utils import F, import_module


def execute(command: Union[List[str], str]) -> int:
    if isinstance(command, str):
        command = command.split(" ")

    click.echo("Execute command: ", nl=False)
    click.secho(" ".join(command), fg="green")

    process = subprocess.Popen(command, shell=False)

    def sigint_handler(signo, frame):
        process.terminate()
        process.wait()

    signal.signal(signal.SIGINT, sigint_handler)

    while process.poll() is None:
        time.sleep(1)

    return process.returncode


@click.group(help=f"Index.py {__version__}")
def index_cli():
    pass


try:
    import uvicorn
except ImportError:
    pass
else:

    @click.command(help="use uvicorn to run Index.py application")
    @click.option("--bind", default="127.0.0.1:4190", show_default=True)
    @click.option("--autoreload/--no-autoreload", default=True, show_default=True)
    @click.option(
        "--log-level",
        type=click.Choice(["critical", "error", "warning", "info", "debug"]),
        default="info",
        show_default=True,
    )
    @click.argument("application")
    def uvicorn_cli(application: str, bind: str, autoreload: bool, log_level: str):
        sys.path.insert(0, os.getcwd())

        if bind.startswith("unix:"):
            unix_path = bind[5:]
            bind_config = {
                "uds": (
                    "/" + unix_path.lstrip("/")
                    if unix_path.startswith("/")
                    else unix_path
                )
                | F(os.path.normpath)
                | F(os.path.abspath)
            }
            if autoreload:
                click.secho(
                    "Reload option doesnt work with unix sockets "
                    "in uvicorn: https://github.com/encode/uvicorn/issues/722",
                    fg="yellow",
                )
        elif bind.startswith("fd://"):
            click.secho("Unsupport bind fd:// when using `index-cli uvicorn`", fg="red")
            raise SystemExit(1)
        else:
            if ":" in bind:
                host, port = bind.split(":")
                bind_config = {"host": host, "port": int(port)}
            else:
                bind_config = {"host": bind, "port": 4190}

        uvicorn.run(
            application,
            **bind_config,
            log_level=log_level,
            interface="asgi3",
            lifespan="on",
            reload=autoreload,
        )

    index_cli.add_command(uvicorn_cli, "uvicorn")

try:
    import gunicorn

    assert gunicorn.version_info > (20, 1)
    del gunicorn
except ImportError:
    pass
else:
    MASTER_PID_FILE = ".gunicorn.pid"

    def read_gunicorn_master_pid(pid_file: str = MASTER_PID_FILE) -> int:
        try:
            with open(os.path.join(os.getcwd(), pid_file), "r") as file:
                return int(file.read())
        except FileNotFoundError:
            sys.exit(
                (
                    f'File "{pid_file}" not found, '
                    + "please make sure you have started gunicorn using the "
                    + "`index-cli gunicorn start ...`."
                )
            )

    @click.group(help="use gunicorn to run Index.py application")
    def gunicorn_cli():
        pass

    @gunicorn_cli.command(help="Run gunicorn")
    @click.option("--bind", default="127.0.0.1:4190", show_default=True)
    @click.option("--autoreload/--no-autoreload", default=False, show_default=True)
    @click.option(
        "--log-level",
        type=click.Choice(["critical", "error", "warning", "info", "debug"]),
        default="info",
        show_default=True,
    )
    @click.option("--workers", "-w", default=cpu_count(), show_default=True)
    @click.option("--daemon", "-d", default=False, is_flag=True, show_default=True)
    @click.option(
        "--configuration",
        "-c",
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    @click.argument("application")
    def start(
        workers: int,
        daemon: bool,
        configuration: str,
        application: str,
        bind: str,
        autoreload: bool,
        log_level: str,
    ):
        command = (
            f"{sys.executable} -m gunicorn -k uvicorn.workers.UvicornWorker"
            + f" --bind {bind}"
            + f" --chdir {os.getcwd()}"
            + f" --workers {workers}"
            + f" --pid {MASTER_PID_FILE}"
            + f" --log-level {log_level}"
        )
        args = command.split(" ")
        if daemon:
            args.extend("-D --log-file run.log".split(" "))
        if autoreload:
            args.append("--reload")
        if configuration:
            args.append("-c")
            args.append(configuration.strip())
        args.append(application)

        execute(args)

    # Gunicorn signal handler
    # https://docs.gunicorn.org/en/stable/signals.html

    @gunicorn_cli.command(help="Increment the number of processes by one")
    def incr():
        os.kill(read_gunicorn_master_pid(), signal.SIGTTIN)

    @gunicorn_cli.command(help="Decrement the number of processes by one")
    def decr():
        os.kill(read_gunicorn_master_pid(), signal.SIGTTOU)

    @gunicorn_cli.command(help="Stop gunicorn processes")
    @click.option("--force", "-f", default=False, is_flag=True)
    def stop(force):
        os.kill(read_gunicorn_master_pid(), signal.SIGINT if force else signal.SIGTERM)

    @gunicorn_cli.command(help="Reload configuration and recreate worker processes")
    def reload():
        os.kill(read_gunicorn_master_pid(), signal.SIGHUP)

    @gunicorn_cli.command(help="Restart gunicorn master processes and worker processes")
    @click.option("--force-stop", "-f", default=False, is_flag=True)
    def restart(force_stop):
        oldpid = read_gunicorn_master_pid()

        os.kill(oldpid, signal.SIGUSR2)
        # Waiting for starting new master process and worker processes
        while not os.path.exists(os.path.join(os.getcwd(), MASTER_PID_FILE + ".2")):
            time.sleep(0.5)
        # Stop old master process and worker processes
        os.kill(oldpid, signal.SIGINT if force_stop else signal.SIGTERM)

    index_cli.add_command(gunicorn_cli, "gunicorn")

import_module("commands")
