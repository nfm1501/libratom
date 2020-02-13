# pylint: disable=unused-argument,too-few-public-methods,arguments-differ
"""
Command-line interface utilities
"""

import json
import re
from contextlib import AbstractContextManager
from pathlib import Path

import click
import pkg_resources
import requests
from pkg_resources import DistributionNotFound
from tabulate import tabulate


class PathPath(click.Path):
    """
    A Click path argument that returns a pathlib Path, not a string

    https://github.com/pallets/click/issues/405#issuecomment-470812067
    """

    def convert(self, value, param, ctx):
        return Path(super().convert(value, param, ctx))


class MockContext(AbstractContextManager):
    """
    A no-op context manager for use in python 3.6 and newer
    It accepts an arbitrary number of keyword arguments and returns an object whose attributes are all None

    Modified from https://github.com/python/cpython/blob/v3.7.4/Lib/contextlib.py#L685-L703
    """

    def __init__(self, **__):
        pass

    def __getattribute__(self, item):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        pass


def validate_out_path(ctx, param, value: Path) -> Path:
    """
    Callback for click commands that checks that an output file doesn't already exist
    """

    if value.is_file():
        raise click.BadParameter(f'File "{value}" already exists.')

    return value


def validate_version_string(ctx, param, value: str) -> str:
    """
    Callback for click commands that checks that version string is valid
    """

    version_pattern = re.compile(r"\d+(?:\.\d+)+")

    if not version_pattern.match(value):
        raise click.BadParameter(value)

    return value


def list_spacy_models(model_name: str = None) -> int:

    response = requests.get(
        url="https://api.github.com/repos/explosion/spacy-models/releases"
    )

    if not response.ok:
        return -1

    releases = json.loads(response.content)

    if model_name:
        releases = [
            release["name"].split("-")
            for release in releases
            if release["name"].startswith(model_name)
        ]
    else:
        releases = [release["name"].split("-") for release in releases]

    # sort by name
    releases.sort(key=lambda x: x[0])

    table = [["spaCy model", "installed version", "latest version"]]

    for name, version in releases:

        # See if we have an installed version
        try:
            installed_model_version = pkg_resources.get_distribution(name).version
        except DistributionNotFound:
            installed_model_version = None

        table.append([name, installed_model_version, version])

    print(tabulate(table, headers="firstrow"))

    return 0
