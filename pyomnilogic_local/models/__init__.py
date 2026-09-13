"""Pydantic models for the Hayward OmniLogic Local API."""

from __future__ import annotations

from .chlorinator_diagnostics import ChlorinatorMeasurement, ChlorinatorRelayPolarity
from .filter_diagnostics import FilterDiagnostics
from .mspconfig import MSPConfig, MSPConfigType, MSPEquipmentType
from .telemetry import Telemetry, TelemetryType

__all__ = [
    "ChlorinatorMeasurement",
    "ChlorinatorRelayPolarity",
    "FilterDiagnostics",
    "MSPConfig",
    "MSPConfigType",
    "MSPEquipmentType",
    "Telemetry",
    "TelemetryType",
]
