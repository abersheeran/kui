import os

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)
os.chdir(example)
