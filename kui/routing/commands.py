from __future__ import annotations

import argparse
import inspect
import os
import sys
import typing

from ..utils import import_from_string
from ..utils.inspect import get_object_filepath, get_raw_handler
from .extensions.multimethod import is_multimethod_view


def display_urls() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "application", type=str, help="Application path like: module:attr"
    )
    args = parser.parse_args()
    application = args.application

    sys.path.insert(0, os.getcwd())
    app: typing.Any = import_from_string(application)
    for path, handler in app.router.http_tree.iterator():
        print("* ", end="")
        print(path, end="")
        print(" => ", end="")

        handler = get_raw_handler(handler)

        if is_multimethod_view(handler):
            print("Is multi-method Endpoint")
            for method in handler.__methods__:
                func = get_raw_handler(getattr(handler, method.lower()))
                filepath = get_object_filepath(func)
                whitespaces = " " * (len(path) + len("* ") + len(" => "))
                print(whitespaces + "| " + method + " => ", end="")
                print(filepath + ":" + str(func.__code__.co_firstlineno))
        else:
            filepath = get_object_filepath(handler)
            print(filepath + ":" + str(inspect.getsourcelines(handler)[1]))
