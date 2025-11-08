# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from pyomnilogic_local.omnitypes import RelayFunction, RelayType, RelayWhyOn, ValveActuatorState

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPConfig, MSPRelay
    from pyomnilogic_local.models.telemetry import Telemetry


@click.command()
@click.pass_context
def valves(ctx: click.Context) -> None:
    """List all valve actuators and their current settings.

    Displays information about all valve actuators (relays with type VALVE_ACTUATOR)
    including their system IDs, names, functions, current state, and operational status.

    Valve actuators control physical valves for features like waterfalls, fountains,
    and other water features.

    Valves will also show under the output of `get relays` as they are a type of relay.

    Example:
        omnilogic get valves
    """
    mspconfig: MSPConfig = ctx.obj["MSPCONFIG"]
    telemetry: Telemetry = ctx.obj["TELEMETRY"]

    valves_found = False

    # Check for valve actuators in the backyard
    if mspconfig.backyard.relay:
        for relay in mspconfig.backyard.relay:
            if relay.type == RelayType.VALVE_ACTUATOR:
                valves_found = True
                _print_valve_info(relay, telemetry)

    # Check for valve actuators in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.relay:
                for relay in bow.relay:
                    if relay.type == RelayType.VALVE_ACTUATOR:
                        valves_found = True
                        _print_valve_info(relay, telemetry)

    if not valves_found:
        click.echo("No valve actuators found in the system configuration.")


def _print_valve_info(relay: MSPRelay, telemetry: Telemetry) -> None:
    """Format and print valve actuator information in a nice table format.

    Args:
        relay: Relay object from MSPConfig with attributes to display (valve actuator)
        telemetry: Telemetry object to fetch valve telemetry from
    """
    click.echo("\n" + "=" * 60)
    click.echo("VALVE ACTUATOR")
    click.echo("=" * 60)

    # Get telemetry for this specific valve actuator
    valve_telem = telemetry.get_telem_by_systemid(relay.system_id)

    # Combine config and telemetry data
    valve_data: dict[Any, Any] = {**dict(relay), **dict(valve_telem)} if valve_telem else dict(relay)

    for attr_name, value in valve_data.items():
        if attr_name == "type":
            value = RelayType(value).pretty()
        elif attr_name == "function":
            value = RelayFunction(value).pretty()
        elif attr_name == "state":
            value = ValveActuatorState(value).pretty()
        elif attr_name == "why_on":
            value = RelayWhyOn(value).pretty()
        elif isinstance(value, list):
            # Format lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
