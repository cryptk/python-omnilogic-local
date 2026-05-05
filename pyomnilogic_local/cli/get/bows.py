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
def bows(ctx: click.Context) -> None:
    """List all Bodies of Water (BOWs) and their current status.

    Displays information about all bodies of water including their system IDs,
    names, types (pool/spa), water temperature, flow status, and attached equipment.

    Example:
        omnilogic get bows
    """
    omnilogic: OmniLogic = ctx.obj["OMNILOGIC"]
    all_bows = omnilogic.all_bows
    for bow in all_bows:
        echo_properties(bow)
        click.echo("\n  Equipment Counts:")

        _print_equipment_count("Filter", len(bow.filters))
        _print_equipment_count("Pump", len(bow.pumps))
        _print_equipment_count("Heater (virtual)", 1 if bow.heater else 0)
        _print_equipment_count("Heaters (physical)", len(bow.heater.heater_equipment) if bow.heater else 0)
        _print_equipment_count("Sensors", len(bow.sensors))
        _print_equipment_count("Lights", len(bow.lights))
        _print_equipment_count("Relays", len(bow.relays))
        _print_equipment_count("Chlorinator (virtual)", 1 if bow.chlorinator else 0)
        _print_equipment_count("Chlorinators (physical)", len(bow.chlorinator.chlorinator_equipment) if bow.chlorinator else 0)
        _print_equipment_count("CSAD (virtual)", 1 if bow.csad else 0)
        _print_equipment_count("CSADs (physical)", len(bow.csad.csad_equipment) if bow.csad else 0)

        click.echo("=" * 60)

    if len(all_bows) == 0:
        click.echo("No Bodies of Water found in the system configuration.")


def _print_equipment_count(name: str, count: int) -> None:
    """Helper function to print equipment counts with styling."""
    click.echo(f"  - {click.style(name, fg='green')}: {count}")
