import os
import sys
import typing
from pathlib import Path

import click

from ..utils import get_raw_handler, import_from_string

if typing.TYPE_CHECKING:
    from indexpy import Index


@click.command(help="display all urls in application")
@click.argument("application")
def display_urls(application):
    sys.path.insert(0, os.getcwd())
    index_app: Index = import_from_string(application)
    for path, handler in index_app.router.http_tree.iterator():
        click.secho("* ", nl=False)
        click.secho(path, fg="green", nl=False)
        click.secho(" => ", nl=False)

        handler = get_raw_handler(handler)

        try:
            filepath = (
                "./"
                + Path(handler.__code__.co_filename).relative_to(Path.cwd()).as_posix()
            )
        except ValueError:
            filepath = handler.__code__.co_filename

        click.secho(filepath + ":" + str(handler.__code__.co_firstlineno), fg="blue")
