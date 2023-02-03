import os
import subprocess

here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_version(package) -> str:
    """
    Return version.
    """
    __: dict = {}
    with open(os.path.join(here, package, "__version__.py")) as f:
        exec(f.read(), __)

    return __["__version__"]


os.chdir(here)
subprocess.check_call(f"pdm version {get_version('kui')}", shell=True)
subprocess.check_call("git add kui/__version__.py pyproject.toml", shell=True)
subprocess.check_call(f'git commit -m "{get_version("kui")}"', shell=True)
subprocess.check_call("git push", shell=True)
subprocess.check_call("git tag v{0}".format(get_version("kui")), shell=True)
subprocess.check_call("git push --tags", shell=True)
