import asyncio

import click

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.cli.debug import commands as debug
from pyomnilogic_local.cli.get import commands as get


async def get_omni(host: str) -> OmniLogicAPI:
    return OmniLogicAPI(host, 10444, 5.0)


@click.group()
@click.pass_context
@click.option("--host", default="127.0.0.1", help="Hostname or IP address of omnilogic system")
def entrypoint(ctx: click.Context, host: str) -> None:
    ctx.ensure_object(dict)
    omni = asyncio.run(get_omni(host))

    ctx.obj["OMNI"] = omni


entrypoint.add_command(debug.debug)
entrypoint.add_command(get.get)
