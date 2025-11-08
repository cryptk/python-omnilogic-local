# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click

from pyomnilogic_local.omnitypes import CSADMode, CSADType

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPCSAD, MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryCSAD


@click.command()
@click.pass_context
def csads(ctx: click.Context) -> None:
    """List all CSAD (Chemistry Sense and Dispense) systems and their current settings.

    Displays information about all CSAD systems including their system IDs, names,
    current pH/ORP readings, mode, and target values.

    Example:
        omnilogic get csads
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    csads_found = False

    # Check for CSADs in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.csad:
                for csad in bow.csad:
                    csads_found = True
                    _print_csad_info(csad, cast("TelemetryCSAD", telemetry.get_telem_by_systemid(csad.system_id)))

    if not csads_found:
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
