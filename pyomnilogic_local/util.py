from __future__ import annotations

from enum import Enum
from typing import Self


class OmniLogicLocalError(Exception):
    """Base exception for python-omnilogic-local."""


class OmniEquipmentNotReadyError(OmniLogicLocalError):
    """Raised when equipment cannot accept commands due to its current state.

    Examples:
        - Light in FIFTEEN_SECONDS_WHITE state
        - Light in CHANGING_SHOW state
        - Light in POWERING_OFF state
        - Light in COOLDOWN state
        - Equipment performing initialization or calibration
    """


class OmniEquipmentNotInitializedError(OmniLogicLocalError):
    """Raised when equipment has not been properly initialized.

    This typically occurs when required identifiers (bow_id or system_id) are None,
    indicating the equipment hasn't been populated from telemetry data yet.
    """


class OmniConnectionError(OmniLogicLocalError):
    """Raised when communication with the OmniLogic controller fails.

    Examples:
        - UDP socket timeout
        - Network unreachable
        - Invalid response from controller
        - Protocol errors
    """


class PrettyEnum(Enum):
    def pretty(self) -> str:
        return self.name.replace("_", " ").title()

    @classmethod
    def from_pretty(cls, name: str) -> Self:
        return cls[name.upper().replace(" ", "_")]
