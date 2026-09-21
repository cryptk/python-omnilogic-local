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
def light(ctx: click.Context, system_id: int) -> None:
    """Interact with a light by system ID.

    If no subcommand is given, displays all properties of the light.

    Example:
        omnilogic light 5 turn_on
        omnilogic light 5 turn_off
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]

    equipment = omnilogic.all_lights.get_by_id(system_id)
    if equipment is None:
        raise click.ClickException(f"No light found with system_id {system_id}. Use 'omnilogic get lights' to list available lights.")

    ctx.obj["EQUIPMENT"] = equipment

    if ctx.invoked_subcommand is None:
        echo_properties(equipment)


@light.command("turn_on")
@click.pass_context
def turn_on(ctx: click.Context) -> None:
    """Turn the light on."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_on())
    click.echo(f"Turned on '{equipment.name}' (system_id={equipment.system_id})")


@light.command("turn_off")
@click.pass_context
def turn_off(ctx: click.Context) -> None:
    """Turn the light off."""
    equipment = ctx.obj["EQUIPMENT"]
    asyncio.run(equipment.turn_off())
    click.echo(f"Turned off '{equipment.name}' (system_id={equipment.system_id})")
