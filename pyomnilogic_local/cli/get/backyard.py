# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import BackyardState

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPBackyard, MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryType


@click.command()
@click.pass_context
def backyard(ctx: click.Context) -> None:
    """Display backyard-level information and equipment summary.

    Shows overall backyard status including air temperature, system state,
    configuration checksum, MSP firmware version, and a summary of all
    installed equipment.

    Example:
        omnilogic get backyard
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    _print_backyard_info(mspconfig.backyard, telemetry.get_telem_by_systemid(mspconfig.backyard.system_id))


def _print_backyard_info(backyardconfig: MSPBackyard, telemetry: TelemetryType | None) -> None:
    """Format and print backyard information in a nice table format.

    Args:
        backyardconfig: Backyard object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("BACKYARD")
    click.echo("=" * 60)

    # Combine config and telemetry data
    backyard_data: dict[Any, Any] = {**dict(backyardconfig), **dict(telemetry)} if telemetry else dict(backyardconfig)

    # Fields to exclude from main display (we'll show equipment counts instead)
    exclude_fields = {"sensor", "bow", "colorlogic_light", "relay"}

    for attr_name, value in backyard_data.items():
        if attr_name in exclude_fields:
            continue

        if attr_name == "state":
            value = BackyardState(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")

    # Show equipment summary
    click.echo("\nAttached Equipment:")
    click.echo("-" * 60)

    equipment_counts = []

    if backyardconfig.bow:
        equipment_counts.append(f"Bodies of Water: {len(backyardconfig.bow)}")
        equipment_counts.extend(f"  - {bow.name} ({bow.equip_type})" for bow in backyardconfig.bow)

    if backyardconfig.sensor:
        equipment_counts.append(f"Backyard Sensors: {len(backyardconfig.sensor)}")

    if backyardconfig.colorlogic_light:
        equipment_counts.append(f"Backyard ColorLogic Lights: {len(backyardconfig.colorlogic_light)}")

    if backyardconfig.relay:
        equipment_counts.append(f"Backyard Relays: {len(backyardconfig.relay)}")

    if equipment_counts:
        for count in equipment_counts:
            click.echo(f"  {count}")
    else:
        click.echo("  None")

    click.echo("=" * 60)
