"""Utilities for parsing and analyzing PCAP files containing OmniLogic protocol traffic.

This module provides functions to parse network packet captures (PCAP files)
and reconstruct OmniLogic protocol messages, including multi-part message
reassembly and payload decompression.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zlib
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from scapy.layers.inet import UDP
from scapy.utils import rdpcap

from pyomnilogic_local.api.protocol import OmniLogicMessage
from pyomnilogic_local.models.leadmessage import LeadMessage
from pyomnilogic_local.omnitypes import MessageType

if TYPE_CHECKING:
    from scapy.packet import Packet


def parse_pcap_file(pcap_path: str) -> Any:
    """Read and parse a PCAP file.

    Args:
        pcap_path: Path to the PCAP file to read

    Returns:
        PacketList from the PCAP file

    Raises:
        OSError: If the PCAP file cannot be read
    """
    return rdpcap(pcap_path)


def extract_omnilogic_message(packet: Packet) -> tuple[OmniLogicMessage, str, str] | None:
    """Extract an OmniLogic message from a UDP packet.

    Args:
        packet: Scapy packet to parse

    Returns:
        Tuple of (OmniLogicMessage, source_ip, dest_ip) if packet contains
        valid OmniLogic protocol data, None otherwise
    """
    if not packet.haslayer(UDP):
        return None

    udp = packet[UDP]
    src_ip = packet.payload.src
    dst_ip = packet.payload.dst

    # Not an OmniLogic message
    try:
        omni_msg = OmniLogicMessage.from_bytes(bytes(udp.payload))
    except Exception:
        return None
    else:
        return omni_msg, src_ip, dst_ip


def reassemble_message_blocks(messages: list[OmniLogicMessage]) -> str:
    """Reassemble a LeadMessage + BlockMessages sequence and decode the payload.

    This function takes a sequence of messages starting with a LeadMessage
    followed by BlockMessages, concatenates the block payloads, decompresses
    if necessary, and decodes to a string.

    Args:
        messages: List containing LeadMessage followed by BlockMessages in order

    Returns:
        Decoded message content as string

    Raises:
        Exception: If message reassembly or decompression fails
    """
    lead_msg = messages[0]
    block_msgs = messages[1:]

    # Sort blocks by message ID to ensure correct order
    sorted_blocks = sorted(block_msgs, key=lambda m: m.id)

    # Concatenate the block payloads (skip the 8-byte header on each block)
    reassembled = b""
    for block_msg in sorted_blocks:
        reassembled += block_msg.payload[8:]

    # Decompress if necessary
    if lead_msg.compressed:
        reassembled = zlib.decompress(reassembled)

    # Decode to string
    return reassembled.decode("utf-8").strip("\x00")


def process_pcap_messages(packets: Any) -> list[tuple[str, str, OmniLogicMessage, str | None]]:
    """Process a list of packets and reconstruct OmniLogic protocol messages.

    This function extracts OmniLogic messages from packets, tracks multi-message
    sequences (LeadMessage + BlockMessages), reassembles them, and returns
    all processed messages with their metadata.

    Args:
        packets: PacketList or iterable of Scapy packets to process

    Returns:
        List of tuples containing (src_ip, dst_ip, message, decoded_content).
        For single messages, decoded_content is None.
        For reassembled multi-part messages, decoded_content contains the
        reconstructed payload.
    """
    # Track multi-message sequences (LeadMessage + BlockMessages)
    # Key: (src_ip, dst_ip, msg_id), Value: list of messages
    message_sequences: dict[tuple[str, str, int], list[OmniLogicMessage]] = defaultdict(list)

    results: list[tuple[str, str, OmniLogicMessage, str | None]] = []

    for packet in packets:
        if not (extraction_result := extract_omnilogic_message(packet)):
            continue

        omni_msg, src_ip, dst_ip = extraction_result  # Add basic message info
        results.append((src_ip, dst_ip, omni_msg, None))

        # Track LeadMessage/BlockMessage sequences
        if omni_msg.type == MessageType.MSP_LEADMESSAGE:
            # Start a new sequence
            seq_key = (src_ip, dst_ip, omni_msg.id)
            message_sequences[seq_key] = [omni_msg]

        elif omni_msg.type == MessageType.MSP_BLOCKMESSAGE:
            # Find the matching LeadMessage sequence
            matching_seq: tuple[str, str, int] | None = None
            for seq_key in message_sequences:
                if (seq_key[0] == src_ip and seq_key[1] == dst_ip) and (not matching_seq or seq_key[2] > matching_seq[2]):
                    matching_seq = seq_key

            if matching_seq:
                message_sequences[matching_seq].append(omni_msg)

                # Check if we have all the blocks
                lead_msg = message_sequences[matching_seq][0]
                lead_data = LeadMessage.model_validate(ET.fromstring(lead_msg.payload[:-1]))

                # We have LeadMessage + all BlockMessages
                if len(message_sequences[matching_seq]) == lead_data.msg_block_count + 1:
                    # Failed to decode, skip it
                    try:
                        decoded_msg = reassemble_message_blocks(message_sequences[matching_seq])
                        # Add the reassembled message result
                        results.append((src_ip, dst_ip, lead_msg, decoded_msg))
                    except Exception:
                        pass

                    # Clean up this sequence
                    del message_sequences[matching_seq]

    return results
