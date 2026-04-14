"""Utility functions for CLI operations.

This module provides helper functions for CLI commands, primarily for
accessing controller data within the Click context.
"""

from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING, Literal, overload

import click

from pyomnilogic_local.api.api import OmniLogicAPI

if TYPE_CHECKING:
    from pyomnilogic_local.models.filter_diagnostics import FilterDiagnostics


async def get_omni(host: str) -> OmniLogicAPI:
    """Create an OmniLogicAPI instance for the specified controller.

    Args:
        host: Hostname or IP address of the OmniLogic controller

    Returns:
        Configured OmniLogicAPI instance ready for communication
    """
    sim_data_path = os.environ.get("PYOMNILOGIC_SIMULATION_DATA")
    if sim_data_path:
        from pyomnilogic_local.api.mock_api import OmniLogicMockAPI

        return OmniLogicMockAPI(sim_data_path)  # type: ignore[return-value]
    return OmniLogicAPI(host, 10444, 5.0)


@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[True]) -> str: ...
@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[False]) -> FilterDiagnostics: ...
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: bool) -> FilterDiagnostics | str:
    """Retrieve filter diagnostics from the controller.

    Args:
        omni: OmniLogicAPI instance for controller communication
        pool_id: System ID of the Body Of Water
        filter_id: System ID of the filter/pump
        raw: If True, return raw XML string; if False, return parsed FilterDiagnostics object

    Returns:
        FilterDiagnostics object or raw XML string depending on raw parameter
    """
    return await omni.async_get_filter_diagnostics(pool_id, filter_id, raw=raw)


def echo_properties(obj):
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
