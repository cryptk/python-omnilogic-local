"""Enhanced comprehensive tests for the OmniLogic protocol layer.

Focuses on:
- OmniLogicMessage parsing and serialization (table-driven)
- Protocol error handling
- Message fragmentation and reassembly
- ACK waiting and retry logic
- Connection lifecycle
"""

from __future__ import annotations

import asyncio
import struct
import time
import zlib
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch
from xml.etree import ElementTree as ET

import pytest

from pyomnilogic_local.api.exceptions import (
    OmniFragmentationError,
    OmniMessageFormatError,
    OmniTimeoutError,
)
from pyomnilogic_local.api.protocol import OmniLogicMessage, OmniLogicProtocol
from pyomnilogic_local.omnitypes import ClientType, MessageType

if TYPE_CHECKING:
    from pytest_subtests import SubTests


# ============================================================================
# OmniLogicMessage Tests
# ============================================================================


def test_parse_basic_ack() -> None:
    """Validate that we can parse a basic ACK packet."""
    bytes_ack = b"\x99_\xd1l\x00\x00\x00\x00dv\x8f\xc11.20\x00\x00\x03\xea\x03\x00\x00\x00"
    message = OmniLogicMessage.from_bytes(bytes_ack)
    assert message.id == 2573193580
    assert message.type is MessageType.ACK
    assert message.compressed is False
    assert str(message) == "ID: 2573193580, Type: ACK, Compressed: False, Client: OMNI, Body: "


def test_create_basic_ack() -> None:
    """Validate that we can create a valid basic ACK packet."""
    bytes_ack = b"\x99_\xd1l\x00\x00\x00\x00dv\x8f\xc11.20\x00\x00\x03\xea\x03\x00\x00\x00"
    message = OmniLogicMessage(2573193580, MessageType.ACK, payload=None, version="1.20")
    message.client_type = ClientType.OMNI
    message.timestamp = 1685491649
    assert bytes(message) == bytes_ack


def test_parse_leadmessage() -> None:
    """Validate that we can parse an MSP LeadMessage."""
    bytes_leadmessage = (
        b'\x00\x00\x90v\x00\x00\x00\x00dv\x92\xc11.20\x00\x00\x07\xce\x03\x00\x01\x00<?xml version="1.0" encoding="UTF-8" ?>'
        b'<Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        b'<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">3361</Parameter>'
        b'<Parameter name="MsgBlockCount" dataType="int">4</Parameter><Parameter name="Type" dataType="int">0</Parameter>'
        b"</Parameters></Response>\x00"
    )
    message = OmniLogicMessage.from_bytes(bytes_leadmessage)
    assert message.id == 36982
    assert message.type is MessageType.MSP_LEADMESSAGE
    assert message.timestamp == 1685492417
    assert message.compressed is True
    assert str(message) == "ID: 36982, Type: MSP_LEADMESSAGE, Compressed: True, Client: OMNI"


def test_create_leadmessage() -> None:
    """Validate that we can create a valid MSP LeadMessage."""
    bytes_leadmessage = (
        b'\x00\x00\x90v\x00\x00\x00\x00dv\x92\xc11.20\x00\x00\x07\xce\x03\x00\x01\x00<?xml version="1.0" encoding="UTF-8" ?>'
        b'<Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        b'<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">3361</Parameter>'
        b'<Parameter name="MsgBlockCount" dataType="int">4</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        b"</Response>\x00"
    )
    payload_leadmessage = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">3361</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">4</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    message = OmniLogicMessage(36982, MessageType.MSP_LEADMESSAGE, payload=payload_leadmessage, version="1.20")
    message.client_type = ClientType.OMNI
    message.timestamp = 1685492417
    message.compressed = True
    assert bytes(message) == bytes_leadmessage


def test_message_from_bytes_errors(subtests: SubTests) -> None:
    """Test OmniLogicMessage.from_bytes with various error conditions using table-driven approach."""
    test_cases = [
        # (data, expected_error, description)  # noqa: ERA001
        (b"short", OmniMessageFormatError, "message too short"),
        (b"\x00" * 10, OmniMessageFormatError, "header too short"),
    ]

    for data, expected_error, description in test_cases:
        with subtests.test(msg=description), pytest.raises(expected_error):
            OmniLogicMessage.from_bytes(data)


def test_message_from_bytes_invalid_message_type() -> None:
    """Test parsing with an invalid message type."""
    # Create a valid header but with invalid message type (9999)
    header = struct.pack(
        "!LQ4sLBBBB",
        12345,  # msg_id
        int(time.time()),  # timestamp
        b"1.20",  # version
        9999,  # invalid message type
        0,  # client_type
        0,  # reserved
        0,  # compressed
        0,  # reserved
    )

    with pytest.raises(OmniMessageFormatError, match="Unknown message type"):
        OmniLogicMessage.from_bytes(header + b"payload")


def test_message_from_bytes_invalid_client_type() -> None:
    """Test parsing with an invalid client type."""
    # Create a valid header but with invalid client type (99)
    header = struct.pack(
        "!LQ4sLBBBB",
        12345,  # msg_id
        int(time.time()),  # timestamp
        b"1.20",  # version
        MessageType.ACK.value,  # valid message type
        99,  # invalid client_type
        0,  # reserved
        0,  # compressed
        0,  # reserved
    )

    with pytest.raises(OmniMessageFormatError, match="Unknown client type"):
        OmniLogicMessage.from_bytes(header + b"payload")


def test_message_repr_with_blockmessage() -> None:
    """Test that __repr__ for MSP_BLOCKMESSAGE doesn't include body."""
    message = OmniLogicMessage(123, MessageType.MSP_BLOCKMESSAGE, payload="test")
    repr_str = str(message)
    assert "Body:" not in repr_str
    assert "MSP_BLOCKMESSAGE" in repr_str


def test_message_telemetry_always_compressed() -> None:
    """Test that MSP_TELEMETRY_UPDATE is always marked as compressed."""
    header = struct.pack(
        "!LQ4sLBBBB",
        12345,  # msg_id
        int(time.time()),  # timestamp
        b"1.20",  # version
        MessageType.MSP_TELEMETRY_UPDATE.value,
        0,  # client_type
        0,  # reserved
        0,  # compressed flag is 0, but should be set to True
        0,  # reserved
    )

    message = OmniLogicMessage.from_bytes(header + b"payload")
    assert message.compressed is True  # Should be True even though flag was 0


def test_message_client_type_xml_vs_simple() -> None:
    """Test that messages with payload use XML client type."""
    msg_with_payload = OmniLogicMessage(123, MessageType.REQUEST_CONFIGURATION, payload="<test/>")
    assert msg_with_payload.client_type == ClientType.XML

    msg_without_payload = OmniLogicMessage(456, MessageType.ACK, payload=None)
    assert msg_without_payload.client_type == ClientType.SIMPLE


def test_message_payload_null_termination() -> None:
    """Test that payload is properly null-terminated."""
    message = OmniLogicMessage(123, MessageType.REQUEST_CONFIGURATION, payload="test")
    assert message.payload == b"test\x00"


# ============================================================================
# OmniLogicProtocol Initialization and Connection Tests
# ============================================================================


def test_protocol_initialization() -> None:
    """Test that protocol initializes with correct queue sizes."""
    protocol = OmniLogicProtocol()
    assert protocol.data_queue.maxsize == 100
    assert protocol.error_queue.maxsize == 100


def test_protocol_connection_made() -> None:
    """Test that connection_made sets the transport."""
    protocol = OmniLogicProtocol()
    mock_transport = MagicMock()

    protocol.connection_made(mock_transport)

    assert protocol.transport is mock_transport


def test_protocol_connection_lost_with_exception() -> None:
    """Test that connection_lost raises exception if provided."""
    protocol = OmniLogicProtocol()
    test_exception = RuntimeError("Connection error")

    with pytest.raises(RuntimeError, match="Connection error"):
        protocol.connection_lost(test_exception)


def test_protocol_connection_lost_without_exception() -> None:
    """Test that connection_lost without exception doesn't raise."""
    protocol = OmniLogicProtocol()
    protocol.connection_lost(None)  # Should not raise


# ============================================================================
# Datagram Received Tests
# ============================================================================


def test_datagram_received_valid_message() -> None:
    """Test that valid messages are added to the queue."""
    protocol = OmniLogicProtocol()
    valid_data = bytes(OmniLogicMessage(123, MessageType.ACK))

    protocol.datagram_received(valid_data, ("127.0.0.1", 12345))

    assert protocol.data_queue.qsize() == 1
    message = protocol.data_queue.get_nowait()
    assert message.id == 123
    assert message.type == MessageType.ACK


def test_datagram_received_with_corrupt_data(caplog: pytest.LogCaptureFixture) -> None:
    """Test that corrupt datagram data is handled gracefully and logged."""
    protocol = OmniLogicProtocol()
    corrupt_data = b"short"

    with caplog.at_level("ERROR"):
        protocol.datagram_received(corrupt_data, ("127.0.0.1", 12345))

    assert any("Failed to parse incoming datagram" in r.message for r in caplog.records)
    assert protocol.error_queue.qsize() == 1


def test_datagram_received_queue_overflow(caplog: pytest.LogCaptureFixture) -> None:
    """Test that queue overflow is handled and logged."""
    protocol = OmniLogicProtocol()
    protocol.data_queue = asyncio.Queue(maxsize=1)
    protocol.data_queue.put_nowait(OmniLogicMessage(1, MessageType.ACK))

    valid_data = bytes(OmniLogicMessage(2, MessageType.ACK))
    with caplog.at_level("ERROR"):
        protocol.datagram_received(valid_data, ("127.0.0.1", 12345))

    assert any("Data queue is full" in r.message for r in caplog.records)


def test_datagram_received_unexpected_exception(caplog: pytest.LogCaptureFixture) -> None:
    """Test that unexpected exceptions during datagram processing are handled."""
    protocol = OmniLogicProtocol()

    # Patch OmniLogicMessage.from_bytes to raise an unexpected exception
    with (
        patch("pyomnilogic_local.api.protocol.OmniLogicMessage.from_bytes", side_effect=RuntimeError("Unexpected")),
        caplog.at_level("ERROR"),
    ):
        protocol.datagram_received(b"data", ("127.0.0.1", 12345))

    assert any("Unexpected error processing datagram" in r.message for r in caplog.records)
    assert protocol.error_queue.qsize() == 1


def test_error_received() -> None:
    """Test that error_received puts errors in the error queue."""
    protocol = OmniLogicProtocol()
    test_error = RuntimeError("UDP error")

    protocol.error_received(test_error)

    assert protocol.error_queue.qsize() == 1
    error = protocol.error_queue.get_nowait()
    assert error is test_error


# ============================================================================
# _wait_for_ack Tests
# ============================================================================


@pytest.mark.asyncio
async def test_wait_for_ack_success() -> None:
    """Test successful ACK waiting."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Put an ACK message in the queue
    ack_message = OmniLogicMessage(123, MessageType.ACK)
    await protocol.data_queue.put(ack_message)

    # Should return without raising
    await protocol._wait_for_ack(123)


@pytest.mark.asyncio
async def test_wait_for_ack_wrong_id_continues_waiting() -> None:
    """Test that wrong ACK IDs are consumed and waiting continues for the correct one."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Put wrong ID first, then correct ID
    wrong_ack = OmniLogicMessage(999, MessageType.ACK)
    correct_ack = OmniLogicMessage(123, MessageType.ACK)

    await protocol.data_queue.put(wrong_ack)
    await protocol.data_queue.put(correct_ack)

    await protocol._wait_for_ack(123)
    # Queue should be empty after consuming both messages
    assert protocol.data_queue.qsize() == 0


@pytest.mark.asyncio
async def test_wait_for_ack_leadmessage_instead(caplog: pytest.LogCaptureFixture) -> None:
    """Test that LeadMessage with matching ID is accepted (ACK was dropped)."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Put a LeadMessage with matching ID (simulating dropped ACK)
    leadmsg = OmniLogicMessage(123, MessageType.MSP_LEADMESSAGE)
    await protocol.data_queue.put(leadmsg)

    with caplog.at_level("DEBUG"):
        await protocol._wait_for_ack(123)

    # With matching ID, it's treated as the ACK we're looking for
    assert any("Received ACK for message ID 123" in r.message for r in caplog.records)
    # LeadMessage should NOT be in queue since IDs matched
    assert protocol.data_queue.qsize() == 0


@pytest.mark.asyncio
async def test_wait_for_ack_leadmessage_wrong_id(caplog: pytest.LogCaptureFixture) -> None:
    """Test that LeadMessage with wrong ID is put back in queue and waiting continues."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Put a LeadMessage with wrong ID, then correct ACK
    leadmsg = OmniLogicMessage(999, MessageType.MSP_LEADMESSAGE)
    correct_ack = OmniLogicMessage(123, MessageType.ACK)

    await protocol.data_queue.put(leadmsg)
    await protocol.data_queue.put(correct_ack)

    with caplog.at_level("DEBUG"):
        await protocol._wait_for_ack(123)

    # Should log that ACK was dropped and put LeadMessage back
    assert any("ACK was dropped" in r.message for r in caplog.records)
    # Both messages were consumed and LeadMessage was put back, so queue should have 1 item
    # But the ACK was also consumed, so we actually end up with just the LeadMessage back
    # Actually, looking at the code: LeadMessage gets put back, then we return
    # So BOTH the correct ACK and the LeadMessage should be in the queue
    assert protocol.data_queue.qsize() == 2  # LeadMessage put back, correct ACK also still there


@pytest.mark.asyncio
async def test_wait_for_ack_error_in_queue() -> None:
    """Test that errors from error queue are raised."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    test_error = RuntimeError("Test error")
    await protocol.error_queue.put(test_error)

    with pytest.raises(RuntimeError, match="Test error"):
        await protocol._wait_for_ack(123)


# ============================================================================
# _ensure_sent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ensure_sent_ack_message() -> None:
    """Test that ACK messages don't wait for ACK."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    ack_message = OmniLogicMessage(123, MessageType.ACK)

    # Should return immediately without waiting
    await protocol._ensure_sent(ack_message)

    protocol.transport.sendto.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_sent_xml_ack_message() -> None:
    """Test that XML_ACK messages don't wait for ACK."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    xml_ack_message = OmniLogicMessage(123, MessageType.XML_ACK, payload="<test/>")

    await protocol._ensure_sent(xml_ack_message)

    protocol.transport.sendto.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_sent_success_first_attempt() -> None:
    """Test successful send on first attempt."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Mock _wait_for_ack to succeed immediately
    with patch.object(protocol, "_wait_for_ack", new_callable=AsyncMock) as mock_wait:
        message = OmniLogicMessage(123, MessageType.REQUEST_CONFIGURATION)
        await protocol._ensure_sent(message, max_attempts=3)

    protocol.transport.sendto.assert_called_once()
    mock_wait.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_ensure_sent_timeout_and_retry_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Test that _ensure_sent logs retries and raises on repeated timeout."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    async def always_timeout(*args: object, **kwargs: object) -> None:  # noqa: ARG001
        await asyncio.sleep(0)
        raise TimeoutError

    message = OmniLogicMessage(123, MessageType.REQUEST_CONFIGURATION)
    with patch.object(protocol, "_wait_for_ack", always_timeout), caplog.at_level("WARNING"), pytest.raises(OmniTimeoutError):
        await protocol._ensure_sent(message, max_attempts=3)

    assert any("attempt 1/3" in r.message for r in caplog.records)
    assert any("attempt 2/3" in r.message for r in caplog.records)
    assert any("after 3 attempts" in r.message for r in caplog.records)
    assert protocol.transport.sendto.call_count == 3


# ============================================================================
# send_message and send_and_receive Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_message_generates_random_id() -> None:
    """Test that send_message generates a random ID when none provided."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    with patch.object(protocol, "_ensure_sent", new_callable=AsyncMock) as mock_ensure:
        await protocol.send_message(MessageType.REQUEST_CONFIGURATION, None, msg_id=None)

    mock_ensure.assert_called_once()
    sent_message = mock_ensure.call_args[0][0]
    assert sent_message.id != 0  # Should have a random ID


@pytest.mark.asyncio
async def test_send_message_uses_provided_id() -> None:
    """Test that send_message uses provided ID."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    with patch.object(protocol, "_ensure_sent", new_callable=AsyncMock) as mock_ensure:
        await protocol.send_message(MessageType.REQUEST_CONFIGURATION, None, msg_id=12345)

    mock_ensure.assert_called_once()
    sent_message = mock_ensure.call_args[0][0]
    assert sent_message.id == 12345


@pytest.mark.asyncio
async def test_send_and_receive() -> None:
    """Test send_and_receive calls send_message and _receive_file."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    with (
        patch.object(protocol, "send_message", new_callable=AsyncMock) as mock_send,
        patch.object(protocol, "_receive_file", new_callable=AsyncMock) as mock_receive,
    ):
        mock_receive.return_value = "test response"

        result = await protocol.send_and_receive(MessageType.REQUEST_CONFIGURATION, "payload", 123)

    mock_send.assert_called_once_with(MessageType.REQUEST_CONFIGURATION, "payload", 123)
    mock_receive.assert_called_once()
    assert result == "test response"


# ============================================================================
# _send_ack Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_ack_generates_xml() -> None:
    """Test that _send_ack generates proper XML ACK message."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    with patch.object(protocol, "send_message", new_callable=AsyncMock) as mock_send:
        await protocol._send_ack(12345)

    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == MessageType.XML_ACK
    assert call_args[0][2] == 12345

    # Verify XML structure
    xml_payload = call_args[0][1]
    root = ET.fromstring(xml_payload)
    assert "Request" in root.tag
    name_elem = root.find(".//{http://nextgen.hayward.com/api}Name")
    assert name_elem is not None
    assert name_elem.text == "Ack"


# ============================================================================
# _receive_file Tests - Simple Response
# ============================================================================


@pytest.mark.asyncio
async def test_receive_file_simple_response() -> None:
    """Test receiving a simple (non-fragmented) response."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Create a simple response message
    response_msg = OmniLogicMessage(123, MessageType.GET_TELEMETRY, payload="<telemetry/>")
    await protocol.data_queue.put(response_msg)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock) as mock_ack:
        result = await protocol._receive_file()

    mock_ack.assert_called_once_with(123)
    assert result == "<telemetry/>"


@pytest.mark.asyncio
async def test_receive_file_skips_duplicate_acks(caplog: pytest.LogCaptureFixture) -> None:
    """Test that duplicate ACKs are skipped."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Put duplicate ACKs followed by real message
    ack1 = OmniLogicMessage(111, MessageType.ACK)
    ack2 = OmniLogicMessage(222, MessageType.XML_ACK)
    response = OmniLogicMessage(333, MessageType.GET_TELEMETRY, payload="<data/>")

    await protocol.data_queue.put(ack1)
    await protocol.data_queue.put(ack2)
    await protocol.data_queue.put(response)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock), caplog.at_level("DEBUG"):
        result = await protocol._receive_file()

    assert any("Skipping duplicate ACK" in r.message for r in caplog.records)
    assert result == "<data/>"


@pytest.mark.asyncio
async def test_receive_file_decompresses_data() -> None:
    """Test that compressed responses are decompressed."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Create compressed payload
    original = b"This is test data that will be compressed"
    compressed = zlib.compress(original)

    # Create message with compressed payload
    response_msg = OmniLogicMessage(123, MessageType.GET_TELEMETRY)
    response_msg.compressed = True
    response_msg.payload = compressed

    await protocol.data_queue.put(response_msg)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock):
        result = await protocol._receive_file()

    assert result == original.decode("utf-8")


@pytest.mark.asyncio
async def test_receive_file_decompression_error() -> None:
    """Test that decompression errors are handled."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Create message with invalid compressed data
    response_msg = OmniLogicMessage(123, MessageType.GET_TELEMETRY)
    response_msg.compressed = True
    response_msg.payload = b"invalid compressed data"

    await protocol.data_queue.put(response_msg)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock), pytest.raises(OmniMessageFormatError, match="Failed to decompress"):
        await protocol._receive_file()


# ============================================================================
# _receive_file Tests - Fragmented Response
# ============================================================================


@pytest.mark.asyncio
async def test_receive_file_fragmented_response() -> None:
    """Test receiving a fragmented response with LeadMessage and BlockMessages."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Create LeadMessage
    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">24</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">2</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    # Create BlockMessages with 8-byte header
    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"first_part"

    block2 = OmniLogicMessage(102, MessageType.MSP_BLOCKMESSAGE)
    block2.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"second_part"

    await protocol.data_queue.put(leadmsg)
    await protocol.data_queue.put(block1)
    await protocol.data_queue.put(block2)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock) as mock_ack:
        result = await protocol._receive_file()

    # Should send ACK for LeadMessage and each BlockMessage
    assert mock_ack.call_count == 3
    assert result == "first_partsecond_part"


@pytest.mark.asyncio
async def test_receive_file_fragmented_out_of_order() -> None:
    """Test that fragments received out of order are reassembled correctly."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">30</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">3</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    # Create blocks out of order (IDs: 102, 100, 101)
    block2 = OmniLogicMessage(102, MessageType.MSP_BLOCKMESSAGE)
    block2.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"third"

    block0 = OmniLogicMessage(100, MessageType.MSP_BLOCKMESSAGE)
    block0.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"first"

    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"second"

    await protocol.data_queue.put(leadmsg)
    await protocol.data_queue.put(block2)  # Out of order
    await protocol.data_queue.put(block0)
    await protocol.data_queue.put(block1)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock):
        result = await protocol._receive_file()

    # Should be reassembled in ID order
    assert result == "firstsecondthird"


@pytest.mark.asyncio
async def test_receive_file_fragmented_invalid_leadmessage() -> None:
    """Test that invalid LeadMessage XML raises error."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Create LeadMessage with invalid XML
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload="invalid xml")
    await protocol.data_queue.put(leadmsg)

    with (
        patch.object(protocol, "_send_ack", new_callable=AsyncMock),
        pytest.raises(OmniFragmentationError, match="Failed to parse LeadMessage"),
    ):
        await protocol._receive_file()


@pytest.mark.asyncio
async def test_receive_file_fragmented_timeout_waiting() -> None:
    """Test timeout while waiting for fragments."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">24</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">2</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    await protocol.data_queue.put(leadmsg)
    # Don't put any BlockMessages - will timeout

    with (
        patch.object(protocol, "_send_ack", new_callable=AsyncMock),
        pytest.raises(OmniFragmentationError, match="Timeout receiving fragment"),
    ):
        await protocol._receive_file()


@pytest.mark.asyncio
async def test_receive_file_fragmented_max_wait_time_exceeded() -> None:
    """Test that MAX_FRAGMENT_WAIT_TIME timeout is enforced."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">24</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">2</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    await protocol.data_queue.put(leadmsg)

    # Mock time to simulate timeout
    with patch.object(protocol, "_send_ack", new_callable=AsyncMock), patch("time.time") as mock_time:
        mock_time.side_effect = [0, 31]  # Start at 0, then 31 seconds later (> 30s max)

        with pytest.raises(OmniFragmentationError, match="Timeout waiting for fragments"):
            await protocol._receive_file()


@pytest.mark.asyncio
async def test_receive_file_fragmented_ignores_non_block_messages(caplog: pytest.LogCaptureFixture) -> None:
    """Test that non-BlockMessages during fragmentation are ignored."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">10</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">1</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    # Put LeadMessage, then an ACK (should be ignored), then the actual block
    ack_msg = OmniLogicMessage(999, MessageType.ACK)
    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"data"

    await protocol.data_queue.put(leadmsg)
    await protocol.data_queue.put(ack_msg)
    await protocol.data_queue.put(block1)

    with patch.object(protocol, "_send_ack", new_callable=AsyncMock), caplog.at_level("DEBUG"):
        result = await protocol._receive_file()

    assert any("other than a blockmessage" in r.message for r in caplog.records)
    assert result == "data"


@pytest.mark.asyncio
async def test_wait_for_ack_cancels_pending_tasks() -> None:
    """Test that pending tasks are properly cancelled in _wait_for_ack to avoid warnings."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Track tasks created during _wait_for_ack
    created_tasks: list[asyncio.Task[Any]] = []
    original_create_task = asyncio.create_task

    def track_create_task(coro: Any) -> asyncio.Task[Any]:
        task: asyncio.Task[Any] = original_create_task(coro)
        created_tasks.append(task)
        return task

    # Queue up an ACK message
    ack_msg = OmniLogicMessage(42, MessageType.ACK)
    await protocol.data_queue.put(ack_msg)

    # Patch create_task to track tasks
    with patch("asyncio.create_task", side_effect=track_create_task):
        await protocol._wait_for_ack(42)

    # Give the event loop a chance to process cancellation
    await asyncio.sleep(0)

    # Should have created 2 tasks (data_task and error_task)
    assert len(created_tasks) == 2

    # One should be done (the data_task that got the ACK)
    # One should be cancelled (the error_task that was waiting)
    done_tasks = [t for t in created_tasks if t.done() and not t.cancelled()]
    cancelled_tasks = [t for t in created_tasks if t.cancelled()]

    assert len(done_tasks) == 1, "Expected exactly one task to complete normally"
    assert len(cancelled_tasks) == 1, "Expected exactly one task to be cancelled"
