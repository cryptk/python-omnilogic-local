# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

import click

from pyomnilogic_local.cli import ensure_connection


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


@get.command()
@click.pass_context
def lights(ctx: click.Context) -> None:
    """List all ColorLogic lights and their current settings.

    Displays information about all lights including their system IDs, names,
    current state, and available light shows.

    Example:
        omnilogic get lights
    """
    mspconfig = ctx.obj["MSPCONFIG"]

    lights_found = False

    # Check for lights in the backyard
    if mspconfig.backyard.colorlogic_light:
        for light in mspconfig.backyard.colorlogic_light:
            lights_found = True
            _print_light_info(light)

    # Check for lights in Bodies of Water
    if mspconfig.backyard.bow:
        for bow in mspconfig.backyard.bow:
            if bow.colorlogic_light:
                for cl_light in bow.colorlogic_light:
                    lights_found = True
                    _print_light_info(cl_light)

    if not lights_found:
        click.echo("No ColorLogic lights found in the system configuration.")


def _print_light_info(light: object) -> None:
    """Format and print light information in a nice table format.

    Args:
        light: Light object from MSPConfig with attributes to display
    """
    click.echo("\n" + "=" * 60)
    for attr_name in dir(light):
        # Skip private/magic attributes and methods
        if attr_name.startswith("_") or callable(getattr(light, attr_name)):
            continue

        value = getattr(light, attr_name)

        # Special handling for show lists - convert to readable format
        if attr_name == "current_show" and isinstance(value, list):
            show_names = [show.name if hasattr(show, "name") else str(show) for show in value]
            value = ", ".join(show_names) if show_names else "None"
        elif isinstance(value, list):
            # Format other lists nicely
            value = ", ".join(str(v) for v in value) if value else "None"

        # Format the attribute name to be more readable
        display_name = attr_name.replace("_", " ").title()
        click.echo(f"{display_name:20} : {value}")
    click.echo("=" * 60)
