from __future__ import annotations

import asyncio

import click

from pyomnilogic_local import OmniLogic
from pyomnilogic_local.cli.debug import commands as debug
from pyomnilogic_local.cli.get import commands as get


@click.group()
@click.pass_context
@click.option("--host", default="127.0.0.1", help="Hostname or IP address of OmniLogic system (default: 127.0.0.1)")
@click.option("--port", default=10444, help="Port number of OmniLogic system (default: 10444)")
@click.option("--timeout", default=5, help="Timeout duration for connecting to OmniLogic system in seconds (default: 5)")
def entrypoint(ctx: click.Context, host: str, port: int, timeout: int) -> None:
    """OmniLogic Local Control - Command line interface for Hayward pool controllers.

    This CLI provides local control and monitoring of Hayward OmniLogic and OmniHub
    pool controllers using their local UDP API (typically on port 10444).

    The CLI connects to your pool controller when you run a command and caches
    configuration and telemetry data for use by that command.

    Examples:
        # Connect to controller at default address
        omnilogic get lights

        # Connect to specific controller IP
        omnilogic --host 192.168.1.100 debug get-telemetry

        # Get raw XML responses for debugging
        omnilogic debug --raw get-mspconfig

    For more information, visit: https://github.com/cryptk/python-omnilogic-local
    """
    ctx.ensure_object(dict)

    # Store the host for later connection, but don't connect yet
    ctx.obj["HOST"] = host
    ctx.obj["PORT"] = port
    ctx.obj["TIMEOUT"] = timeout
    omnilogic = OmniLogic(host, port, timeout)  # Store the OmniLogic instance for later use

    asyncio.run(omnilogic.refresh(force=True))

    ctx.obj["OMNILOGIC"] = omnilogic

    # If no subcommand was provided, show help and exit
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


entrypoint.add_command(debug.debug)
entrypoint.add_command(get.get)
