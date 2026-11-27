from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Self, cast

_LOGGER = logging.getLogger(__name__)


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
    def __str__(self) -> str:
        """Return a human-friendly string representation of the enum member."""
        return self.name.replace("_", " ").title()

    @classmethod
    def from_str(cls, name: str) -> Self:
        lookup_key = name.upper().replace(" ", "_")
        try:
            return cls[lookup_key]
        except KeyError as err:
            msg = f"'{name}' is not a valid {cls.__name__}"
            raise ValueError(msg) from err


class TolerantIntEnum(Enum):
    """Mixin for IntEnums parsed from telemetry: an unknown value becomes an UNKNOWN_<n> member.

    Controllers report values that aren't in the enums (new firmware, undocumented states). A
    plain IntEnum makes pydantic reject the field, which fails the whole Telemetry parse, so
    every piece of equipment goes missing until the library is updated. With this mixin the
    value is kept as a pseudo-member (e.g. ``FilterWhyOn.UNKNOWN_23``, ``str()`` "Unknown 23"),
    a warning is logged once per value, and the rest of the telemetry parses normally.

    Pseudo-members compare equal to their int value, are reused for the same value, and are
    not listed when iterating the enum. Values that aren't integers are still rejected.
    """

    @classmethod
    def _missing_(cls, value: Any) -> Self | None:
        if isinstance(value, bool):
            return None
        try:
            int_value = int(value)
        except TypeError, ValueError:
            return None
        if int_value in cls._value2member_map_:  # e.g. "15" arriving as a string
            return cls._value2member_map_[int_value]  # type: ignore[return-value]
        pseudo = cast("Self", int.__new__(cast("type[int]", cls), int_value))
        pseudo._name_ = f"UNKNOWN_{int_value}"
        pseudo._value_ = int_value
        _LOGGER.warning(
            "Unknown %s value %s from the controller; please report it at https://github.com/cryptk/python-omnilogic-local/issues",
            cls.__name__,
            int_value,
        )
        return cls._value2member_map_.setdefault(int_value, pseudo)  # type: ignore[return-value]


def is_unknown_member(value: object) -> bool:
    """True if value is a pseudo-member TolerantIntEnum made for a value the enum doesn't list."""
    return isinstance(value, TolerantIntEnum) and value._name_ not in type(value).__members__
