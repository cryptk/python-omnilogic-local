import asyncio
from unittest.mock import MagicMock, patch

import pytest

from pyomnilogic_local.exceptions import OmniTimeoutException
from pyomnilogic_local.omnitypes import ClientType, MessageType
from pyomnilogic_local.protocol import OmniLogicMessage, OmniLogicProtocol


def test_parse_basic_ack() -> None:
    """Validate that we can parse a basic ACK packet"""
    bytes_ack = b"\x99_\xd1l\x00\x00\x00\x00dv\x8f\xc11.20\x00\x00\x03\xea\x03\x00\x00\x00"
    message = OmniLogicMessage.from_bytes(bytes_ack)
    assert message.id == 2573193580
    assert message.type is MessageType.ACK
    assert message.compressed is False
    assert str(message) == "ID: 2573193580, Type: ACK, Compressed: False, Client: OMNI, Body: "


def test_create_basic_ack() -> None:
    """Validate that we can create a valid basic ACK packet"""
    bytes_ack = b"\x99_\xd1l\x00\x00\x00\x00dv\x8f\xc11.20\x00\x00\x03\xea\x03\x00\x00\x00"
    message = OmniLogicMessage(2573193580, MessageType.ACK, payload=None, version="1.20")
    message.client_type = ClientType.OMNI
    message.timestamp = 1685491649
    assert bytes(message) == bytes_ack


def test_parse_leadmessate() -> None:
    """Validate that we can parse an MSP LeadMessage."""
    bytes_leadmessage = (
        b'\x00\x00\x90v\x00\x00\x00\x00dv\x92\xc11.20\x00\x00\x07\xce\x03\x00\x01\x00<?xml version="1.0" encoding="UTF-8" ?>'
        b'<Response xmlns="http://nextgen.hayward.com/api"><Name>LeadMessage</Name><Parameters>'
        b'<Parameter name="SourceOpId" dataType="int">1003</Parameter><Parameter name="MsgSize" dataType="int">3361</Parameter>'
        b'<Parameter name="MsgBlockCount" dataType="int">4</Parameter><Parameter name="Type" dataType="int">0</Parameter>'
        b"</Parameters></Response>\x00"
    )
    message = OmniLogicMessage.from_bytes(bytes_leadmessage)
    print(message.timestamp)
    assert message.id == 36982
    assert message.type is MessageType.MSP_LEADMESSAGE
    assert message.timestamp == 1685492417
    assert message.compressed is True
    assert str(message) == "ID: 36982, Type: MSP_LEADMESSAGE, Compressed: True, Client: OMNI"


def test_create_leadmessage() -> None:
    """Validate that we can create a valid MSP LeadMessage"""
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


def test_datagram_received_with_corrupt_data(caplog: pytest.LogCaptureFixture) -> None:
    """Test that corrupt datagram data is handled gracefully and logged."""
    protocol = OmniLogicProtocol()
    # Provide invalid/corrupt data (too short for header)
    corrupt_data = b"short"
    with caplog.at_level("ERROR"):
        protocol.datagram_received(corrupt_data, ("127.0.0.1", 12345))
    assert any("Failed to parse incoming datagram" in r.message for r in caplog.records)


def test_datagram_received_queue_overflow(caplog: pytest.LogCaptureFixture) -> None:
    """Test that queue overflow is handled and logged."""
    protocol = OmniLogicProtocol()
    # Fill the queue to capacity
    protocol.data_queue = asyncio.Queue(maxsize=1)
    protocol.data_queue.put_nowait(OmniLogicMessage(1, MessageType.ACK))
    # Now send another valid message
    valid_data = bytes(OmniLogicMessage(2, MessageType.ACK))
    with caplog.at_level("ERROR"):
        protocol.datagram_received(valid_data, ("127.0.0.1", 12345))
    assert any("Data queue is full" in r.message for r in caplog.records)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_ensure_sent_timeout_and_retry_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Test that _ensure_sent logs retries and raises on repeated timeout."""
    protocol = OmniLogicProtocol()
    protocol.transport = MagicMock()

    # Patch _wait_for_ack to always timeout using patch.object
    async def always_timeout(*args: object, **kwargs: object) -> None:
        await asyncio.sleep(0)
        raise TimeoutError()

    message = OmniLogicMessage(123, MessageType.REQUEST_CONFIGURATION)
    with patch.object(protocol, "_wait_for_ack", always_timeout):
        with caplog.at_level("WARNING"):
            with pytest.raises(OmniTimeoutException):
                await protocol._ensure_sent(message, max_attempts=3)  # pylint: disable=protected-access
    # Should log retries and final error
    assert any("attempt 1/3" in r.message for r in caplog.records)
    assert any("attempt 2/3" in r.message for r in caplog.records)
    assert any("after 3 attempts" in r.message for r in caplog.records)
