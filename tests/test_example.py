import os
import sys
import traceback

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)


def test_example():
    os.chdir(example)
    assert os.system(f"{sys.executable} -m index test --throw") == 0
