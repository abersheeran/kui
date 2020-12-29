import os
import signal
import subprocess
import sys
import time
from multiprocessing import cpu_count
from typing import List, Union

import click

from .__version__ import __version__
from .conf import serve_config, ConfigError
from .utils import import_module


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
    @click.argument("application", default=lambda: serve_config.APP)
    def uvicorn_cli(application):
        sys.path.insert(0, os.getcwd())

        if serve_config.BIND.startswith("unix:"):
            unix_path = serve_config.BIND[5:]
            bind_config = {
                "uds": os.path.abspath(
                    os.path.normpath(
                        "/" + unix_path.lstrip("/")
                        if unix_path.startswith("/")
                        else unix_path
                    )
                )
            }
            if serve_config.AUTORELOAD:
                click.secho(
                    "Reload option doesnt work with unix sockets in uvicorn: https://github.com/encode/uvicorn/issues/722",
                    fg="yellow",
                )
        elif serve_config.BIND.startswith("fd://"):
            raise ConfigError("Unsupport bind fd:// when using `index-cli uvicorn`")
        else:
            if ":" in serve_config.BIND:
                host, port = serve_config.BIND.split(":")
                bind_config = {"host": host, "port": int(port)}
            else:
                bind_config = {"host": serve_config.BIND}

        uvicorn.run(
            application,
            **bind_config,
            log_level=serve_config.LOG_LEVEL,
            interface="asgi3",
            lifespan="on",
            reload=serve_config.AUTORELOAD,
        )

    index_cli.add_command(uvicorn_cli, "uvicorn")

try:
    import gunicorn
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
                    + "`index-cli gunicorn start --daemon ...`."
                )
            )

    @click.group(help="use gunicorn to run Index.py application")
    def gunicorn_cli():
        pass

    @gunicorn_cli.command(help="Run gunicorn")
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
        command = (
            "gunicorn"
            + f" -k {worker_class}"
            + f" --bind {serve_config.BIND}"
            + f" --chdir {os.getcwd()}"
            + f" --workers {workers}"
            + f" --pid {MASTER_PID_FILE}"
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
