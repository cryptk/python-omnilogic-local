# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPSchedule


@click.command()
@click.pass_context
def schedules(ctx: click.Context) -> None:
    """List all schedules and their current settings.

    Displays information about all schedules including their system IDs, names,
    current state, and icon IDs.

    Example:
        omnilogic get schedules
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]

    schedules_found = False

    # Check for schedules at the top level
    if mspconfig.schedules:
        for schedule in mspconfig.schedules:
            schedules_found = True
            _print_schedule_info(schedule)

    if not schedules_found:
        click.echo("No schedules found in the system configuration.")


def _print_schedule_info(schedule: MSPSchedule) -> None:
    """Format and print schedule information in a nice table format.

    Args:
        schedule: Schedule object from MSPConfig with attributes to display
    """
    click.echo("\n" + "=" * 60)
    click.echo("SCHEDULE")
    click.echo("=" * 60)

    schedule_data: dict[Any, Any] = dict(schedule)
    for attr_name, value in schedule_data.items():
        if attr_name == "days_active_raw":
            # Skip raw bitmask field
            continue
        if attr_name == "event":
            value = value.pretty()
        if isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    # Days Active is a computed property, so it's not in the dict representation
    click.echo(f"{'Days Active':20} : {schedule.days_active}")
    click.echo("=" * 60)
