# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click

from pyomnilogic_local.omnitypes import GroupState

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPGroup
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryGroup


@click.command()
@click.pass_context
def groups(ctx: click.Context) -> None:
    """List all groups and their current settings.

    Displays information about all groups including their system IDs, names,
    current state, and icon IDs.

    Example:
        omnilogic get groups
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    groups_found = False

    # Check for groups at the top level
    if mspconfig.groups:
        for group in mspconfig.groups:
            groups_found = True
            _print_group_info(group, cast("TelemetryGroup", telemetry.get_telem_by_systemid(group.system_id)))

    if not groups_found:
        click.echo("No groups found in the system configuration.")


def _print_group_info(group: MSPGroup, telemetry: TelemetryGroup | None) -> None:
    """Format and print group information in a nice table format.

    Args:
        group: Group object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("GROUP")
    click.echo("=" * 60)

    group_data: dict[Any, Any] = {**dict(group), **dict(telemetry)} if telemetry else dict(group)
    for attr_name, value in group_data.items():
        if attr_name == "bow_id":
            # Skip bow_id as it's not relevant for groups
            continue
        if attr_name == "state":
            value = GroupState(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
