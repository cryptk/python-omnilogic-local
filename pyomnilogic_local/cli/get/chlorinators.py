# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click

from pyomnilogic_local.omnitypes import ChlorinatorCellType, ChlorinatorDispenserType, ChlorinatorOperatingMode

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPChlorinator, MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryChlorinator


@click.command()
@click.pass_context
def chlorinators(ctx: click.Context) -> None:
    """List all chlorinators and their current settings.

    Displays information about all chlorinators including their system IDs, names,
    salt levels, operational status, alerts, and errors.

    Example:
        omnilogic get chlorinators
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    chlorinators_found = False

    # Check for chlorinators in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.chlorinator:
                chlorinators_found = True
                _print_chlorinator_info(
                    bow.chlorinator, cast("TelemetryChlorinator", telemetry.get_telem_by_systemid(bow.chlorinator.system_id))
                )

    if not chlorinators_found:
        click.echo("No chlorinators found in the system configuration.")


def _print_chlorinator_info(chlorinator: MSPChlorinator, telemetry: TelemetryChlorinator | None) -> None:
    """Format and print chlorinator information in a nice table format.

    Args:
        chlorinator: Chlorinator object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("CHLORINATOR")
    click.echo("=" * 60)

    chlor_data: dict[Any, Any] = {**dict(chlorinator), **dict(telemetry)} if telemetry else dict(chlorinator)
    for attr_name, value in chlor_data.items():
        if attr_name == "cell_type":
            value = ChlorinatorCellType(value).pretty()
        elif attr_name == "dispenser_type":
            value = ChlorinatorDispenserType(value).pretty()
        elif attr_name == "operating_mode":
            value = ChlorinatorOperatingMode(value).pretty()
        elif attr_name in ("status", "alerts", "errors") and isinstance(value, list):
            # These are computed properties that return lists of flag names
            value = ", ".join(value) if value else "None"
        elif isinstance(value, list):
            # Format other lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
