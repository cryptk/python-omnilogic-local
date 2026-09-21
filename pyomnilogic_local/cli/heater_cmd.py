# mypy: disable-error-code="misc"

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click

from pyomnilogic_local.cli.utils import echo_properties

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic


@click.group(invoke_without_command=True)
@click.argument("system_id", type=int)
@click.pass_context
def heater(ctx: click.Context, system_id: int) -> None:
    """Interact with a heater by system ID.

    If no subcommand is given, displays all properties of the heater.

    Example:
        omnilogic heater 4
        omnilogic heater 4 turn_on
        omnilogic heater 4 set_temperature 82
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]

    equipment = omnilogic.all_heaters.get_by_id(system_id)
    if equipment is None:
        raise click.ClickException(f"No heater found with system_id {system_id}. Use 'omnilogic get heaters' to list available heaters.")

    ctx.obj["EQUIPMENT"] = equipment

    if ctx.invoked_subcommand is None:
        echo_properties(equipment)


@heater.command("turn_on")
@click.pass_context
def turn_on(ctx: click.Context) -> None:
    """Turn the heater on."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_on())
    click.echo(f"Turned on '{equipment.name}' (system_id={equipment.system_id})")


@heater.command("turn_off")
@click.pass_context
def turn_off(ctx: click.Context) -> None:
    """Turn the heater off."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_off())
    click.echo(f"Turned off '{equipment.name}' (system_id={equipment.system_id})")


@heater.command("set_temperature")
@click.argument("temperature", type=int)
@click.pass_context
def set_temperature(ctx: click.Context, temperature: int) -> None:
    """Set the heater target temperature (Fahrenheit).

    Example:
        omnilogic heater 4 set_temperature 82
    """
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.set_temperature(temperature))
    click.echo(f"Set '{equipment.name}' (system_id={equipment.system_id}) to {temperature}°F")


@heater.command("set_solar_temperature")
@click.argument("temperature", type=int)
@click.pass_context
def set_solar_temperature(ctx: click.Context, temperature: int) -> None:
    """Set the solar heater target temperature (Fahrenheit).

    Example:
        omnilogic heater 4 set_solar_temperature 90
    """
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.set_solar_temperature(temperature))
    click.echo(f"Set solar temperature for '{equipment.name}' (system_id={equipment.system_id}) to {temperature}°F")
