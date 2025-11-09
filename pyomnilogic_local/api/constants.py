"""Constants for the OmniLogic API."""

from __future__ import annotations

# Protocol Configuration
PROTOCOL_HEADER_SIZE = 24  # Size of the message header in bytes
PROTOCOL_HEADER_FORMAT = "!LQ4sLBBBB"  # struct format for header
PROTOCOL_VERSION = "1.19"  # Current protocol version

# Block Message Constants
BLOCK_MESSAGE_HEADER_OFFSET = 8  # Offset to skip block message header and get to payload

# Timing Constants (in seconds)
OMNI_RETRANSMIT_TIME = 2.1  # Time Omni waits before retransmitting a packet
OMNI_RETRANSMIT_COUNT = 5  # Number of retransmit attempts (6 total including initial)
ACK_WAIT_TIMEOUT = 0.5  # Timeout waiting for ACK response
DEFAULT_RESPONSE_TIMEOUT = 5.0  # Default timeout for receiving responses

# Network Constants
DEFAULT_CONTROLLER_PORT = 10444  # Default UDP port for OmniLogic communication

# Queue Constants
MAX_QUEUE_SIZE = 100  # Maximum number of messages to queue
MAX_FRAGMENT_WAIT_TIME = 30.0  # Maximum time to wait for all fragments (seconds)

# Validation Constants
MAX_TEMPERATURE_F = 104  # Maximum temperature in Fahrenheit
MIN_TEMPERATURE_F = 65  # Minimum temperature in Fahrenheit
MAX_SPEED_PERCENT = 100  # Maximum speed percentage
MIN_SPEED_PERCENT = 0  # Minimum speed percentage
MAX_MESSAGE_SIZE = 65507  # Maximum UDP payload size (theoretical)

# XML Constants
XML_NAMESPACE = "http://nextgen.hayward.com/api"  # Namespace for XML messages
XML_ENCODING = "unicode"  # Encoding for XML output
