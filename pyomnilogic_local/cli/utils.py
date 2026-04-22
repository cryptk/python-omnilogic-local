"""Utility functions for CLI operations.

This module provides helper functions for CLI commands, primarily for
accessing controller data within the Click context.
"""

from __future__ import annotations

import inspect
from typing import Any

import click


def echo_properties(obj: Any) -> None:
    """Echo all properties of an object in a formatted way."""
    # 1. Identify the properties from the class
    prop_names = [name for name, value in inspect.getmembers(type(obj), lambda x: isinstance(x, property))]
    longest_name = max(prop_names, key=len, default="")
    name_length = len(click.style(longest_name, fg="green"))  # Get the length including the ANSI color codes
    name_column_width = name_length + 2  # Add some padding

    if not prop_names:
        click.echo(click.style("No properties found.", fg="yellow"))
        return

    click.echo("\n" + "=" * 60)
    click.echo(click.style(f"Instance of {type(obj).__name__}:", fg="cyan", bold=True))
    click.echo("=" * 60)

    # 2. Iterate and echo with formatting
    for name in sorted(prop_names):
        if name in ("_api"):  # Skip internal properties that are not relevant to display
            continue
        try:
            value = getattr(obj, name)
            # Label in green, value in default/white
            click.echo(f"  {click.style(name, fg='green'):{name_column_width}}: {value}")
        except Exception as e:
            # Handle cases where the property might fail
            click.echo(f"  {click.style(name, fg='red')}: Error ({e})")
