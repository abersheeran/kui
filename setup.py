#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command


here = os.path.abspath(os.path.dirname(__file__))


def get_version(package) -> str:
    """
    Return version.
    """
    __: dict = {}
    with open(os.path.join(here, package, "__version__.py")) as f:
        exec(f.read(), __)

    return __["__version__"]


def get_long_description():
    """
    Return the README.
    """
    return open("README.md", "r", encoding="utf8").read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options: list = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s), flush=True)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status("Removing previous builds…")
        rmtree(os.path.join(here, "dist"), ignore_errors=True)
        rmtree(os.path.join(here, "build"), ignore_errors=True)

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(get_version("index")))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name="index.py",
    version=get_version("index"),
    description="An easy-to-use asynchronous web framework based on ASGI.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Aber Sheeran",
    author_email="abersheeran@qq.com",
    python_requires=">=3.6.0",
    url="https://github.com/abersheeran/index.py",
    packages=get_packages("index"),
    entry_points={"console_scripts": ["index-cli=index.cli:main"],},
    install_requires=[
        "gunicorn",
        "uvicorn",
        "starlette",
        "requests",  # test client
        "aiofiles",  # file response
        "jinja2",  # template
        "watchdog",  # autoreload
        "python-multipart",  # form parse
        "pyyaml",  # yaml response
        "pydantic",  # openapi
        'contextvars ;python_version<"3.7"',
    ],
    license="Apache 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    # $ setup.py publish support.
    cmdclass={"upload": UploadCommand},
)
