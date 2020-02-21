import os
import sys

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)


def test_example():
    os.chdir(example)
    assert os.system(f"{sys.executable} -m indexpy only-print") == 0
    assert os.system(f"{sys.executable} -m indexpy test --throw") == 0

    assert os.path.exists(os.path.join(example, "index.startup"))
    os.remove(os.path.join(example, "index.startup"))
    assert os.path.exists(os.path.join(example, "index.shutdown"))
    os.remove(os.path.join(example, "index.shutdown"))
