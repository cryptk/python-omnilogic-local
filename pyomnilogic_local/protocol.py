import asyncio
import logging
import random
import struct
import time
import xml.etree.ElementTree as ET
import zlib
from typing import Any, cast

from typing_extensions import Self

from .exceptions import OmniTimeoutException
from .models.leadmessage import LeadMessage
from .omnitypes import ClientType, MessageType

_LOGGER = logging.getLogger(__name__)


class OmniLogicMessage:
    """
    Represents a protocol message for communication with the OmniLogic controller.
    Handles serialization and deserialization of message headers and payloads.
    """

    header_format = "!LQ4sLBBBB"
    id: int
    type: MessageType
    payload: bytes
    client_type: ClientType = ClientType.SIMPLE
    version: str = "1.19"
    timestamp: int | None = int(time.time())
    reserved_1: int = 0
    compressed: bool = False
    reserved_2: int = 0

    def __init__(
        self,
        msg_id: int,
        msg_type: MessageType,
        payload: str | None = None,
        version: str = "1.19",
    ) -> None:
        """
        Initialize a new OmniLogicMessage.
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
        """
        Serialize the message to bytes for UDP transmission.
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
        """
        Return a string representation of the message for debugging.
        """
        if self.compressed or self.type is MessageType.MSP_BLOCKMESSAGE:
            return f"ID: {self.id}, Type: {self.type.name}, Compressed: {self.compressed}, Client: {self.client_type.name}"
        return (
            f"ID: {self.id}, Type: {self.type.name}, Compressed: {self.compressed}, Client: {self.client_type.name}, "
            f"Body: {self.payload[:-1].decode('utf-8')}"
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """
        Parse a message from its byte representation.
        Args:
            data: Byte data received from the controller.
        Returns:
            OmniLogicMessage instance.
        """
        # split the header and data
        header = data[:24]
        rdata: bytes = data[24:]

        (msg_id, tstamp, vers, msg_type, client_type, res1, compressed, res2) = struct.unpack(cls.header_format, header)
        message = cls(msg_id=msg_id, msg_type=MessageType(msg_type), version=vers.decode("utf-8"))
        message.timestamp = tstamp
        message.client_type = ClientType(int(client_type))
        message.reserved_1 = res1
        # There are some messages that are ALWAYS compressed although they do not return a 1 in their LeadMessage
        message.compressed = compressed == 1 or message.type in [MessageType.MSP_TELEMETRY_UPDATE]
        message.reserved_2 = res2
        message.payload = rdata

        return message


class OmniLogicProtocol(asyncio.DatagramProtocol):
    """
    Asyncio DatagramProtocol implementation for OmniLogic UDP communication.
    Handles message sending, receiving, retries, and block message reassembly.
    """

    transport: asyncio.DatagramTransport
    # The omni will re-transmit a packet every 2 seconds if it does not receive an ACK.  We pad that just a touch to be safe
    _omni_retransmit_time = 2.1
    # The omni will re-transmit 5 times (a total of 6 attempts including the initial) if it does not receive an ACK
    _omni_retransmit_count = 5

    def __init__(self) -> None:
        """
        Initialize the protocol handler and message queue.
        """
        self.data_queue = asyncio.Queue[OmniLogicMessage]()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """
        Called when a UDP connection is made.
        """
        self.transport = cast(asyncio.DatagramTransport, transport)

    def connection_lost(self, exc: Exception | None) -> None:
        """
        Called when the UDP connection is lost or closed.
        """
        if exc:
            raise exc

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        """
        Called when a datagram is received from the controller.
        Parses the message and puts it on the queue. Handles corrupt or unexpected data gracefully.
        """
        try:
            message = OmniLogicMessage.from_bytes(data)
            _LOGGER.debug("Received Message %s from %s", str(message), addr)
            try:
                self.data_queue.put_nowait(message)
            except asyncio.QueueFull:
                _LOGGER.error("Data queue is full. Dropping message: %s", str(message))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _LOGGER.error("Failed to parse incoming datagram from %s: %s", addr, exc, exc_info=True)

    def error_received(self, exc: Exception) -> None:
        """
        Called when a UDP error is received.
        """
        raise exc

    async def _wait_for_ack(self, ack_id: int) -> None:
        """
        Wait for an ACK message with the given ID.
        Handles dropped or out-of-order ACKs.
        """
        message = await self.data_queue.get()
        while message.id != ack_id:
            _LOGGER.debug("We received a message that is not our ACK, it appears the ACK was dropped")
            # If the message that we received was either a LEADMESSAGE or a BLOCK MESSAGE, lets put it back and return,
            # The Omni is continuing on with life, lets not be clingy for an ACK that was dropped and will never come
            # We will put this new message back into the queue and stop waiting for our ACK.
            # The set below should include any message types that may be sent immediately after the Omni sends us an ACK.
            # Example is:
            # Us > Omni: MessageType.REQUEST_CONFIGURATION
            # Omni > Us: MessageType.ACK
            # Omni > Us: MessageType.MSP_LEADMESSAGE  <--- Sent immediately after an ACK
            if message.type in {MessageType.MSP_LEADMESSAGE, MessageType.MSP_TELEMETRY_UPDATE}:
                _LOGGER.debug("Omni has sent a new message, continuing on with the communication")
                await self.data_queue.put(message)
                break
            # In theory, we should never get to this spot, but it's mostly here to cause the code to wait forever so that asyncio will
            # eventually time out waiting for it, that way we can deal with the dropped packets
            message = await self.data_queue.get()

    async def _ensure_sent(
        self,
        message: OmniLogicMessage,
        max_attempts: int = 5,
    ) -> None:
        """
        Send a message and ensure it is acknowledged, retrying if necessary.
        Args:
            message: The message to send.
            max_attempts: Maximum number of send attempts.
        Raises:
            OmniTimeoutException: If no ACK is received after retries.
        """
        for attempt in range(0, max_attempts):
            self.transport.sendto(bytes(message))

            # If the message that we just sent is an ACK, we do not need to wait to receive an ACK, we are done
            if message.type in [MessageType.XML_ACK, MessageType.ACK]:
                return

            # Wait for a bit to either receive an ACK for our message, otherwise, we retry delivery
            try:
                await asyncio.wait_for(self._wait_for_ack(message.id), 0.5)
                return
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
                    _LOGGER.error(
                        "Failed to receive ACK for message type %s (ID: %s) after %d attempts.", message.type.name, message.id, max_attempts
                    )
                    raise OmniTimeoutException("Failed to receive acknowledgement of command, max retries exceeded") from exc

    async def send_and_receive(
        self,
        msg_type: MessageType,
        payload: str | None,
        msg_id: int | None = None,
    ) -> str:
        """
        Send a message and wait for a response, returning the response payload as a string.
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
        """
        Send a message that does not require a response.
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
        """
        Send an ACK message for the given message ID.
        """
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})
        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "Ack"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self.send_message(MessageType.XML_ACK, req_body, msg_id)

    async def _receive_file(self) -> str:
        """
        Wait for and reassemble a full response from the controller.
        Handles single and multi-block (LeadMessage/BlockMessage) responses.
        Returns:
            Response payload as a string.
        Raises:
            OmniTimeoutException: If a block message is not received in time.
        """
        # wait for the initial packet.
        message = await self.data_queue.get()

        # If messages have to be re-transmitted, we can sometimes receive multiple ACKs.  The first one would be handled by
        # self._ensure_sent, but if any subsequent ACKs are sent to us, we need to dump them and wait for a "real" message.
        while message.type in [MessageType.ACK, MessageType.XML_ACK]:
            message = await self.data_queue.get()

        await self._send_ack(message.id)

        # If the response is too large, the controller will send a LeadMessage indicating how many follow-up messages will be sent
        if message.type is MessageType.MSP_LEADMESSAGE:
            leadmsg = LeadMessage.from_orm(ET.fromstring(message.payload[:-1]))

            _LOGGER.debug("Will receive %s blockmessages", leadmsg.msg_block_count)

            # Wait for the block data data
            retval: bytes = b""
            # If we received a LeadMessage, continue to receive messages until we have all of our data
            # Fragments of data may arrive out of order, so we store them in a buffer as they arrive and sort them after
            data_fragments: dict[int, bytes] = {}
            while len(data_fragments) < leadmsg.msg_block_count:
                # We need to wait long enough for the Omni to get through all of it's retries before we bail out.
                try:
                    resp = await asyncio.wait_for(self.data_queue.get(), self._omni_retransmit_time * self._omni_retransmit_count)
                except TimeoutError as exc:
                    raise OmniTimeoutException from exc

                # We only want to collect blockmessages here
                if resp.type is not MessageType.MSP_BLOCKMESSAGE:
                    _LOGGER.debug("Received a message other than a blockmessage: %s", resp.type)
                    continue

                await self._send_ack(resp.id)

                # remove an 8 byte header to get to the payload data
                data_fragments[resp.id] = resp.payload[8:]

            # Reassemble the fragmets in order
            for _, data in sorted(data_fragments.items()):
                retval += data

        # We did not receive a LeadMessage, so our payload is just this one packet
        else:
            retval = message.payload

        # Decompress the returned data if necessary
        if message.compressed:
            comp_bytes = bytes.fromhex(retval.hex())
            retval = zlib.decompress(comp_bytes)

        # For some API calls, the Omni null terminates the response, we are stripping that here to make parsing it later easier
        return retval.decode("utf-8").strip("\x00")
