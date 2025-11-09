# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import click

from pyomnilogic_local.cli import ensure_connection
from pyomnilogic_local.cli.pcap_utils import parse_pcap_file, process_pcap_messages
from pyomnilogic_local.cli.utils import async_get_filter_diagnostics

if TYPE_CHECKING:
    from pyomnilogic_local.api.api import OmniLogicAPI


@click.group()
@click.option("--raw/--no-raw", default=False, help="Output the raw XML from the OmniLogic, do not parse the response")
@click.pass_context
def debug(ctx: click.Context, raw: bool) -> None:
    """Debug commands for low-level controller access.

    These commands provide direct access to controller data and debugging utilities
    including configuration, telemetry, diagnostics, and PCAP file analysis.
    """
    ctx.ensure_object(dict)
    ctx.obj["RAW"] = raw
    # Don't connect yet - parse_pcap doesn't need it, others will call ensure_connection individually


@debug.command()
@click.pass_context
def get_mspconfig(ctx: click.Context) -> None:
    """Retrieve the MSP configuration from the controller.

    The MSP configuration contains all pool equipment definitions, system IDs,
    and configuration parameters. Use --raw to see the unprocessed XML.

    Example:
        omnilogic debug get-mspconfig
        omnilogic debug --raw get-mspconfig

    """
    ensure_connection(ctx)
    omni: OmniLogicAPI = ctx.obj["OMNI"]
    mspconfig = asyncio.run(omni.async_get_mspconfig(raw=ctx.obj["RAW"]))
    click.echo(mspconfig)


@debug.command()
@click.pass_context
def get_telemetry(ctx: click.Context) -> None:
    """Retrieve current telemetry data from the controller.

    Telemetry includes real-time sensor readings, equipment states, temperatures,
    and other operational data. Use --raw to see the unprocessed XML.

    Example:
        omnilogic debug get-telemetry
        omnilogic debug --raw get-telemetry

    """
    ensure_connection(ctx)
    omni: OmniLogicAPI = ctx.obj["OMNI"]
    telemetry = asyncio.run(omni.async_get_telemetry(raw=ctx.obj["RAW"]))
    click.echo(telemetry)


@debug.command()
@click.option(
    "--pool-id", required=True, type=int, help="System ID of the Body Of Water the filter is associated with. Example: --pool-id 1"
)
@click.option("--filter-id", required=True, type=int, help="System ID of the filter to request diagnostics for. Example: --filter-id 5")
@click.pass_context
def get_filter_diagnostics(ctx: click.Context, pool_id: int, filter_id: int) -> None:
    """Get diagnostic information for a specific filter/pump.

    This command retrieves detailed diagnostic data including firmware versions,
    power consumption, and error status for a filter or pump.

    Example:
        omnilogic debug get-filter-diagnostics --pool-id 1 --filter-id 5

    """
    ensure_connection(ctx)
    filter_diags = asyncio.run(async_get_filter_diagnostics(ctx.obj["OMNI"], pool_id, filter_id, ctx.obj["RAW"]))
    if ctx.obj["RAW"]:
        click.echo(filter_diags)
    else:
        drv1 = chr(filter_diags.get_param_by_name("DriveFWRevisionB1"))
        drv2 = chr(filter_diags.get_param_by_name("DriveFWRevisionB2"))
        drv3 = chr(filter_diags.get_param_by_name("DriveFWRevisionB3"))
        drv4 = chr(filter_diags.get_param_by_name("DriveFWRevisionB4"))
        dfw1 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB1"))
        dfw2 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB2"))
        dfw3 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB3"))
        dfw4 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB4"))
        pow1 = filter_diags.get_param_by_name("PowerMSB")
        pow2 = filter_diags.get_param_by_name("PowerLSB")
        errs = filter_diags.get_param_by_name("ErrorStatus")
        click.echo(
            f"DRIVE FW REV: {drv1}{drv2}.{drv3}{drv4}\n"
            f"DISPLAY FW REV: {dfw1}{dfw2}.{dfw3}.{dfw4}\n"
            f"POWER: {pow1:x}{pow2:x}W\n"
            f"ERROR STATUS: {errs}"
        )


@debug.command()
@click.argument("pcap_file", type=click.Path(exists=True, path_type=Path))
def parse_pcap(pcap_file: Path) -> None:
    """Parse a PCAP file and reconstruct OmniLogic protocol communication.

    Analyzes network packet captures to decode OmniLogic protocol messages.
    Automatically reassembles multi-part messages (LeadMessage + BlockMessages)
    and decompresses payloads.

    The PCAP file should contain UDP traffic captured from OmniLogic controller
    communication (typically on port 10444).

    Example:
        omnilogic debug parse-pcap /path/to/capture.pcap
        tcpdump -i eth0 -w pool.pcap udp port 10444
        omnilogic debug parse-pcap pool.pcap

    """
    # Read the PCAP file
    try:
        packets = parse_pcap_file(str(pcap_file))
    except Exception as e:
        click.echo(f"Error reading PCAP file: {e}", err=True)
        raise click.Abort from e

    # Process all packets and extract OmniLogic messages
    results = process_pcap_messages(packets)

    # Display the results
    for src_ip, dst_ip, omni_msg, decoded_content in results:
        click.echo(f"\n{src_ip} sent {omni_msg.type.name} to {dst_ip}")

        if decoded_content:
            click.echo("Decoded message content:")
            click.echo(decoded_content)
            click.echo()  # Extra newline for readability


@debug.command()
@click.argument("bow_id", type=int)
@click.argument("equip_id", type=int)
@click.argument("is_on")
@click.pass_context
def set_equipment(ctx: click.Context, bow_id: int, equip_id: int, is_on: str) -> None:
    """Control equipment by turning it on/off or setting a value.

    BOW_ID: The Body of Water (pool/spa) system ID
    EQUIP_ID: The equipment system ID to control
    IS_ON: Equipment state - can be:
        - Boolean: true/false, on/off, 1/0
        - Integer: 0-100 for variable speed equipment (0=off, 1-100=speed percentage)

    For most equipment (relays, lights), use true/false or 1/0.
    For variable speed pumps/filters, use 0-100 to set speed percentage.

    Examples:
        # Turn on a relay
        omnilogic --host 192.168.1.100 debug set-equipment 7 10 true

        # Turn off a light
        omnilogic --host 192.168.1.100 debug set-equipment 7 15 false

        # Set pump to 50% speed
        omnilogic --host 192.168.1.100 debug set-equipment 7 8 50

        # Turn off pump (0% speed)
        omnilogic --host 192.168.1.100 debug set-equipment 7 8 0

    """
    ensure_connection(ctx)
    omni: OmniLogicAPI = ctx.obj["OMNI"]

    # Parse is_on parameter - can be bool-like string or integer
    is_on_lower = is_on.lower()
    if is_on_lower in ("true", "on", "yes", "1"):
        is_on_value: int | bool = True
    elif is_on_lower in ("false", "off", "no", "0"):
        is_on_value = False
    else:
        # Try to parse as integer for variable speed equipment
        try:
            is_on_value = int(is_on)
            if not 0 <= is_on_value <= 100:
                click.echo(f"Error: Integer value must be between 0-100, got {is_on_value}", err=True)
                raise click.Abort
        except ValueError as exc:
            click.echo(f"Error: Invalid value '{is_on}'. Use true/false, on/off, or 0-100 for speed.", err=True)
            raise click.Abort from exc

    # Execute the command
    try:
        asyncio.run(omni.async_set_equipment(bow_id, equip_id, is_on_value))
        if isinstance(is_on_value, bool):
            state = "ON" if is_on_value else "OFF"
            click.echo(f"Successfully set equipment {equip_id} in BOW {bow_id} to {state}")
        else:
            click.echo(f"Successfully set equipment {equip_id} in BOW {bow_id} to {is_on_value}%")
    except Exception as e:
        click.echo(f"Error setting equipment: {e}", err=True)
        raise click.Abort from e
