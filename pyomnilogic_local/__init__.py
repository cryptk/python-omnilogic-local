"""PyOmniLogic-Local: A Python library for interacting with Hayward OmniLogic Local API."""

from __future__ import annotations

from ._base import OmniEquipment
from .backyard import Backyard
from .bow import Bow
from .chlorinator import Chlorinator
from .chlorinator_equip import ChlorinatorEquipment
from .collections import EffectsCollection, LightEffectsCollection
from .colorlogiclight import ColorLogicLight
from .csad import CSAD
from .csad_equip import CSADEquipment
from .filter import Filter
from .groups import Group
from .heater import Heater
from .heater_equip import HeaterEquipment
from .omnilogic import OmniLogic
from .pump import Pump
from .relay import Relay
from .schedule import Schedule
from .sensor import Sensor
from .system import System
from .util import (
    OmniConnectionError,
    OmniEquipmentNotInitializedError,
    OmniEquipmentNotReadyError,
    OmniLogicLocalError,
)

__all__ = [
    "CSAD",
    "Backyard",
    "Bow",
    "CSADEquipment",
    "Chlorinator",
    "ChlorinatorEquipment",
    "ColorLogicLight",
    "EffectsCollection",
    "Filter",
    "Group",
    "Heater",
    "HeaterEquipment",
    "LightEffectsCollection",
    "OmniConnectionError",
    "OmniEquipment",
    "OmniEquipmentNotInitializedError",
    "OmniEquipmentNotReadyError",
    "OmniLogic",
    "OmniLogicLocalError",
    "Pump",
    "Relay",
    "Schedule",
    "Sensor",
    "System",
]
