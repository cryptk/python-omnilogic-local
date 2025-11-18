from __future__ import annotations

import asyncio
import logging
import random
import struct
import time
import xml.etree.ElementTree as ET
import zlib
from typing import Any, Self, cast

from pyomnilogic_local.models.leadmessage import LeadMessage
from pyomnilogic_local.omnitypes import ClientType, MessageType

from .constants import (
    ACK_WAIT_TIMEOUT,
    BLOCK_MESSAGE_HEADER_OFFSET,
    MAX_FRAGMENT_WAIT_TIME,
    MAX_QUEUE_SIZE,
    OMNI_RETRANSMIT_COUNT,
    OMNI_RETRANSMIT_TIME,
    PROTOCOL_HEADER_FORMAT,
    PROTOCOL_HEADER_SIZE,
    PROTOCOL_VERSION,
    XML_ENCODING,
    XML_NAMESPACE,
)
from .exceptions import (
    OmniFragmentationError,
    OmniMessageFormatError,
    OmniTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


class OmniLogicMessage:
    """A protocol message for communication with the OmniLogic controller.

    Handles serialization and deserialization of message headers and payloads.
    """

    header_format = PROTOCOL_HEADER_FORMAT
    id: int
    type: MessageType
    payload: bytes
    client_type: ClientType = ClientType.SIMPLE
    version: str = PROTOCOL_VERSION
    timestamp: int | None = int(time.time())
    reserved_1: int = 0
    compressed: bool = False
    reserved_2: int = 0

    def __init__(
        self,
        msg_id: int,
        msg_type: MessageType,
        payload: str | None = None,
        version: str = PROTOCOL_VERSION,
    ) -> None:
        """Initialize a new OmniLogicMessage.

        Args:
            msg_id: Unique message identifier.
            msg_type: Type of message being sent.
            payload: Optional string payload (XML or command body).
            version: Protocol version string.
        """
        self.id = msg_id
        self.type = msg_type
        # If we are speaking the XML API, it seems like we need client_type 0, otherwise we need client_type 1
        self.client_type = ClientType.XML if payload is not None else ClientType.SIMPLE
        # The Hayward API terminates it's messages with a null character
        payload = f"{payload}\x00" if payload is not None else ""
        self.payload = bytes(payload, "utf-8")

        self.version = version

    def __bytes__(self) -> bytes:
        """Serialize the message to bytes for UDP transmission.

        Returns:
            Byte representation of the message.
        """
        header = struct.pack(
            self.header_format,
            self.id,  # Msg id
            self.timestamp,
            bytes(self.version, "ascii"),  # version string
            self.type.value,  # OpID/msgType
            self.client_type.value,  # Client type
            0,  # reserved
            self.compressed,  # compressed
            0,  # reserved
        )
        return header + self.payload

    def __repr__(self) -> str:
        """Return a string representation of the message for debugging."""
        if self.compressed or self.type is MessageType.MSP_BLOCKMESSAGE:
            return f"ID: {self.id}, Type: {self.type.name}, Compressed: {self.compressed}, Client: {self.client_type.name}"
        return (
            f"ID: {self.id}, Type: {self.type.name}, Compressed: {self.compressed}, Client: {self.client_type.name}, "
            f"Body: {self.payload[:-1].decode('utf-8')}"
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """Parse a message from its byte representation.

        Args:
            data: Byte data received from the controller.

        Returns:
            OmniLogicMessage instance.

        Raises:
            OmniMessageFormatException: If the message format is invalid.
        """
        if len(data) < PROTOCOL_HEADER_SIZE:
            msg = f"Message too short: {len(data)} bytes, expected at least {PROTOCOL_HEADER_SIZE}"
            raise OmniMessageFormatError(msg)

        # split the header and data
        header = data[:PROTOCOL_HEADER_SIZE]
        rdata: bytes = data[PROTOCOL_HEADER_SIZE:]

        try:
            (msg_id, tstamp, vers, msg_type, client_type, res1, compressed, res2) = struct.unpack(cls.header_format, header)
        except struct.error as exc:
            msg = f"Failed to unpack message header: {exc}"
            raise OmniMessageFormatError(msg) from exc

        # Validate message type
        try:
            message_type_enum = MessageType(msg_type)
        except ValueError as exc:
            msg = f"Unknown message type: {msg_type}: {exc}"
            raise OmniMessageFormatError(msg) from exc

        # Validate client type
        try:
            client_type_enum = ClientType(int(client_type))
        except ValueError as exc:
            msg = f"Unknown client type: {client_type}: {exc}"
            raise OmniMessageFormatError(msg) from exc

        message = cls(msg_id=msg_id, msg_type=message_type_enum, version=vers.decode("utf-8"))
        message.timestamp = tstamp
        message.client_type = client_type_enum
        message.reserved_1 = res1
        # There are some messages that are ALWAYS compressed although they do not return a 1 in their LeadMessage
        message.compressed = compressed == 1 or message.type in [MessageType.MSP_TELEMETRY_UPDATE]
        message.reserved_2 = res2
        message.payload = rdata

        return message


class OmniLogicProtocol(asyncio.DatagramProtocol):
    """Asyncio DatagramProtocol implementation for OmniLogic UDP communication.

    Handles message sending, receiving, retries, and block message reassembly.
    """

    transport: asyncio.DatagramTransport
    # The omni will re-transmit a packet every 2 seconds if it does not receive an ACK.  We pad that just a touch to be safe
    _omni_retransmit_time = OMNI_RETRANSMIT_TIME
    # The omni will re-transmit 5 times (a total of 6 attempts including the initial) if it does not receive an ACK
    _omni_retransmit_count = OMNI_RETRANSMIT_COUNT

    data_queue: asyncio.Queue[OmniLogicMessage]
    error_queue: asyncio.Queue[Exception]

    def __init__(self) -> None:
        """Initialize the protocol handler and message queue."""
        self.data_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self.error_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Called when a UDP connection is made."""
        self.transport = cast("asyncio.DatagramTransport", transport)

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the UDP connection is lost or closed."""
        if exc:
            raise exc

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        """Called when a datagram is received from the controller.

        Parses the message and puts it on the queue. Handles corrupt or unexpected data gracefully.
        """
        try:
            message = OmniLogicMessage.from_bytes(data)
            _LOGGER.debug("Received Message %s from %s", str(message), addr)
            try:
                self.data_queue.put_nowait(message)
            except asyncio.QueueFull:
                _LOGGER.exception("Data queue is full. Dropping message: %s", str(message))
        except OmniMessageFormatError as exc:
            _LOGGER.exception("Failed to parse incoming datagram from %s", addr)
            self.error_queue.put_nowait(exc)
        except Exception as exc:
            _LOGGER.exception("Unexpected error processing datagram from %s", addr)
            self.error_queue.put_nowait(exc)

    def error_received(self, exc: Exception) -> None:
        """Called when a UDP error is received.

        Store the error so it can be handled by awaiting coroutines.
        """
        self.error_queue.put_nowait(exc)

    async def _wait_for_ack(self, ack_id: int) -> None:
        """Wait for an ACK message with the given ID.

        Handles dropped or out-of-order ACKs.

        Args:
            ack_id: The message ID to wait for an ACK.

        Raises:
            OmniTimeoutException: If no ACK is received.
            Exception: If a protocol error occurs.
        """
        # Wait for either an ACK message or an error
        while True:
            # Wait for either a message or an error
            data_task = asyncio.create_task(self.data_queue.get())
            error_task = asyncio.create_task(self.error_queue.get())
            done, pending = await asyncio.wait([data_task, error_task], return_when=asyncio.FIRST_COMPLETED)

            # Cancel any pending tasks to avoid "Task was destroyed but it is pending" warnings
            for task in pending:
                task.cancel()

            if error_task in done:
                exc = error_task.result()
                if isinstance(exc, Exception):
                    raise exc
                _LOGGER.error("Unknown error occurred during communication with OmniLogic: %s", exc)
            if data_task in done:
                message = data_task.result()
                if message.id == ack_id:
                    _LOGGER.debug("Received ACK for message ID %s", ack_id)
                    return
                _LOGGER.debug("We received a message that is not our ACK, it appears the ACK was dropped")
                if message.type in {MessageType.MSP_LEADMESSAGE, MessageType.MSP_TELEMETRY_UPDATE}:
                    _LOGGER.debug("Omni has sent a new message, continuing on with the communication")
                    await self.data_queue.put(message)
                    return

    async def _ensure_sent(
        self,
        message: OmniLogicMessage,
        max_attempts: int = 5,
    ) -> None:
        """Send a message and ensure it is acknowledged, retrying if necessary.

        Args:
            message: The message to send.
            max_attempts: Maximum number of send attempts.

        Raises:
            OmniTimeoutException: If no ACK is received after retries.
        """
        for attempt in range(max_attempts):
            self.transport.sendto(bytes(message))
            _LOGGER.debug("Sent message ID %s (attempt %d/%d)", message.id, attempt + 1, max_attempts)

            # If the message that we just sent is an ACK, we do not need to wait to receive an ACK, we are done
            if message.type in [MessageType.XML_ACK, MessageType.ACK]:
                return

            # Wait for a bit to either receive an ACK for our message, otherwise, we retry delivery
            try:
                await asyncio.wait_for(self._wait_for_ack(message.id), ACK_WAIT_TIMEOUT)
            except TimeoutError as exc:
                if attempt < max_attempts - 1:
                    _LOGGER.warning(
                        "ACK not received for message type %s (ID: %s), attempt %d/%d. Retrying...",
                        message.type.name,
                        message.id,
                        attempt + 1,
                        max_attempts,
                    )
                else:
                    _LOGGER.exception(
                        "Failed to receive ACK for message type %s (ID: %s) after %d attempts.", message.type.name, message.id, max_attempts
                    )
                    msg = f"Failed to receive acknowledgement of command, max retries exceeded: {exc}"
                    raise OmniTimeoutError(msg) from exc
            else:
                return

    async def send_and_receive(
        self,
        msg_type: MessageType,
        payload: str | None,
        msg_id: int | None = None,
    ) -> str:
        """Send a message and wait for a response, returning the response payload as a string.

        Args:
            msg_type: Type of message to send.
            payload: Optional payload string.
            msg_id: Optional message ID.

        Returns:
            Response payload as a string.
        """
        await self.send_message(msg_type, payload, msg_id)
        return await self._receive_file()

    # Send a message that you do NOT need a response to
    async def send_message(
        self,
        msg_type: MessageType,
        payload: str | None,
        msg_id: int | None = None,
    ) -> None:
        """Send a message that does not require a response.

        Args:
            msg_type: Type of message to send.
            payload: Optional payload string.
            msg_id: Optional message ID.
        """
        # If we aren't sending a specific msg_id, lets randomize it
        if not msg_id:
            msg_id = random.randrange(2**32)

        message = OmniLogicMessage(msg_id, msg_type, payload)

        _LOGGER.debug("Sending Message %s", str(message))

        await self._ensure_sent(message)

    async def _send_ack(self, msg_id: int) -> None:
        """Send an ACK message for the given message ID."""
        body_element = ET.Element("Request", {"xmlns": XML_NAMESPACE})
        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "Ack"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding=XML_ENCODING)
        await self.send_message(MessageType.XML_ACK, req_body, msg_id)

    async def _receive_file(self) -> str:
        """Wait for and reassemble a full response from the controller.

        Handles single and multi-block (LeadMessage/BlockMessage) responses.

        Returns:
            Response payload as a string.

        Raises:
            OmniTimeoutException: If a block message is not received in time.
            OmniFragmentationException: If fragment reassembly fails.
        """
        # wait for the initial packet.
        message = await self.data_queue.get()

        # If messages have to be re-transmitted, we can sometimes receive multiple ACKs.  The first one would be handled by
        # self._ensure_sent, but if any subsequent ACKs are sent to us, we need to dump them and wait for a "real" message.
        while message.type in [MessageType.ACK, MessageType.XML_ACK]:
            _LOGGER.debug("Skipping duplicate ACK message")
            message = await self.data_queue.get()

        await self._send_ack(message.id)

        # If the response is too large, the controller will send a LeadMessage indicating how many follow-up messages will be sent
        if message.type is MessageType.MSP_LEADMESSAGE:
            try:
                leadmsg = LeadMessage.model_validate(ET.fromstring(message.payload[:-1]))
            except Exception as exc:
                msg = f"Failed to parse LeadMessage: {exc}"
                raise OmniFragmentationError(msg) from exc

            _LOGGER.debug("Will receive %s blockmessages for fragmented response", leadmsg.msg_block_count)

            # Wait for the block data data
            retval: bytes = b""
            # If we received a LeadMessage, continue to receive messages until we have all of our data
            # Fragments of data may arrive out of order, so we store them in a buffer as they arrive and sort them after
            data_fragments: dict[int, bytes] = {}
            fragment_start_time = time.time()

            while len(data_fragments) < leadmsg.msg_block_count:
                # Check if we've been waiting too long for fragments
                if time.time() - fragment_start_time > MAX_FRAGMENT_WAIT_TIME:
                    _LOGGER.error(
                        "Timeout waiting for fragments: received %d/%d after %ds",
                        len(data_fragments),
                        leadmsg.msg_block_count,
                        MAX_FRAGMENT_WAIT_TIME,
                    )
                    msg = (
                        f"Timeout waiting for fragments: received {len(data_fragments)}/{leadmsg.msg_block_count} "
                        f"after {MAX_FRAGMENT_WAIT_TIME}s"
                    )
                    raise OmniFragmentationError(msg)

                # We need to wait long enough for the Omni to get through all of it's retries before we bail out.
                try:
                    resp = await asyncio.wait_for(self.data_queue.get(), self._omni_retransmit_time * self._omni_retransmit_count)
                except TimeoutError as exc:
                    msg = f"Timeout receiving fragment: got {len(data_fragments)}/{leadmsg.msg_block_count} fragments: {exc}"
                    raise OmniFragmentationError(msg) from exc

                # We only want to collect blockmessages here
                if resp.type is not MessageType.MSP_BLOCKMESSAGE:
                    _LOGGER.debug("Received a message other than a blockmessage during fragmentation: %s", resp.type)
                    continue

                await self._send_ack(resp.id)

                # remove an 8 byte header to get to the payload data
                data_fragments[resp.id] = resp.payload[BLOCK_MESSAGE_HEADER_OFFSET:]
                _LOGGER.debug("Received fragment %d/%d", len(data_fragments), leadmsg.msg_block_count)

            # Reassemble the fragmets in order
            for _, data in sorted(data_fragments.items()):
                retval += data

            _LOGGER.debug("Successfully reassembled %d fragments into %d bytes", leadmsg.msg_block_count, len(retval))

        # We did not receive a LeadMessage, so our payload is just this one packet
        else:
            retval = message.payload

        # Decompress the returned data if necessary
        if message.compressed:
            _LOGGER.debug("Decompressing response payload")
            try:
                comp_bytes = bytes.fromhex(retval.hex())
                retval = zlib.decompress(comp_bytes)
                _LOGGER.debug("Decompressed %d bytes to %d bytes", len(comp_bytes), len(retval))
            except zlib.error as exc:
                msg = f"Failed to decompress message: {exc}"
                raise OmniMessageFormatError(msg) from exc

        # For some API calls, the Omni null terminates the response, we are stripping that here to make parsing it later easier
        return retval.decode("utf-8").strip("\x00")
