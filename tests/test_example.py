import os
import sys
import time
import subprocess

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)


def test_example():
    os.chdir(example)
    assert os.system(f"{sys.executable} -m indexpy only-print") == 0
    assert os.system(f"{sys.executable} -m indexpy test --throw") == 0


def test_gunicorn():
    if sys.platform != "linux":
        return
    os.chdir(example)
    process = subprocess.Popen(
        f"{sys.executable} -m indexpy gunicorn start -w 1", shell=True, cwd=example
    )
    time.sleep(3)  # wait application startup
    process.terminate()
    while process.poll() is None:
        time.sleep(1)
    for _ in range(5):
        if process.poll() < 0:
            time.sleep(1)
    assert process.wait() == 0
