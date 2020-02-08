import os
import sys

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)


def test_example():
    os.chdir(example)
    assert os.system(f"{sys.executable} -m index only-print") == 0
    assert os.system(f"{sys.executable} -m index test --throw") == 0
