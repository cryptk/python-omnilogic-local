# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import click

from pyomnilogic_local.cli import ensure_connection
from pyomnilogic_local.cli.pcap_utils import parse_pcap_file, process_pcap_messages
from pyomnilogic_local.cli.utils import async_get_filter_diagnostics

if TYPE_CHECKING:
    from pyomnilogic_local.api.api import OmniLogicAPI
    from pyomnilogic_local.models.telemetry import TelemetryChlorinator


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

    is_on_value: int | bool | str
    # Parse is_on parameter - can be bool-like string or integer
    is_on_lower = is_on.lower()
    if is_on_lower in ("true", "on", "yes", "1"):
        is_on_value = True
    elif is_on_lower in ("false", "off", "no", "0"):
        is_on_value = False
    else:
        is_on_value = is_on

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


@debug.command()
@click.argument("bow_id", type=int)
@click.argument("equip_id", type=int)
@click.argument("timed_percent", type=int)
@click.argument("op_mode", type=int)
@click.pass_context
def set_chlor_params(ctx: click.Context, bow_id: int, equip_id: int, timed_percent: int, op_mode: int) -> None:
    """Set chlorinator parameters with explicit control over configuration.

    This command sets chlorinator parameters using the current chlorinator's
    configuration for cell_type, sc_timeout, bow_type, and orp_timeout, while
    allowing you to specify timed_percent and op_mode. The cfg_state is derived
    from the chlorinator's current on/off state.

    BOW_ID: The Body of Water (pool/spa) system ID
    EQUIP_ID: The chlorinator equipment system ID
    TIMED_PERCENT: Chlorine generation percentage (0-100)
    OP_MODE: Operating mode (0=DISABLED, 1=TIMED, 2=ORP_AUTO)

    Examples:
        # Set chlorinator to 75% in TIMED mode
        omnilogic --host 192.168.1.100 debug set-chlor-params 7 12 75 1

        # Set to ORP AUTO mode with 50% generation
        omnilogic --host 192.168.1.100 debug set-chlor-params 7 12 50 2

    """
    ensure_connection(ctx)
    omni: OmniLogicAPI = ctx.obj["OMNI"]

    # Validate timed_percent
    if not 0 <= timed_percent <= 1000:  # Temporarily allow up to 1000 to test ORP behavior
        click.echo(f"Error: timed_percent must be between 0-100, got {timed_percent}", err=True)
        raise click.Abort

    # Validate op_mode
    if not 0 <= op_mode <= 2:
        click.echo(f"Error: op_mode must be between 0-3, got {op_mode}", err=True)
        raise click.Abort

    # Get MSPConfig and Telemetry to find the chlorinator
    try:
        mspconfig_raw = asyncio.run(omni.async_get_mspconfig(raw=False))
        telemetry_raw = asyncio.run(omni.async_get_telemetry(raw=False))
    except Exception as e:
        click.echo(f"Error retrieving configuration: {e}", err=True)
        raise click.Abort from e

    # Find the BOW
    bow = None
    if mspconfig_raw.backyard.bow:
        for candidate_bow in mspconfig_raw.backyard.bow:
            if candidate_bow.system_id == bow_id:
                bow = candidate_bow
                break

    if bow is None:
        click.echo(f"Error: Body of Water with ID {bow_id} not found", err=True)
        raise click.Abort

    # Find the chlorinator
    if bow.chlorinator is None or bow.chlorinator.system_id != equip_id:
        click.echo(f"Error: Chlorinator with ID {equip_id} not found in BOW {bow_id}", err=True)
        raise click.Abort

    chlorinator = bow.chlorinator

    # Get telemetry for the chlorinator to determine is_on state
    chlorinator_telemetry = telemetry_raw.get_telem_by_systemid(equip_id)
    if chlorinator_telemetry is None:
        click.echo(f"Warning: No telemetry found for chlorinator {equip_id}, defaulting cfg_state to 3 (on)", err=True)
        cfg_state = 3
    else:
        # Cast to TelemetryChlorinator to access enable attribute
        chlorinator_telem = cast("TelemetryChlorinator", chlorinator_telemetry)
        # Determine cfg_state from enable flag in telemetry
        cfg_state = 3 if chlorinator_telem.enable else 2

    # Determine bow_type from equipment type (0=pool, 1=spa)
    bow_type = 0 if bow.equip_type == "BOW_POOL" else 1

    # Get parameters from chlorinator config
    cell_type = chlorinator.cell_type.value
    sc_timeout = chlorinator.superchlor_timeout
    orp_timeout = chlorinator.orp_timeout

    # Execute the command
    try:
        asyncio.run(
            omni.async_set_chlorinator_params(
                pool_id=bow_id,
                equipment_id=equip_id,
                timed_percent=timed_percent,
                cell_type=cell_type,
                op_mode=op_mode,
                sc_timeout=sc_timeout,
                bow_type=bow_type,
                orp_timeout=orp_timeout,
                cfg_state=cfg_state,
            )
        )
        click.echo(
            f"Sent command to chlorinator {equip_id} in BOW {bow_id}:\n"
            f"  Timed Percent: {timed_percent}%\n"
            f"  Operating Mode: {op_mode}\n"
            f"  Config State: {cfg_state} ({'on' if cfg_state == 3 else 'off'})\n"
            f"  Cell Type: {cell_type}\n"
            f"  SC Timeout: {sc_timeout}\n"
            f"  BOW Type: {bow_type}\n"
            f"  ORP Timeout: {orp_timeout}"
        )
    except Exception as e:
        click.echo(f"Error setting chlorinator parameters: {e}", err=True)
        raise click.Abort from e
