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
def relay(ctx: click.Context, system_id: int) -> None:
    """Interact with a relay by system ID.

    If no subcommand is given, displays all properties of the relay.

    Example:
        omnilogic relay 6 turn_on
        omnilogic relay 6 turn_off
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]

    equipment = omnilogic.all_relays.get_by_id(system_id)
    if equipment is None:
        raise click.ClickException(f"No relay found with system_id {system_id}. Use 'omnilogic get relays' to list available relays.")

    ctx.obj["EQUIPMENT"] = equipment

    if ctx.invoked_subcommand is None:
        echo_properties(equipment)


@relay.command("turn_on")
@click.pass_context
def turn_on(ctx: click.Context) -> None:
    """Turn the relay on."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_on())
    click.echo(f"Turned on '{equipment.name}' (system_id={equipment.system_id})")


@relay.command("turn_off")
@click.pass_context
def turn_off(ctx: click.Context) -> None:
    """Turn the relay off."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_off())
    click.echo(f"Turned off '{equipment.name}' (system_id={equipment.system_id})")
