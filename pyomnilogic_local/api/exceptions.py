from __future__ import annotations


class OmniLogicError(Exception):
    """Base exception for all OmniLogic errors."""


class OmniProtocolError(OmniLogicError):
    """Protocol-level errors during communication with the OmniLogic controller."""


class OmniTimeoutError(OmniProtocolError):
    """Timeout occurred while waiting for a response from the controller."""


class OmniMessageFormatError(OmniProtocolError):
    """Received a malformed or invalid message from the controller."""


class OmniFragmentationError(OmniProtocolError):
    """Error occurred during message fragmentation or reassembly."""


class OmniConnectionError(OmniLogicError):
    """Network connection error occurred."""


class OmniValidationError(OmniLogicError):
    """Invalid parameter or configuration value provided."""


class OmniCommandError(OmniLogicError):
    """Error occurred while executing a command on the controller."""
