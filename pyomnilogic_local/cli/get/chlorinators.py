# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from pyomnilogic_local.cli.utils import echo_properties

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic


@click.command()
@click.pass_context
def chlorinators(ctx: click.Context) -> None:
    """List all chlorinators and their current settings.

    Displays information about all chlorinators including their system IDs, names,
    salt levels, operational status, alerts, and errors.

    Example:
        omnilogic get chlorinators
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]

    chlorinators = omnilogic.all_chlorinators
    for chlor in chlorinators:
        echo_properties(chlor)

    if len(chlorinators) == 0:
        click.echo("No chlorinators found in the system configuration.")
