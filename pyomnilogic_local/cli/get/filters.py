# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import FilterState, FilterType, FilterValvePosition, FilterWhyOn

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPFilter
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryType


@click.command()
@click.pass_context
def filters(ctx: click.Context) -> None:
    """List all filters and their current settings.

    Displays information about all filters including their system IDs, names,
    current state, speed, valve position, and power usage.

    Example:
        omnilogic get filters
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    filters_found = False

    # Check for filters in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.filter:
                for filt in bow.filter:
                    filters_found = True
                    _print_filter_info(filt, telemetry.get_telem_by_systemid(filt.system_id))

    if not filters_found:
        click.echo("No filters found in the system configuration.")


def _print_filter_info(filt: MSPFilter, telemetry: TelemetryType | None) -> None:
    """Format and print filter information in a nice table format.

    Args:
        filt: Filter object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("FILTER")
    click.echo("=" * 60)

    filter_data: dict[Any, Any] = {**dict(filt), **dict(telemetry)} if telemetry else dict(filt)
    for attr_name, value in filter_data.items():
        if attr_name == "state":
            value = FilterState(value).pretty()
        elif attr_name == "type":
            value = FilterType(value).pretty()
        elif attr_name == "valve_position":
            value = FilterValvePosition(value).pretty()
        elif attr_name == "why_on":
            value = FilterWhyOn(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
