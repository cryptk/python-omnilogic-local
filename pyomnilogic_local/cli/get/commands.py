# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

import click

from pyomnilogic_local.cli import ensure_connection
from pyomnilogic_local.cli.get.backyard import backyard
from pyomnilogic_local.cli.get.bows import bows
from pyomnilogic_local.cli.get.chlorinators import chlorinators
from pyomnilogic_local.cli.get.csads import csads
from pyomnilogic_local.cli.get.filters import filters
from pyomnilogic_local.cli.get.groups import groups
from pyomnilogic_local.cli.get.heaters import heaters
from pyomnilogic_local.cli.get.lights import lights
from pyomnilogic_local.cli.get.pumps import pumps
from pyomnilogic_local.cli.get.relays import relays
from pyomnilogic_local.cli.get.schedules import schedules
from pyomnilogic_local.cli.get.sensors import sensors
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
get.add_command(chlorinators)
get.add_command(csads)
get.add_command(filters)
get.add_command(groups)
get.add_command(heaters)
get.add_command(lights)
get.add_command(pumps)
get.add_command(relays)
get.add_command(schedules)
get.add_command(sensors)
get.add_command(valves)
