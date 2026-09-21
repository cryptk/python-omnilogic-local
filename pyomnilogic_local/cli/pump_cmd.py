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
def pump(ctx: click.Context, system_id: int) -> None:
    """Interact with a pump by system ID.

    If no subcommand is given, displays all properties of the pump.

    Example:
        omnilogic pump 3 turn_on
        omnilogic pump 3 set_speed 75
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]

    equipment = omnilogic.all_pumps.get_by_id(system_id)
    if equipment is None:
        raise click.ClickException(f"No pump found with system_id {system_id}. Use 'omnilogic get pumps' to list available pumps.")

    ctx.obj["EQUIPMENT"] = equipment

    if ctx.invoked_subcommand is None:
        echo_properties(equipment)


@pump.command("turn_on")
@click.pass_context
def turn_on(ctx: click.Context) -> None:
    """Turn the pump on."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_on())
    click.echo(f"Turned on '{equipment.name}' (system_id={equipment.system_id})")


@pump.command("turn_off")
@click.pass_context
def turn_off(ctx: click.Context) -> None:
    """Turn the pump off."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_off())
    click.echo(f"Turned off '{equipment.name}' (system_id={equipment.system_id})")


@pump.command("set_speed")
@click.argument("percent", type=int)
@click.pass_context
def set_speed(ctx: click.Context, percent: int) -> None:
    """Set the pump speed (0-100 percent).

    Example:
        omnilogic pump 3 set_speed 75
    """
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.set_speed(percent))
    click.echo(f"Set '{equipment.name}' (system_id={equipment.system_id}) to {percent}%")
