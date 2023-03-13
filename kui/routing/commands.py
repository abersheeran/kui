from __future__ import annotations

import argparse
import inspect
import os
import sys
import typing
from fnmatch import fnmatchcase

from ..utils import F, import_from_string
from ..utils.inspect import get_object_filepath, get_raw_handler
from .routers import Router


def main(argv: typing.Sequence[str] = sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "application", type=str, help="application path like: module:attr"
    )
    parser.add_argument(
        "--match",
        type=str,
        help="match path by unix filename pattern matching",
    )
    parser.add_argument(
        "--not-match",
        type=str,
        help="only display no matched path by unix filename pattern matching",
    )
    args = parser.parse_args(argv)

    match_func_list = []
    if args.match is not None:
        match_func_list.append(lambda p, h: fnmatchcase(p, args.match))
    if args.not_match is not None:
        match_func_list.append(lambda p, h: not fnmatchcase(p, args.not_match))

    sys.path.insert(0, os.getcwd())
    display_urls(import_from_string(args.application).router, match_func_list)


def display_urls(
    router: Router,
    match_func_list: typing.Iterable[typing.Callable[[str, typing.Any], bool]],
) -> None:
    filter_path = F(
        filter, lambda p_h: match_func_list | F(map, lambda f: f(*p_h)) | F(all)
    )

    for path, handler in router.http_tree.iterator() | filter_path:
        raw_handler = get_raw_handler(handler)

        if hasattr(handler, "__methods__"):
            for method in raw_handler.__methods__:
                func = get_raw_handler(getattr(raw_handler, method.lower()))
                print_url(
                    method,
                    path,
                    get_object_filepath(func),
                    func.__code__.co_firstlineno,
                )
        else:
            print_url(
                getattr(handler, "__method__", "ANY"),
                path,
                get_object_filepath(raw_handler),
                inspect.getsourcelines(raw_handler)[1],
            )


def print_url(method: str, path: str, filepath: str, lineno: int) -> None:
    print(f"{method:<7} {path} => {filepath}:{lineno}")
