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
    sys.exit(execute(command))


if __name__ == "__main__":
    shell("pytest -o log_cli=true -o log_cli_level=DEBUG")
    shell("cd example")
    shell("index-cli test -app example:app")
