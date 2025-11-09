# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import RelayFunction, RelayState, RelayType, RelayWhyOn

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPRelay
    from pyomnilogic_local.models.telemetry import Telemetry, TelemetryType


@click.command()
@click.pass_context
def relays(ctx: click.Context) -> None:
    """List all relays and their current settings.

    Displays information about all relays including their system IDs, names,
    current state, type, and function.

    Example:
        omnilogic get relays
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    relays_found = False

    # Check for relays in the backyard
    if mspconfig.backyard.relay:
        for relay in mspconfig.backyard.relay:
            relays_found = True
            _print_relay_info(relay, telemetry.get_telem_by_systemid(relay.system_id))

    # Check for relays in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.relay:
                for relay in bow.relay:
                    relays_found = True
                    _print_relay_info(relay, telemetry.get_telem_by_systemid(relay.system_id))

    if not relays_found:
        click.echo("No relays found in the system configuration.")


def _print_relay_info(relay: MSPRelay, telemetry: TelemetryType | None) -> None:
    """Format and print relay information in a nice table format.

    Args:
        relay: Relay object from MSPConfig with attributes to display
        telemetry: Telemetry object containing current state information
    """
    click.echo("\n" + "=" * 60)
    click.echo("RELAY")
    click.echo("=" * 60)

    relay_data: dict[Any, Any] = {**dict(relay), **dict(telemetry)} if telemetry else dict(relay)
    for attr_name, value in relay_data.items():
        if attr_name == "state":
            value = RelayState(value).pretty()
        elif attr_name == "type":
            value = RelayType(value).pretty()
        elif attr_name == "function":
            value = RelayFunction(value).pretty()
        elif attr_name == "why_on":
            value = RelayWhyOn(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
