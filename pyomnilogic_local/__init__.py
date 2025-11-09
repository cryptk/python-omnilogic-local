"""PyOmniLogic-Local: A Python library for interacting with Hayward OmniLogic Local API."""

from __future__ import annotations

from .collections import EffectsCollection, LightEffectsCollection
from .omnilogic import OmniLogic
from .util import (
    OmniConnectionError,
    OmniEquipmentNotInitializedError,
    OmniEquipmentNotReadyError,
    OmniLogicLocalError,
)

__all__ = [
    "EffectsCollection",
    "LightEffectsCollection",
    "OmniConnectionError",
    "OmniEquipmentNotInitializedError",
    "OmniEquipmentNotReadyError",
    "OmniLogic",
    "OmniLogicLocalError",
]
