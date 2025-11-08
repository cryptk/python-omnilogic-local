# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click

from pyomnilogic_local.omnitypes import ColorLogicBrightness, ColorLogicPowerState, ColorLogicSpeed

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPColorLogicLight, MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryColorLogicLight


@click.command()
@click.pass_context
def lights(ctx: click.Context) -> None:
    """List all ColorLogic lights and their current settings.

    Displays information about all lights including their system IDs, names,
    current state, and available light shows.

    Example:
        omnilogic get lights
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    lights_found = False

    # Check for lights in the backyard
    if mspconfig.backyard.colorlogic_light:
        for light in mspconfig.backyard.colorlogic_light:
            lights_found = True
            _print_light_info(light, cast("TelemetryColorLogicLight", telemetry.get_telem_by_systemid(light.system_id)))

    # Check for lights in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.colorlogic_light:
                for cl_light in bow.colorlogic_light:
                    lights_found = True
                    _print_light_info(cl_light, cast("TelemetryColorLogicLight", telemetry.get_telem_by_systemid(cl_light.system_id)))

    if not lights_found:
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
            value = ColorLogicBrightness(value).pretty()
        elif attr_name == "effects" and isinstance(value, list):
            show_names = [show.pretty() if hasattr(show, "pretty") else str(show) for show in value]
            value = ", ".join(show_names) if show_names else "None"
        elif attr_name == "show" and value is not None:
            value = telemetry.show_name(light.equip_type, light.v2_active) if telemetry else str(value)
        elif attr_name == "speed":
            value = ColorLogicSpeed(value).pretty()
        elif attr_name == "state":
            value = ColorLogicPowerState(value).pretty()
        elif isinstance(value, list):
            # Format other lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
