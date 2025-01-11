# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"
import asyncio

import click

from pyomnilogic_local.cli.utils import async_get_mspconfig


@click.group()
@click.pass_context
def get(ctx: click.Context) -> None:
    # Container for all get commands

    ctx.ensure_object(dict)


@get.command()
@click.pass_context
def lights(ctx: click.Context) -> None:
    mspconfig = asyncio.run(async_get_mspconfig(ctx.obj["OMNI"]))
    # Return data about lights in the backyard
    if mspconfig.backyard.colorlogic_light:
        for light in mspconfig.backyard.colorlogic_light:
            click.echo(light)

    # Return data about lights in the Body of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.colorlogic_light:
                for cl_light in bow.colorlogic_light:
                    for k, v in cl_light:
                        click.echo(f"{k:15}\t{str(v)}")
