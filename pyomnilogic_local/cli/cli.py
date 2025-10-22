import asyncio
from typing import Any

import click

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.cli.debug import commands as debug
from pyomnilogic_local.cli.get import commands as get
from pyomnilogic_local.cli.utils import async_get_mspconfig, async_get_telemetry


async def get_omni(host: str) -> OmniLogicAPI:
    return OmniLogicAPI(host, 10444, 5.0)


async def fetch_startup_data(omni: OmniLogicAPI) -> tuple[Any, Any]:
    """Fetch MSPConfig and Telemetry from the controller."""
    try:
        mspconfig = await async_get_mspconfig(omni)
        telemetry = await async_get_telemetry(omni)
    except Exception as exc:
        raise RuntimeError(f"[ERROR] Failed to fetch config or telemetry from controller: {exc}") from exc
    return mspconfig, telemetry


@click.group()
@click.pass_context
@click.option("--host", default="127.0.0.1", help="Hostname or IP address of omnilogic system")
def entrypoint(ctx: click.Context, host: str) -> None:
    """Main CLI entrypoint for OmniLogic local control."""
    ctx.ensure_object(dict)
    try:
        omni = asyncio.run(get_omni(host))
        mspconfig, telemetry = asyncio.run(fetch_startup_data(omni))
    except Exception as exc:  # pylint: disable=broad-except
        click.secho(str(exc), fg="red", err=True)
        ctx.exit(1)
    ctx.obj["OMNI"] = omni
    ctx.obj["MSPCONFIG"] = mspconfig
    ctx.obj["TELEMETRY"] = telemetry


entrypoint.add_command(debug.debug)
entrypoint.add_command(get.get)
