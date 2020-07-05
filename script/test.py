import os
import sys
import time
import signal
import subprocess


def execute(*commands):
    process = subprocess.Popen(" ".join(commands), cwd=os.getcwd(), shell=True)

    def sigterm_handler(signo, frame):
        process.terminate()
        process.wait()

    signal.signal(signal.SIGTERM, sigterm_handler)

    while process.poll() is None:
        time.sleep(1)
    return process.poll()


def shell(command: str) -> None:
    exit_code = execute(command)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    shell("pytest -o log_cli=true -o log_cli_level=DEBUG")
    os.chdir("example")
    shell("index-cli test -app example:app")
