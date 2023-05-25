import asyncio
import logging
import random
import struct
import time
from typing import Any, cast
import xml.etree.ElementTree as ET
import zlib

from typing_extensions import Self

from .models.leadmessage import LeadMessage
from .types import ClientType, MessageType

_LOGGER = logging.getLogger(__name__)


class OmniLogicMessage:
    header_format = "!LQ4sLBBBB"
    id: int
    type: MessageType
    payload: bytes
    client_type: ClientType = ClientType.SIMPLE
    version: str = "1.19"
    timestamp: int | None
    reserved_1: int
    compressed: int
    reserved_2: int

    def __init__(self, msg_id: int, msg_type: MessageType, payload: str | None = None, version: str = "1.19") -> None:
        self.id = msg_id
        self.type = msg_type
        # If we are speaking the XML API, it seems like we need client_type 0, otherwise we need client_type 1
        self.client_type = ClientType.XML if payload is not None else ClientType.SIMPLE
        # The Hayward API terminates it's messages with a null character
        payload = f"{payload}\x00" if payload is not None else ""
        self.payload = bytes(payload, "utf-8")

        self.version = version

    def __bytes__(self) -> bytes:
        header = struct.pack(
            self.header_format,
            self.id,  # Msg id
            int(time.time_ns() / (10**9)),  # Timestamp
            bytes(self.version, "ascii"),  # version string
            self.type.value,  # OpID/msgType
            self.client_type.value,  # Client type
            0,  # reserved
            0,  # compressed
            0,  # reserved
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        # split the header and data
        header = data[0:24]
        rdata: bytes = data[24:]

        msg_id, tstamp, vers, msg_type, client_type, res1, compressed, res2 = struct.unpack(cls.header_format, header)
        message = cls(msg_id=msg_id, msg_type=MessageType(msg_type), version=vers)
        message.timestamp = tstamp
        message.client_type = client_type
        message.reserved_1 = res1
        # There are some messages that are ALWAYS compressed although they do not return a 1 in their LeadMessage
        message.compressed = compressed == 1 or message.type in [MessageType.MSP_TELEMETRY_UPDATE]
        message.reserved_2 = res2
        message.payload = rdata

        return message


class OmniLogicProtocol(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport

    def __init__(self) -> None:
        self.data_queue = asyncio.Queue[OmniLogicMessage]()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = cast(asyncio.DatagramTransport, transport)

    def connection_lost(self, exc: Exception | None) -> None:
        if exc:
            raise exc

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        message = OmniLogicMessage.from_bytes(data)
        if message.compressed:
            _LOGGER.debug("Received compressed message ID: %s, Type: %s", message.id, message.type)
        else:
            _LOGGER.debug("Received Message ID: %s, Type: %s", message.id, message.type)
        self.data_queue.put_nowait(message)

    def error_received(self, exc: Exception) -> None:
        raise exc

    async def _wait_for_ack(self, ack_id: int) -> None:
        message = await self.data_queue.get()
        while message.id != ack_id:
            _LOGGER.debug("We received a message that is not our ACK, lets put it back")
            await self.data_queue.put(message)
            message = await self.data_queue.get()

    async def _ensure_sent(self, message: OmniLogicMessage) -> None:
        delivered = False
        while not delivered:
            self.transport.sendto(bytes(message))

            # If the message that we just sent is an ACK, we do not need to wait to receive an ACK, we are done
            if message.type in [MessageType.XML_ACK, MessageType.ACK]:
                return

            # Wait for a bit to either receive an ACK for our message, otherwise, we retry delivery
            try:
                await asyncio.wait_for(self._wait_for_ack(message.id), 0.5)
                delivered = True
            except TimeoutError:
                _LOGGER.debug("ACK not received, re-attempting delivery")

    async def send_and_receive(self, msg_type: MessageType, payload: str | None, msg_id: int | None = None) -> str:
        await self.send_message(msg_type, payload, msg_id)
        return await self._receive_file()

    # Send a message that you do NOT need a response to
    async def send_message(self, msg_type: MessageType, payload: str | None, msg_id: int | None = None) -> None:
        # If we aren't sending a specific msg_id, lets randomize it
        if not msg_id:
            msg_id = random.randrange(2**32)

        _LOGGER.debug("Sending Message ID: %s, Message Type: %s, Request Body: %s", msg_id, msg_type.name, payload)

        message = OmniLogicMessage(msg_id, msg_type, payload)

        await self._ensure_sent(message)

    async def _send_ack(self, msg_id: int) -> None:
        body_element = ET.Element("Request", {"xmlns": "http://nextgen.hayward.com/api"})
        name_element = ET.SubElement(body_element, "Name")
        name_element.text = "Ack"

        req_body = ET.tostring(body_element, xml_declaration=True, encoding="unicode")
        await self.send_message(MessageType.XML_ACK, req_body, msg_id)

    async def _receive_file(self) -> str:
        # wait for the initial packet.
        message = await self.data_queue.get()

        await self._send_ack(message.id)

        # If the response is too large, the controller will send a LeadMessage indicating how many follow-up messages will be sent
        if message.type == MessageType.MSP_LEADMESSAGE:
            leadmsg = LeadMessage.from_orm(ET.fromstring(message.payload[:-1]))

            # Wait for the block data data
            retval: bytes = b""
            # If we received a LeadMessage, continue to receive messages until we have all of our data
            # Fragments of data may arrive out of order, so we store them in a buffer as they arrive and sort them after
            data_fragments: dict[int, bytes] = {}
            while len(data_fragments) < leadmsg.msg_block_count:
                resp = await self.data_queue.get()
                await self._send_ack(resp.id)
                # remove an 8 byte header to get to the payload data
                data_fragments[resp.id] = resp.payload[8:]

            # Reassemble the fragmets in order
            for _, data in sorted(data_fragments.items()):
                retval += data

        # If we did not receive a LeadMessage, but the message is compressed anyway...
        elif message.compressed:
            retval = message.payload
        # A short response, no LeadMessage and no compression...
        else:
            retval = message.payload[8:]

        # Decompress the returned data if necessary
        if message.compressed:
            comp_bytes = bytes.fromhex(retval.hex())
            retval = zlib.decompress(comp_bytes)

        # return retval
        return retval.decode("utf-8")
