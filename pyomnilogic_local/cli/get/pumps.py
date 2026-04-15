# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.cli.utils import echo_properties
from pyomnilogic_local.omnitypes import PumpFunction, PumpState, PumpType

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic
    from pyomnilogic_local.models.mspconfig import MSPPump
    from pyomnilogic_local.models.telemetry import TelemetryType


@click.command()
@click.pass_context
def pumps(ctx: click.Context) -> None:
    """List all pumps and their current settings.

    Displays information about all pumps including their system IDs, names,
    current state, speed settings, and pump type.

    Example:
        omnilogic get pumps
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]
    all_pumps = omnilogic.all_pumps
    for pump in all_pumps:
        echo_properties(pump)

    if len(all_pumps) == 0:
        click.echo("No pumps found in the system configuration.")


def _print_pump_info(pump: MSPPump, telemetry: TelemetryType | None) -> None:
    """Format and print pump information in a nice table format.

    Args:
        pump: Pump object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("PUMP")
    click.echo("=" * 60)

    pump_data: dict[Any, Any] = {**dict(pump), **dict(telemetry)} if telemetry else dict(pump)
    for attr_name, value in pump_data.items():
        if attr_name == "state":
            value = PumpState(value).pretty()
        elif attr_name == "equip_type":
            value = PumpType(value).pretty()
        elif attr_name == "function":
            value = PumpFunction(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
