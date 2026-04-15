# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.cli.utils import echo_properties
from pyomnilogic_local.omnitypes import ColorLogicBrightness, ColorLogicPowerState, ColorLogicSpeed

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic
    from pyomnilogic_local.models.mspconfig import MSPColorLogicLight
    from pyomnilogic_local.models.telemetry import TelemetryColorLogicLight


@click.command()
@click.pass_context
def lights(ctx: click.Context) -> None:
    """List all ColorLogic lights and their current settings.

    Displays information about all lights including their system IDs, names,
    current state, and available light shows.

    Example:
        omnilogic get lights
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]
    all_lights = omnilogic.all_lights
    for light in all_lights:
        echo_properties(light)

    if len(all_lights) == 0:
        click.echo("No ColorLogic lights found in the system configuration.")


def _print_light_info(light: MSPColorLogicLight, telemetry: TelemetryColorLogicLight | None) -> None:
    """Format and print light information in a nice table format.

    Args:
        light: Light object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("LIGHT")
    click.echo("=" * 60)

    light_data: dict[Any, Any] = {**dict(light), **dict(telemetry)} if telemetry else dict(light)

    for attr_name, value in light_data.items():
        if attr_name == "brightness":
            value = str(ColorLogicBrightness(value))
        elif attr_name == "effects" and isinstance(value, list):
            show_names = [str(show) for show in value]
            value = ", ".join(show_names) if show_names else "None"
        elif attr_name == "show" and value is not None:
            value = telemetry.show_name(light.equip_type, light.v2_active) if telemetry else str(value)
        elif attr_name == "speed":
            value = str(ColorLogicSpeed(value))
        elif attr_name == "state":
            value = str(ColorLogicPowerState(value))
        elif isinstance(value, list):
            # Format other lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
