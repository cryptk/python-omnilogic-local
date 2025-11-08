# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import BodyOfWaterType

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPBoW, MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryType


@click.command()
@click.pass_context
def bows(ctx: click.Context) -> None:
    """List all Bodies of Water (BOWs) and their current status.

    Displays information about all bodies of water including their system IDs,
    names, types (pool/spa), water temperature, flow status, and attached equipment.

    Example:
        omnilogic get bows
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    bows_found = False

    # Check for BOWs in the backyard
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            bows_found = True
            _print_bow_info(bow, telemetry.get_telem_by_systemid(bow.system_id))

    if not bows_found:
        click.echo("No Bodies of Water found in the system configuration.")


def _print_bow_info(bow: MSPBoW, telemetry: TelemetryType | None) -> None:
    """Format and print Body of Water information in a nice table format.

    Args:
        bow: BOW object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("BODY OF WATER")
    click.echo("=" * 60)

    # Combine config and telemetry data
    bow_data: dict[Any, Any] = {**dict(bow), **dict(telemetry)} if telemetry else dict(bow)

    # Fields to exclude from main display (we'll show equipment counts instead)
    exclude_fields = {"filter", "relay", "heater", "sensor", "colorlogic_light", "pump", "chlorinator", "csad"}

    for attr_name, value in bow_data.items():
        if attr_name in exclude_fields:
            continue

        if attr_name == "type":
            value = BodyOfWaterType(value).pretty()
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
    if bow.filter:
        equipment_counts.append(f"Filters: {len(bow.filter)}")
    if bow.pump:
        equipment_counts.append(f"Pumps: {len(bow.pump)}")
    if bow.heater:
        equipment_counts.append("Heater: 1 (virtual)")
        if bow.heater.heater_equipment:
            equipment_counts.append(f"  - Physical Heaters: {len(bow.heater.heater_equipment)}")
    if bow.sensor:
        equipment_counts.append(f"Sensors: {len(bow.sensor)}")
    if bow.colorlogic_light:
        equipment_counts.append(f"ColorLogic Lights: {len(bow.colorlogic_light)}")
    if bow.relay:
        equipment_counts.append(f"Relays: {len(bow.relay)}")
    if bow.chlorinator:
        equipment_counts.append("Chlorinator: 1")
    if bow.csad:
        equipment_counts.append(f"CSADs: {len(bow.csad)}")

    if equipment_counts:
        for count in equipment_counts:
            click.echo(f"  {count}")
    else:
        click.echo("  None")

    click.echo("=" * 60)
