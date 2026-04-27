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
from unittest.mock import AsyncMock, MagicMock, patch
from xml.etree import ElementTree as ET

import pytest

from pyomnilogic_local.api.constants import OMNI_RETRANSMIT_COUNT
from pyomnilogic_local.api.exceptions import OmniMessageFormatError, OmniTimeoutError
from pyomnilogic_local.api.message import OmniLogicMessage
from pyomnilogic_local.api.protocol import OmniLogicProtocol
from pyomnilogic_local.omnitypes import ClientType, MessageType

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


def test_message_from_bytes_errors(subtests: pytest.Subtests) -> None:
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
    assert protocol._receive_queue.maxsize == 100


def test_protocol_connection_made() -> None:
    """Test that connection_made sets the transport."""
    protocol = OmniLogicProtocol()
    mock_transport = MagicMock()

    protocol.connection_made(mock_transport)

    assert protocol._transport is mock_transport


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
    # ACK/XML_ACK messages resolve futures, not the queue; use a non-ACK type
    valid_data = bytes(OmniLogicMessage(123, MessageType.MSP_CONFIGURATIONUPDATE))

    protocol.datagram_received(valid_data, ("127.0.0.1", 12345))

    assert protocol._receive_queue.qsize() == 1
    message = protocol._receive_queue.get_nowait()
    assert isinstance(message, OmniLogicMessage)
    assert message.id == 123
    assert message.type == MessageType.MSP_CONFIGURATIONUPDATE


def test_datagram_received_with_corrupt_data(caplog: pytest.LogCaptureFixture) -> None:
    """Test that corrupt datagram data is handled gracefully and logged."""
    protocol = OmniLogicProtocol()
    corrupt_data = b"short"

    with caplog.at_level("WARNING"):
        protocol.datagram_received(corrupt_data, ("127.0.0.1", 12345))

    assert any("received unparsable datagram" in r.message for r in caplog.records)
    # The parse error is placed on the receive queue as an OmniMessageFormatError
    assert protocol._receive_queue.qsize() == 1
    assert isinstance(protocol._receive_queue.get_nowait(), OmniMessageFormatError)


def test_datagram_received_queue_overflow() -> None:
    """Test that QueueFull is raised when the receive queue is full."""
    protocol = OmniLogicProtocol()
    protocol._receive_queue = asyncio.Queue(maxsize=1)
    # ACKs resolve futures, not the queue; fill with a non-ACK message
    protocol._receive_queue.put_nowait(OmniLogicMessage(1, MessageType.MSP_CONFIGURATIONUPDATE))

    valid_data = bytes(OmniLogicMessage(2, MessageType.MSP_CONFIGURATIONUPDATE))
    with pytest.raises(asyncio.QueueFull):
        protocol.datagram_received(valid_data, ("127.0.0.1", 12345))


def test_datagram_received_unexpected_exception() -> None:
    """Test that unexpected exceptions during datagram processing propagate to the caller."""
    protocol = OmniLogicProtocol()

    # Only OmniMessageFormatError is caught; any other exception propagates unhandled
    with (
        patch("pyomnilogic_local.api.protocol.OmniLogicMessage.from_bytes", side_effect=RuntimeError("Unexpected")),
        pytest.raises(RuntimeError, match="Unexpected"),
    ):
        protocol.datagram_received(b"data", ("127.0.0.1", 12345))


def test_error_received(caplog: pytest.LogCaptureFixture) -> None:
    """Test that error_received logs transport errors."""
    protocol = OmniLogicProtocol()
    test_error = RuntimeError("UDP error")

    with caplog.at_level("ERROR"):
        protocol.error_received(test_error)

    assert any("transport error" in r.message for r in caplog.records)


# ============================================================================
# _wait_for_ack Tests
# ============================================================================


@pytest.mark.asyncio
async def test_wait_for_ack_success() -> None:
    """Test that an ACK for the correct ID resolves the pending future."""
    loop = asyncio.get_running_loop()
    protocol = OmniLogicProtocol()

    ack_future: asyncio.Future[OmniLogicMessage] = loop.create_future()
    protocol._ack_futures[123] = ack_future

    ack_message = OmniLogicMessage(123, MessageType.ACK)
    protocol._resolve_ack(ack_message)

    assert ack_future.done()
    assert ack_future.result() is ack_message


@pytest.mark.asyncio
async def test_wait_for_ack_wrong_id_continues_waiting() -> None:
    """Test that an ACK for a different ID does not resolve the pending future."""
    loop = asyncio.get_running_loop()
    protocol = OmniLogicProtocol()

    ack_future: asyncio.Future[OmniLogicMessage] = loop.create_future()
    protocol._ack_futures[123] = ack_future

    wrong_ack = OmniLogicMessage(999, MessageType.ACK)
    protocol._resolve_ack(wrong_ack)

    assert not ack_future.done()


@pytest.mark.asyncio
async def test_wait_for_ack_leadmessage_instead() -> None:
    """Test that a LeadMessage with a matching ID goes to the receive queue, not the ACK future."""
    loop = asyncio.get_running_loop()
    protocol = OmniLogicProtocol()

    ack_future: asyncio.Future[OmniLogicMessage] = loop.create_future()
    protocol._ack_futures[123] = ack_future

    # Build a valid LeadMessage datagram and deliver it via datagram_received
    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api">'
        "<Name>LeadMessage</Name><Parameters>"
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter>'
        '<Parameter name="MsgSize" dataType="int">10</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">1</Parameter>'
        '<Parameter name="Type" dataType="int">0</Parameter>'
        "</Parameters></Response>"
    )
    leadmsg = OmniLogicMessage(123, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)
    protocol.datagram_received(bytes(leadmsg), ("127.0.0.1", 12345))

    # LeadMessages are not ACKs — the future should remain unresolved
    assert not ack_future.done()
    # The LeadMessage is placed on the receive queue for response assembly
    assert protocol._receive_queue.qsize() == 1


@pytest.mark.asyncio
async def test_wait_for_ack_leadmessage_wrong_id() -> None:
    """Test that a LeadMessage with a different ID also goes to the receive queue, not the ACK future."""
    loop = asyncio.get_running_loop()
    protocol = OmniLogicProtocol()

    ack_future: asyncio.Future[OmniLogicMessage] = loop.create_future()
    protocol._ack_futures[123] = ack_future

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api">'
        "<Name>LeadMessage</Name><Parameters>"
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter>'
        '<Parameter name="MsgSize" dataType="int">10</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">1</Parameter>'
        '<Parameter name="Type" dataType="int">0</Parameter>'
        "</Parameters></Response>"
    )
    leadmsg = OmniLogicMessage(999, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)
    protocol.datagram_received(bytes(leadmsg), ("127.0.0.1", 12345))

    # Future for ID 123 should remain unresolved
    assert not ack_future.done()
    # The LeadMessage goes to the receive queue regardless of ID
    assert protocol._receive_queue.qsize() == 1


@pytest.mark.asyncio
async def test_wait_for_ack_error_in_queue() -> None:
    """Test that _send_with_retry raises OmniTimeoutError when no ACK is received."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    # Patch wait_for to always raise TimeoutError so every attempt times out immediately
    with patch("asyncio.wait_for", side_effect=TimeoutError), pytest.raises(OmniTimeoutError):
        await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")


# ============================================================================
# _ensure_sent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ensure_sent_ack_message() -> None:
    """Test that _send_xml_ack transmits directly without waiting for an ACK."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    protocol._send_xml_ack(123)

    protocol._transport.sendto.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_sent_xml_ack_message() -> None:
    """Test that _send_xml_ack sends the correct XML_ACK message format."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    protocol._send_xml_ack(456)

    protocol._transport.sendto.assert_called_once()
    sent_bytes = protocol._transport.sendto.call_args[0][0]
    # Verify the sent bytes parse back to an XML_ACK message with the correct ID
    parsed = OmniLogicMessage.from_bytes(sent_bytes)
    assert parsed.type == MessageType.XML_ACK
    assert parsed.id == 456


@pytest.mark.asyncio
async def test_ensure_sent_success_first_attempt() -> None:
    """Test successful send on first attempt with _send_with_retry."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    # Simulate an immediate ACK by resolving the future when sendto is called
    def resolve_ack_on_send(data: bytes) -> None:
        msg = OmniLogicMessage.from_bytes(data)
        protocol._resolve_ack(OmniLogicMessage(msg.id, MessageType.ACK))

    protocol._transport.sendto.side_effect = resolve_ack_on_send

    await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    protocol._transport.sendto.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_sent_timeout_and_retry_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Test that _send_with_retry logs retries and raises OmniTimeoutError after all attempts."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    with patch("asyncio.wait_for", side_effect=TimeoutError), caplog.at_level("DEBUG"), pytest.raises(OmniTimeoutError):
        await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    retry_logs = [r for r in caplog.records if "no ACK" in r.message]
    assert len(retry_logs) == OMNI_RETRANSMIT_COUNT
    assert protocol._transport.sendto.call_count == OMNI_RETRANSMIT_COUNT + 1


# ============================================================================
# send_message and send_and_receive Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_message_generates_random_id() -> None:
    """Test that _send_with_retry generates a non-zero message ID."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    captured_ids: list[int] = []

    def capture_id(data: bytes) -> None:
        msg = OmniLogicMessage.from_bytes(data)
        captured_ids.append(msg.id)
        protocol._resolve_ack(OmniLogicMessage(msg.id, MessageType.ACK))

    protocol._transport.sendto.side_effect = capture_id

    await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    assert len(captured_ids) == 1
    assert captured_ids[0] != 0


@pytest.mark.asyncio
async def test_send_message_uses_incrementing_id() -> None:
    """Test that each _send_with_retry call uses a distinct, incrementing message ID."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    captured_ids: list[int] = []

    def capture_and_ack(data: bytes) -> None:
        msg = OmniLogicMessage.from_bytes(data)
        captured_ids.append(msg.id)
        protocol._resolve_ack(OmniLogicMessage(msg.id, MessageType.ACK))

    protocol._transport.sendto.side_effect = capture_and_ack

    await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")
    await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    assert len(captured_ids) == 2
    assert captured_ids[0] != captured_ids[1]


@pytest.mark.asyncio
async def test_send_and_receive() -> None:
    """Test async_send_and_receive calls _send_with_retry and _receive_response."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    with (
        patch.object(protocol, "_send_with_retry", new_callable=AsyncMock) as mock_send,
        patch.object(protocol, "_receive_response", new_callable=AsyncMock) as mock_receive,
        patch.object(protocol, "_decode_payload", return_value="test response"),
    ):
        mock_receive.return_value = (b"raw", False)

        result = await protocol.async_send_and_receive(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    mock_send.assert_called_once_with(MessageType.REQUEST_CONFIGURATION, "<payload/>")
    mock_receive.assert_called_once()
    assert result == "test response"


# ============================================================================
# _send_ack Tests
# ============================================================================


@pytest.mark.asyncio
async def test_send_ack_generates_xml() -> None:
    """Test that _send_xml_ack transmits a well-formed XML_ACK message."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    protocol._send_xml_ack(12345)

    protocol._transport.sendto.assert_called_once()
    sent_bytes = protocol._transport.sendto.call_args[0][0]

    parsed = OmniLogicMessage.from_bytes(sent_bytes)
    assert parsed.type == MessageType.XML_ACK
    assert parsed.id == 12345

    # Verify XML structure contains the expected Ack name element
    xml_payload = parsed.payload.rstrip(b"\x00").decode("utf-8")
    root = ET.fromstring(xml_payload)
    name_elem = root.find(".//{http://nextgen.hayward.com/api}Name")
    assert name_elem is not None
    assert name_elem.text == "Ack"


# ============================================================================
# _receive_file Tests - Simple Response
# ============================================================================


@pytest.mark.asyncio
async def test_receive_file_simple_response() -> None:
    """Test receiving a simple (non-fragmented) response via _receive_response."""
    protocol = OmniLogicProtocol()

    response_msg = OmniLogicMessage(123, MessageType.MSP_TELEMETRY_UPDATE)
    response_msg.payload = b"<telemetry/>"
    response_msg.compressed = False
    await protocol._receive_queue.put(response_msg)

    raw_data, compressed = await protocol._receive_response()

    assert raw_data == b"<telemetry/>"
    assert compressed is False


@pytest.mark.asyncio
async def test_receive_file_skips_duplicate_acks(caplog: pytest.LogCaptureFixture) -> None:
    """Test that orphaned block messages are skipped and the real response is returned."""
    protocol = OmniLogicProtocol()

    # Stray block message (no preceding lead message) should be skipped
    stray_block = OmniLogicMessage(111, MessageType.MSP_BLOCKMESSAGE)
    stray_block.payload = b"\x00" * 8 + b"stray"
    response = OmniLogicMessage(333, MessageType.MSP_CONFIGURATIONUPDATE)
    response.payload = b"<data/>"
    response.compressed = False

    await protocol._receive_queue.put(stray_block)
    await protocol._receive_queue.put(response)

    with caplog.at_level("WARNING"):
        raw_data, _compressed = await protocol._receive_response()

    assert any("block message" in r.message for r in caplog.records)
    assert raw_data == b"<data/>"


@pytest.mark.asyncio
async def test_receive_file_decompresses_data() -> None:
    """Test that _decode_payload decompresses compressed responses."""
    protocol = OmniLogicProtocol()

    original = b"This is test data that will be compressed"
    compressed_data = zlib.compress(original)

    result = protocol._decode_payload(compressed_data, compressed=True)

    assert result == original.decode("utf-8")


@pytest.mark.asyncio
async def test_receive_file_decompression_error() -> None:
    """Test that _decode_payload raises OmniMessageFormatError for invalid compressed data."""
    protocol = OmniLogicProtocol()

    with pytest.raises(zlib.error):
        protocol._decode_payload(b"invalid compressed data", compressed=True)


# ============================================================================
# _receive_file Tests - Fragmented Response
# ============================================================================


@pytest.mark.asyncio
async def test_receive_file_fragmented_response() -> None:
    """Test receiving a fragmented response with LeadMessage and BlockMessages via _receive_response."""
    protocol = OmniLogicProtocol()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">24</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">2</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"first_part"

    block2 = OmniLogicMessage(102, MessageType.MSP_BLOCKMESSAGE)
    block2.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"second_part"

    await protocol._receive_queue.put(leadmsg)
    await protocol._receive_queue.put(block1)
    await protocol._receive_queue.put(block2)

    raw_data, compressed = await protocol._receive_response()

    assert raw_data == b"first_partsecond_part"
    assert compressed is False


@pytest.mark.asyncio
async def test_receive_file_fragmented_out_of_order() -> None:
    """Test that fragments are concatenated in receive order."""
    protocol = OmniLogicProtocol()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">30</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">3</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    # Enqueue blocks out of ID order: 102, 100, 101
    block2 = OmniLogicMessage(102, MessageType.MSP_BLOCKMESSAGE)
    block2.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"third"

    block0 = OmniLogicMessage(100, MessageType.MSP_BLOCKMESSAGE)
    block0.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"first"

    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"second"

    await protocol._receive_queue.put(leadmsg)
    await protocol._receive_queue.put(block2)
    await protocol._receive_queue.put(block0)
    await protocol._receive_queue.put(block1)

    raw_data, _compressed = await protocol._receive_response()

    # Blocks are assembled in receive order, not by ID
    assert raw_data == b"thirdfirstsecond"


@pytest.mark.asyncio
async def test_receive_file_fragmented_invalid_leadmessage() -> None:
    """Test that invalid LeadMessage XML raises a parse error."""
    protocol = OmniLogicProtocol()

    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload="invalid xml")
    await protocol._receive_queue.put(leadmsg)

    with pytest.raises(ET.ParseError):
        await protocol._receive_response()


@pytest.mark.asyncio
async def test_receive_file_fragmented_timeout_waiting() -> None:
    """Test that OmniTimeoutError is raised when no fragment arrives within the timeout."""
    protocol = OmniLogicProtocol()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">24</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">2</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)
    await protocol._receive_queue.put(leadmsg)
    # No block messages — _receive_next_message will time out

    with pytest.raises(OmniTimeoutError):
        await protocol._receive_response()


@pytest.mark.asyncio
async def test_receive_file_fragmented_max_wait_time_exceeded() -> None:
    """Test that _receive_next_message raises OmniTimeoutError when MAX_FRAGMENT_WAIT_TIME elapses."""
    protocol = OmniLogicProtocol()

    # Patch asyncio.timeout to raise TimeoutError immediately, simulating the deadline being exceeded
    with patch("asyncio.timeout", side_effect=TimeoutError), pytest.raises(OmniTimeoutError):
        await protocol._receive_next_message()


@pytest.mark.asyncio
async def test_receive_file_fragmented_ignores_non_block_messages(caplog: pytest.LogCaptureFixture) -> None:
    """Test that non-BlockMessages during fragment reassembly are warned and ignored."""
    protocol = OmniLogicProtocol()

    leadmsg_payload = (
        '<?xml version="1.0" encoding="UTF-8" ?><Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        '<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">10</Parameter>'
        '<Parameter name="MsgBlockCount" dataType="int">1</Parameter><Parameter name="Type" dataType="int">0</Parameter></Parameters>'
        "</Response>"
    )
    leadmsg = OmniLogicMessage(100, MessageType.MSP_LEADMESSAGE, payload=leadmsg_payload)

    # A configuration update message (not a block) should be skipped during reassembly
    interloper = OmniLogicMessage(999, MessageType.MSP_CONFIGURATIONUPDATE)
    interloper.payload = b"<config/>"

    block1 = OmniLogicMessage(101, MessageType.MSP_BLOCKMESSAGE)
    block1.payload = b"\x00\x00\x00\x00\x00\x00\x00\x00" + b"data"

    await protocol._receive_queue.put(leadmsg)
    await protocol._receive_queue.put(interloper)
    await protocol._receive_queue.put(block1)

    with caplog.at_level("WARNING"):
        raw_data, _compressed = await protocol._receive_response()

    assert any("expected block message" in r.message for r in caplog.records)
    assert raw_data == b"data"


@pytest.mark.asyncio
async def test_wait_for_ack_cancels_pending_tasks() -> None:
    """Test that _ack_futures are cleaned up after _send_with_retry completes."""
    protocol = OmniLogicProtocol()
    protocol._transport = MagicMock()

    def resolve_ack_on_send(data: bytes) -> None:
        msg = OmniLogicMessage.from_bytes(data)
        protocol._resolve_ack(OmniLogicMessage(msg.id, MessageType.ACK))

    protocol._transport.sendto.side_effect = resolve_ack_on_send

    await protocol._send_with_retry(MessageType.REQUEST_CONFIGURATION, "<payload/>")

    # After a successful send, all futures should be cleaned up from _ack_futures
    assert len(protocol._ack_futures) == 0
