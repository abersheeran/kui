from __future__ import annotations

import inspect
import os
import sys
import typing

import click

from ..utils import import_from_string
from ..utils.inspect import get_object_filepath, get_raw_handler
from .extensions.multimethod import is_multimethod_view


@click.command(help="display all urls in application")
@click.argument("application")
def display_urls(application):
    sys.path.insert(0, os.getcwd())
    app: typing.Any = import_from_string(application)
    for path, handler in app.router.http_tree.iterator():
        click.secho("* ", nl=False)
        click.secho(path, fg="green", nl=False)
        click.secho(" => ", nl=False)

        handler = get_raw_handler(handler)

        if is_multimethod_view(handler):
            click.secho("Is multi-method Endpoint")
            for method in handler.__methods__:
                func = get_raw_handler(getattr(handler, method.lower()))
                filepath = get_object_filepath(func)
                whitespaces = " " * (len(path) + len("* ") + len(" => "))
                click.secho(whitespaces + "| " + method + " => ", nl=False)
                click.secho(
                    filepath + ":" + str(func.__code__.co_firstlineno), fg="blue"
                )
        else:
            filepath = get_object_filepath(handler)
            click.secho(
                filepath + ":" + str(inspect.getsourcelines(handler)[1]), fg="blue"
            )
