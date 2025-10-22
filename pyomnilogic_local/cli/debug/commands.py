# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"
import asyncio
import xml.etree.ElementTree as ET
import zlib
from collections import defaultdict
from pathlib import Path
from typing import Literal, overload

import click
from scapy.layers.inet import UDP
from scapy.utils import rdpcap

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.cli.utils import async_get_mspconfig, async_get_telemetry
from pyomnilogic_local.models.filter_diagnostics import FilterDiagnostics
from pyomnilogic_local.models.leadmessage import LeadMessage
from pyomnilogic_local.omnitypes import MessageType
from pyomnilogic_local.protocol import OmniLogicMessage


@click.group()
@click.option("--raw/--no-raw", default=False, help="Output the raw XML from the OmniLogic, do not parse the response")
@click.pass_context
def debug(ctx: click.Context, raw: bool) -> None:
    # Container for all get commands

    ctx.ensure_object(dict)
    ctx.obj["RAW"] = raw


@debug.command()
@click.pass_context
def get_mspconfig(ctx: click.Context) -> None:
    mspconfig = asyncio.run(async_get_mspconfig(ctx.obj["OMNI"], ctx.obj["RAW"]))
    click.echo(mspconfig)


@debug.command()
@click.pass_context
def get_telemetry(ctx: click.Context) -> None:
    telemetry = asyncio.run(async_get_telemetry(ctx.obj["OMNI"], ctx.obj["RAW"]))
    click.echo(telemetry)


@debug.command()
@click.option("--pool-id", help="System ID of the Body Of Water the filter is associated with")
@click.option("--filter-id", help="System ID of the filter to request diagnostics for")
@click.pass_context
def get_filter_diagnostics(ctx: click.Context, pool_id: int, filter_id: int) -> None:
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


@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[True]) -> str: ...
@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[False]) -> FilterDiagnostics: ...
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: bool) -> FilterDiagnostics | str:
    filter_diags = await omni.async_get_filter_diagnostics(pool_id, filter_id, raw=raw)
    return filter_diags


@debug.command()
@click.argument("pcap_file", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def parse_pcap(ctx: click.Context, pcap_file: Path) -> None:
    """Parse a PCAP file and reconstruct Omnilogic protocol communication."""
    # Read the PCAP file
    try:
        packets = rdpcap(str(pcap_file))
    except Exception as e:
        click.echo(f"Error reading PCAP file: {e}", err=True)
        raise click.Abort()

    # Track multi-message sequences (LeadMessage + BlockMessages)
    # Key: (src_ip, dst_ip, msg_id), Value: list of messages
    message_sequences: dict[tuple[str, str, int], list[OmniLogicMessage]] = defaultdict(list)

    # Process packets in order
    for packet in packets:
        if not packet.haslayer(UDP):
            click.echo("Not a UDP packet, skipping...", err=True)
            continue

        udp = packet[UDP]
        src_ip = packet.payload.src
        dst_ip = packet.payload.dst

        # Parse the Omnilogic message
        try:
            omni_msg = OmniLogicMessage.from_bytes(bytes(udp.payload))
            click.echo(f"Parsed Omnilogic message: {omni_msg}")
        except Exception:  # pylint: disable=broad-except
            # Not an Omnilogic message, skip it
            click.echo("Not an Omnilogic message, skipping...", err=True)
            continue

        # Print the basic packet info
        click.echo(f"{src_ip} sent {omni_msg.type.name} to {dst_ip}")

        # Track LeadMessage/BlockMessage sequences
        if omni_msg.type == MessageType.MSP_LEADMESSAGE:
            # Start a new sequence
            seq_key = (src_ip, dst_ip, omni_msg.id)
            message_sequences[seq_key] = [omni_msg]
        elif omni_msg.type == MessageType.MSP_BLOCKMESSAGE:
            # Find the matching LeadMessage sequence
            # We need to find the sequence with the same src/dst and highest ID less than or equal to this message
            matching_seq: tuple[str, str, int] = ("", "", 0)
            for seq_key in message_sequences:
                if seq_key[0] == src_ip and seq_key[1] == dst_ip:
                    # Check if this is the right sequence (the LeadMessage should have been received before this block)
                    if not matching_seq or seq_key[2] > matching_seq[2]:
                        matching_seq = seq_key

            if matching_seq:
                message_sequences[matching_seq].append(omni_msg)

                # Check if we have all the blocks
                lead_msg = message_sequences[matching_seq][0]
                lead_data = LeadMessage.from_orm(ET.fromstring(lead_msg.payload[:-1]))

                # We have LeadMessage + all BlockMessages
                if len(message_sequences[matching_seq]) == lead_data.msg_block_count + 1:
                    # Reassemble and decode
                    try:
                        decoded_msg = _reassemble_and_decode(message_sequences[matching_seq])
                        click.echo(f"\nMessage from {src_ip} decoded:")
                        click.echo(decoded_msg)
                        click.echo()  # Extra newline for readability
                    except Exception as e:  # pylint: disable=broad-except
                        click.echo(f"Error decoding message: {e}", err=True)

                    # Clean up this sequence
                    del message_sequences[matching_seq]


def _reassemble_and_decode(messages: list[OmniLogicMessage]) -> str:
    """
    Reassemble a LeadMessage + BlockMessages sequence and decode the payload.

    Args:
        messages: List containing LeadMessage followed by BlockMessages

    Returns:
        Decoded message content as string
    """
    lead_msg = messages[0]
    block_msgs = messages[1:]

    # Reassemble the blocks
    # Sort by message ID to ensure correct order
    sorted_blocks = sorted(block_msgs, key=lambda m: m.id)

    # Concatenate the block payloads (skip the 8-byte header on each block)
    reassembled = b""
    for block_msg in sorted_blocks:
        reassembled += block_msg.payload[8:]

    # Decompress if necessary
    if lead_msg.compressed:
        reassembled = zlib.decompress(reassembled)

    # Decode to string
    decoded = reassembled.decode("utf-8").strip("\x00")

    return decoded
