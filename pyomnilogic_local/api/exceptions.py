from __future__ import annotations


class OmniLogicException(Exception):
    """Base exception for all OmniLogic errors."""


class OmniProtocolException(OmniLogicException):
    """Protocol-level errors during communication with the OmniLogic controller."""


class OmniTimeoutException(OmniProtocolException):
    """Timeout occurred while waiting for a response from the controller."""


class OmniMessageFormatException(OmniProtocolException):
    """Received a malformed or invalid message from the controller."""


class OmniFragmentationException(OmniProtocolException):
    """Error occurred during message fragmentation or reassembly."""


class OmniConnectionException(OmniLogicException):
    """Network connection error occurred."""


class OmniValidationException(OmniLogicException):
    """Invalid parameter or configuration value provided."""


class OmniCommandException(OmniLogicException):
    """Error occurred while executing a command on the controller."""
