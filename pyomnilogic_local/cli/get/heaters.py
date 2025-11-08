# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import HeaterMode, HeaterState, HeaterType

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPHeaterEquip, MSPVirtualHeater
    from pyomnilogic_local.models.telemetry import Telemetry


@click.command()
@click.pass_context
def heaters(ctx: click.Context) -> None:
    """List all heaters and their current settings.

    Displays information about virtual heaters and their associated physical
    heater equipment including system IDs, names, types, current state,
    temperature settings, and operational status.

    Each Body of Water has a single virtual heater that may control multiple
    physical heater units (gas, heat pump, solar, etc.).

    Example:
        omnilogic get heaters
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    heaters_found = False

    # Check for heaters in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.heater:
                heaters_found = True
                _print_virtual_heater_info(bow.heater, telemetry)

    if not heaters_found:
        click.echo("No heaters found in the system configuration.")


def _print_virtual_heater_info(virt_heater: MSPVirtualHeater, telemetry: Telemetry) -> None:
    """Format and print virtual heater information in a nice table format.

    Args:
        virt_heater: Virtual heater object from MSPConfig with attributes to display
        telemetry: Telemetry object containing all telemetry data
    """
    click.echo("\n" + "=" * 60)
    click.echo("VIRTUAL HEATER")
    click.echo("=" * 60)

    # Get telemetry for this specific virtual heater
    virt_heater_telem = telemetry.get_telem_by_systemid(virt_heater.system_id)

    # Combine config and telemetry data for virtual heater
    heater_data: dict[Any, Any] = {**dict(virt_heater), **dict(virt_heater_telem)} if virt_heater_telem else dict(virt_heater)

    # Don't display the heater_equipment list in the main output - we'll show those separately
    display_data = {k: v for k, v in heater_data.items() if k != "heater_equipment"}

    for attr_name, value in display_data.items():
        if attr_name == "state":
            value = HeaterState(value).pretty()
        elif attr_name == "mode":
            value = HeaterMode(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")

    # Now display physical heater equipment if any
    if virt_heater.heater_equipment:
        click.echo("\nPhysical Heater Equipment:")
        click.echo("-" * 60)
        for equip in virt_heater.heater_equipment:
            _print_heater_equipment_info(equip, telemetry)

    click.echo("=" * 60)


def _print_heater_equipment_info(equip: MSPHeaterEquip, telemetry: Telemetry) -> None:
    """Format and print physical heater equipment information.

    Args:
        equip: Heater equipment object from MSPConfig
        telemetry: Telemetry object to fetch equipment telemetry from
    """
    click.echo("")

    # Get telemetry for this specific heater equipment
    equip_telem = telemetry.get_telem_by_systemid(equip.system_id)

    # Combine config and telemetry data for heater equipment
    equip_data: dict[Any, Any] = {**dict(equip), **dict(equip_telem)} if equip_telem else dict(equip)

    for attr_name, value in equip_data.items():
        if attr_name == "heater_type":
            value = HeaterType(value).pretty()
        elif attr_name == "state":
            value = HeaterState(value).pretty()
        elif isinstance(value, list):
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"  {display_name:18} : {value}")
