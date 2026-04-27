from __future__ import annotations

import logging
import struct
import time
from typing import Self

from pyomnilogic_local.omnitypes import ClientType, MessageType

from .constants import (
    PROTOCOL_HEADER_FORMAT,
    PROTOCOL_HEADER_SIZE,
    PROTOCOL_VERSION,
)
from .exceptions import OmniMessageFormatError

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
    timestamp: int
    reserved_1: int = 0
    compressed: bool = False
    reserved_2: int = 0

    def __init__(
        self,
        msg_id: int,
        msg_type: MessageType,
        payload: str | None = None,
        version: str = PROTOCOL_VERSION,
        timestamp: int | None = None,
    ) -> None:
        """Initialize a new OmniLogicMessage.

        Args:
            msg_id: Unique message identifier.
            msg_type: Type of message being sent.
            payload: Optional string payload (XML or command body).
            version: Protocol version string.
            timestamp: Optional timestamp for the message.
        """
        self.id = msg_id
        self.type = msg_type
        # If we are speaking the XML API, it seems like we need client_type 0, otherwise we need client_type 1
        self.client_type = ClientType.XML if payload is not None else ClientType.SIMPLE
        # The Hayward API terminates it's messages with a null character
        payload = f"{payload}\x00" if payload is not None else ""
        self.payload = bytes(payload, "utf-8")

        self.version = version
        self.timestamp = timestamp if timestamp is not None else int(time.time())

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
