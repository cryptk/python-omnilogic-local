# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

import click

from pyomnilogic_local.cli import ensure_connection
from pyomnilogic_local.cli.get.backyard import backyard
from pyomnilogic_local.cli.get.bows import bows
from pyomnilogic_local.cli.get.filters import filters
from pyomnilogic_local.cli.get.heaters import heaters
from pyomnilogic_local.cli.get.lights import lights
from pyomnilogic_local.cli.get.valves import valves


@click.group()
@click.pass_context
def get(ctx: click.Context) -> None:
    """Query information about pool equipment and status.

    These commands retrieve specific information about pool equipment
    such as lights, filters, heaters, and other devices.
    """
    ctx.ensure_object(dict)
    # Ensure we're connected to the controller before running any get commands
    ensure_connection(ctx)


# Register subcommands
get.add_command(backyard)
get.add_command(bows)
get.add_command(filters)
get.add_command(heaters)
get.add_command(lights)
get.add_command(valves)
