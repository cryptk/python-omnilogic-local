# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.cli.utils import echo_properties
from pyomnilogic_local.omnitypes import CSADMode, CSADType

if TYPE_CHECKING:
    from pyomnilogic_local import OmniLogic
    from pyomnilogic_local.models.mspconfig import MSPCSAD
    from pyomnilogic_local.models.telemetry import TelemetryCSAD


@click.command()
@click.pass_context
def csads(ctx: click.Context) -> None:
    """List all CSAD (Chemistry Sense and Dispense) systems and their current settings.

    Displays information about all CSAD systems including their system IDs, names,
    current pH/ORP readings, mode, and target values.

    Example:
        omnilogic get csads
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]
    all_csads = omnilogic.all_csads
    for csad in all_csads:
        echo_properties(csad)

    if len(all_csads) == 0:
        click.echo("No CSAD systems found in the system configuration.")


def _print_csad_info(csad: MSPCSAD, telemetry: TelemetryCSAD | None) -> None:
    """Format and print CSAD information in a nice table format.

    Args:
        csad: CSAD object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("CSAD (CHEMISTRY SENSE AND DISPENSE)")
    click.echo("=" * 60)

    csad_data: dict[Any, Any] = {**dict(csad), **dict(telemetry)} if telemetry else dict(csad)
    for attr_name, value in csad_data.items():
        if attr_name == "equip_type":
            value = CSADType(value).pretty()
        elif attr_name == "mode":
            value = CSADMode(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
