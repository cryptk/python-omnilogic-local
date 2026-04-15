# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.cli.utils import echo_properties
from pyomnilogic_local.omnitypes import SensorType, SensorUnits

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic
    from pyomnilogic_local.models.mspconfig import MSPSensor


@click.command()
@click.pass_context
def sensors(ctx: click.Context) -> None:
    """List all sensors and their current settings.

    Displays information about all sensors including their system IDs, names,
    sensor type, and units.

    Example:
        omnilogic get sensors
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]
    all_sensors = omnilogic.all_sensors
    for sensor in all_sensors:
        echo_properties(sensor)

    if len(all_sensors) == 0:
        click.echo("No sensors found in the system configuration.")


def _print_sensor_info(sensor: MSPSensor) -> None:
    """Format and print sensor information in a nice table format.

    Args:
        sensor: Sensor object from MSPConfig with attributes to display
    """
    click.echo("\n" + "=" * 60)
    click.echo("SENSOR")
    click.echo("=" * 60)

    sensor_data: dict[Any, Any] = dict(sensor)
    for attr_name, value in sensor_data.items():
        if attr_name == "equip_type":
            value = str(SensorType(value))
        elif attr_name == "units":
            value = str(SensorUnits(value))
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
