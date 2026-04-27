"""Asyncio UDP datagram protocol for communication with the OmniLogic controller."""

from __future__ import annotations

import asyncio
import logging
import random
import xml.etree.ElementTree as ET
import zlib
from typing import cast

from pyomnilogic_local.models.leadmessage import LeadMessage
from pyomnilogic_local.omnitypes import MessageType

from .constants import (
    ACK_WAIT_TIMEOUT,
    BLOCK_MESSAGE_HEADER_OFFSET,
    DEFAULT_RESPONSE_TIMEOUT,
    MAX_FRAGMENT_WAIT_TIME,
    MAX_QUEUE_SIZE,
    OMNI_RETRANSMIT_COUNT,
    XML_NAMESPACE,
)
from .exceptions import OmniConnectionError, OmniMessageFormatError, OmniTimeoutError
from .message import OmniLogicMessage

_LOGGER = logging.getLogger(__name__)

_ACK_PAYLOAD = f'<Request xmlns="{XML_NAMESPACE}">\n<Name>Ack</Name>\n</Request>'

_ACK_TYPES = frozenset({MessageType.ACK, MessageType.XML_ACK})

# Type alias for items placed on the receive queue: either a parsed message or a parse error.
_QueueItem = OmniLogicMessage | OmniMessageFormatError


class OmniLogicProtocol(asyncio.DatagramProtocol):
    """Asyncio UDP datagram protocol for communication with the OmniLogic controller.

    Handles message framing, acknowledgement, retransmission, and multi-part
    response reassembly for the Hayward OmniLogic local UDP protocol.

    Example:
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            OmniLogicProtocol, remote_addr=(controller_ip, controller_port)
        )
        try:
            response = await protocol.async_send_and_receive(MessageType.GET_TELEMETRY, xml_body)
        finally:
            transport.close()
    """

    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        # Seed with a random value so each protocol instance (one per API call) uses distinct IDs.
        # Message ID is an unsigned 32-bit integer in the wire format, so cap at 2**16 to
        # leave room for plenty of increments.
        self._msg_counter: int = random.randint(1, 2**16)
        self._ack_futures: dict[int, asyncio.Future[OmniLogicMessage]] = {}
        self._receive_queue: asyncio.Queue[_QueueItem] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

    # -------------------------------------------------------------------------
    # asyncio.DatagramProtocol callbacks
    # -------------------------------------------------------------------------

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = cast("asyncio.DatagramTransport", transport)
        _LOGGER.debug("connection established")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            msg = OmniLogicMessage.from_bytes(data)
        except OmniMessageFormatError as exc:
            _LOGGER.warning("received unparsable datagram from %s: %s", addr, exc)
            self._receive_queue.put_nowait(exc)
            return

        _LOGGER.debug("received from %s: %r", addr, msg)

        if msg.type in _ACK_TYPES:
            self._resolve_ack(msg)
        else:
            self._send_xml_ack(msg.id)
            self._receive_queue.put_nowait(msg)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.error("transport error: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        _LOGGER.debug("connection lost: %s", exc)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _next_msg_id(self) -> int:
        """Return the next sequential message ID."""
        self._msg_counter += 1
        return self._msg_counter

    def _resolve_ack(self, msg: OmniLogicMessage) -> None:
        """Resolve the pending ACK future for the given message ID."""
        future = self._ack_futures.get(msg.id)
        if future is not None and not future.done():
            future.set_result(msg)

    def _send_xml_ack(self, msg_id: int) -> None:
        """Transmit an XML_ACK for a received message."""
        if self._transport is None:
            _LOGGER.warning("cannot send ACK for ID %d, transport unavailable", msg_id)
            return
        ack = OmniLogicMessage(msg_id=msg_id, msg_type=MessageType.XML_ACK, payload=_ACK_PAYLOAD)
        self._transport.sendto(bytes(ack))
        _LOGGER.debug("sent XML_ACK for message ID %d", msg_id)

    def _build_request(self, msg_type: MessageType, payload: str) -> OmniLogicMessage:
        """Build a new outgoing request message with a fresh ID."""
        return OmniLogicMessage(msg_id=self._next_msg_id(), msg_type=msg_type, payload=payload)

    async def _send_with_retry(self, msg_type: MessageType, payload: str) -> None:
        """Transmit a message and wait for acknowledgement, retransmitting as needed.

        A fresh message ID is used on each attempt so the controller treats every
        retransmission as a new request (an ACK only confirms receipt/parse, not
        that the controller will act on or re-respond to the same ID again).

        Args:
            msg_type: The type of message to send.
            payload: The XML payload string.

        Raises:
            OmniConnectionError: If the transport is not available.
            OmniTimeoutError: If no ACK is received after all retransmission attempts.
        """
        if self._transport is None:
            msg = f"Cannot send message type {msg_type.name}, transport not available"
            raise OmniConnectionError(msg)

        loop = asyncio.get_running_loop()

        for attempt in range(OMNI_RETRANSMIT_COUNT + 1):
            message = self._build_request(msg_type, payload)
            ack_future: asyncio.Future[OmniLogicMessage] = loop.create_future()
            self._ack_futures[message.id] = ack_future

            try:
                _LOGGER.debug(
                    "transmitting message ID: %d, type: %s (attempt %d/%d)",
                    message.id,
                    message.type.name,
                    attempt + 1,
                    OMNI_RETRANSMIT_COUNT + 1,
                )
                self._transport.sendto(bytes(message))
                try:
                    await asyncio.wait_for(asyncio.shield(ack_future), timeout=ACK_WAIT_TIMEOUT)
                except TimeoutError:
                    if attempt < OMNI_RETRANSMIT_COUNT:
                        _LOGGER.debug("no ACK for message ID %d, will retry", message.id)
                else:
                    return
            finally:
                self._ack_futures.pop(message.id, None)
                if not ack_future.done():
                    ack_future.cancel()

        msg = f"No ACK received for message type {msg_type.name} after {OMNI_RETRANSMIT_COUNT + 1} attempts"
        raise OmniTimeoutError(msg)

    async def _receive_next_message(self) -> OmniLogicMessage:
        """Wait for and return the next incoming (non-ACK) message from the queue.

        Raises:
            OmniTimeoutError: If no message arrives within MAX_FRAGMENT_WAIT_TIME seconds.
            OmniMessageFormatError: If the queued item is a parse error.
        """
        try:
            async with asyncio.timeout(MAX_FRAGMENT_WAIT_TIME):
                item: _QueueItem = await self._receive_queue.get()
        except TimeoutError as exc:
            msg = "Timed out waiting for response message from controller"
            raise OmniTimeoutError(msg) from exc

        if isinstance(item, OmniMessageFormatError):
            raise item

        return item

    # -------------------------------------------------------------------------
    # Response assembly
    # -------------------------------------------------------------------------

    async def _receive_response(self) -> tuple[bytes, bool]:
        """Receive and return the full response payload for a prior request.

        Handles both single-message responses and multi-part lead/block responses.

        Returns:
            Tuple of (raw_payload_bytes, compressed_flag).
        """
        while True:
            msg = await self._receive_next_message()

            if msg.type == MessageType.MSP_LEADMESSAGE:
                return await self._reassemble_multipart(msg)

            if msg.type == MessageType.MSP_BLOCKMESSAGE:
                _LOGGER.warning("received block message ID %d before any lead message, ignoring", msg.id)
                continue

            return msg.payload, msg.compressed

    async def _reassemble_multipart(self, lead_msg: OmniLogicMessage) -> tuple[bytes, bool]:
        """Reassemble a multi-part response from a lead message and its block messages.

        Args:
            lead_msg: The initial MSP_LEADMESSAGE received from the controller.

        Returns:
            Tuple of (concatenated_block_payload_bytes, compressed_flag).
        """
        lead = self._parse_lead_message(lead_msg)
        compressed = lead_msg.compressed
        seen_lead_ids: set[int] = {lead_msg.id}

        _LOGGER.debug(
            "reassembling %d-block response (compressed=%s)",
            lead.msg_block_count,
            compressed,
        )

        payload_data = b""
        received_block_count = 0
        seen_block_ids: set[int] = set()

        while received_block_count < lead.msg_block_count:
            msg = await self._receive_next_message()

            if msg.type == MessageType.MSP_LEADMESSAGE:
                if msg.id not in seen_lead_ids:
                    _LOGGER.warning("received unexpected secondary lead message ID %d", msg.id)
                    seen_lead_ids.add(msg.id)
                else:
                    _LOGGER.debug("received duplicate lead message ID %d, re-ACK already sent", msg.id)
                continue

            if msg.type != MessageType.MSP_BLOCKMESSAGE:
                _LOGGER.warning("expected block message but got %s (ID %d), ignoring", msg.type.name, msg.id)
                continue

            if msg.id in seen_block_ids:
                _LOGGER.debug("received duplicate block message ID %d, re-ACK already sent", msg.id)
                continue

            seen_block_ids.add(msg.id)
            payload_data += msg.payload[BLOCK_MESSAGE_HEADER_OFFSET:]
            received_block_count += 1
            _LOGGER.debug("received block %d/%d", received_block_count, lead.msg_block_count)

        return payload_data, compressed

    def _parse_lead_message(self, msg: OmniLogicMessage) -> LeadMessage:
        """Parse the XML payload of an MSP_LEADMESSAGE into a LeadMessage model.

        Args:
            msg: The MSP_LEADMESSAGE to parse.

        Returns:
            Parsed LeadMessage model.
        """
        payload_str = msg.payload.decode("utf-8").strip("\x00")
        root = ET.fromstring(payload_str)
        return LeadMessage.model_validate(root)

    def _decode_payload(self, data: bytes, compressed: bool) -> str:
        """Decode a raw response payload, decompressing if necessary.

        Args:
            data: Raw payload bytes.
            compressed: Whether the payload is zlib-compressed.

        Returns:
            Decoded UTF-8 string with leading/trailing null bytes stripped.
        """
        if compressed:
            data = zlib.decompress(data.rstrip(b"\x00"))
        return data.decode("utf-8").strip("\x00")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def async_send(self, msg_type: MessageType, payload: str) -> None:
        """Send a message to the controller and wait for acknowledgement.

        The message is retransmitted up to OMNI_RETRANSMIT_COUNT times if no ACK
        is received within ACK_WAIT_TIMEOUT seconds.

        Args:
            msg_type: The type of message to send.
            payload: The XML payload string.

        Raises:
            OmniConnectionError: If the transport is not available.
            OmniTimeoutError: If no ACK is received after all retransmission attempts.
        """
        await self._send_with_retry(msg_type, payload)

    async def async_send_and_receive(self, msg_type: MessageType, payload: str) -> str:
        """Send a message and receive the controller's response payload.

        Handles the full send → ACK → response (single or lead/block) flow,
        including retransmission on ACK timeout and decompression of compressed
        responses. If an ACK is received but the controller never sends the
        expected follow-up response within DEFAULT_RESPONSE_TIMEOUT, the entire
        send+receive cycle is retried up to OMNI_RETRANSMIT_COUNT times.

        Args:
            msg_type: The type of message to send.
            payload: The XML payload string.

        Returns:
            The decoded UTF-8 response string from the controller.

        Raises:
            OmniConnectionError: If the transport is not available.
            OmniTimeoutError: If no ACK or response is received within the allowed time.
            OmniMessageFormatError: If an unparsable response datagram is received.
        """
        for attempt in range(OMNI_RETRANSMIT_COUNT + 1):
            await self._send_with_retry(msg_type, payload)
            try:
                async with asyncio.timeout(DEFAULT_RESPONSE_TIMEOUT):
                    raw_data, compressed = await self._receive_response()
                return self._decode_payload(raw_data, compressed)
            except TimeoutError:
                if attempt < OMNI_RETRANSMIT_COUNT:
                    _LOGGER.debug(
                        "no response received for %s within %ds, retrying (attempt %d/%d)",
                        msg_type.name,
                        DEFAULT_RESPONSE_TIMEOUT,
                        attempt + 1,
                        OMNI_RETRANSMIT_COUNT + 1,
                    )

        msg = f"No response received for {msg_type.name} after {OMNI_RETRANSMIT_COUNT + 1} attempts"
        raise OmniTimeoutError(msg)
