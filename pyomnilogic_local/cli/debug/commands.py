# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"
import asyncio
from pathlib import Path

import click

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.cli import ensure_connection
from pyomnilogic_local.cli.pcap_utils import parse_pcap_file, process_pcap_messages
from pyomnilogic_local.cli.utils import async_get_filter_diagnostics


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
    mspconfig = asyncio.run(omni.async_get_config(raw=ctx.obj["RAW"]))
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
@click.pass_context
def parse_pcap(ctx: click.Context, pcap_file: Path) -> None:
    """Parse a PCAP file and reconstruct Omnilogic protocol communication.

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
        raise click.Abort()

    # Process all packets and extract OmniLogic messages
    results = process_pcap_messages(packets)

    # Display the results
    for src_ip, dst_ip, omni_msg, decoded_content in results:
        click.echo(f"\n{src_ip} sent {omni_msg.type.name} to {dst_ip}")

        if decoded_content:
            click.echo("Decoded message content:")
            click.echo(decoded_content)
            click.echo()  # Extra newline for readability
