from __future__ import annotations

from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.collections import EquipmentDict
from pyomnilogic_local.csad_equip import CSADEquipment
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPCSAD
from pyomnilogic_local.models.telemetry import TelemetryCSAD
from pyomnilogic_local.omnitypes import CSADMode, CSADStatus
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import CSADType


class CSAD(OmniEquipment[MSPCSAD, TelemetryCSAD]):
    """Represents a CSAD (Chemistry Sense and Dispense) system in the OmniLogic system.

    A CSAD system monitors and automatically dispenses chemicals (typically pH reducer
    or CO2) to maintain optimal water chemistry. It continuously measures pH levels
    and dispenses treatment chemicals as needed to maintain target pH levels.

    The Chemistry Sense Module (CSM) contains both pH and ORP probes. The pH sensor
    output is the primary control input for the CSAD function, while the ORP sensor
    output is primarily used by the chlorinator function for automatic chlorine
    generation control (though ORP readings are included in CSAD telemetry for
    monitoring chlorinator effectiveness).

    Attributes:
        mspconfig: The MSP configuration for this CSAD
        telemetry: Real-time telemetry data for this CSAD
        csad_equipment: Collection of physical CSAD equipment devices

    Example:
        >>> csad = pool.get_csad()
        >>> print(f"Current pH: {csad.current_ph}")
        >>> print(f"Target pH: {csad.target_ph}")
        >>> if csad.is_dispensing:
        ...     print("Currently dispensing chemicals")
    """

    mspconfig: MSPCSAD
    telemetry: TelemetryCSAD
    csad_equipment: EquipmentDict[CSADEquipment] = EquipmentDict()

    def __init__(self, omni: OmniLogic, mspconfig: MSPCSAD, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    def _update_equipment(self, mspconfig: MSPCSAD, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        if telemetry is None:
            return
        self._update_csad_equipment(mspconfig, telemetry)

    def _update_csad_equipment(self, mspconfig: MSPCSAD, telemetry: Telemetry) -> None:
        """Update the CSAD equipment based on the MSP configuration."""
        if mspconfig.csad_equipment is None:
            self.csad_equipment = EquipmentDict()
            return

        self.csad_equipment = EquipmentDict([CSADEquipment(self._omni, equip, telemetry) for equip in mspconfig.csad_equipment])

    # Expose MSPConfig attributes
    @property
    def enabled(self) -> bool:
        """Whether the CSAD is enabled in the system configuration."""
        return self.mspconfig.enabled

    @property
    def equip_type(self) -> CSADType:
        """Type of CSAD system (ACID or CO2)."""
        return self.mspconfig.equip_type

    @property
    def ph_target_level(self) -> float:
        """Target pH level that the CSAD aims to maintain."""
        return self.mspconfig.target_value

    @property
    def ph_current_value(self) -> float:
        """Current pH level reading from the sensor, including calibration offset."""
        return self.telemetry.ph + self.ph_calibration_value

    @property
    def ph_current_value_raw(self) -> float:
        """Current pH level reading from the sensor without calibration offset."""
        return self.telemetry.ph

    @property
    def ph_calibration_value(self) -> float:
        """Calibration offset value for pH sensor."""
        return self.mspconfig.calibration_value

    @property
    def ph_low_alarm_level(self) -> float:
        """Low pH threshold for triggering an alarm."""
        return self.mspconfig.ph_low_alarm_level

    @property
    def ph_high_alarm_level(self) -> float:
        """High pH threshold for triggering an alarm."""
        return self.mspconfig.ph_high_alarm_level

    @property
    def orp_target_level(self) -> int:
        """Target ORP (Oxidation-Reduction Potential) level in millivolts."""
        return self.mspconfig.orp_target_level

    @property
    def orp_current_level(self) -> int:
        """Current ORP (Oxidation-Reduction Potential) reading in millivolts."""
        return self.telemetry.orp

    @property
    def orp_runtime_level(self) -> int:
        """ORP runtime level threshold in millivolts."""
        return self.mspconfig.orp_runtime_level

    @property
    def orp_low_alarm_level(self) -> int:
        """ORP level that triggers a low ORP alarm in millivolts."""
        return self.mspconfig.orp_low_alarm_level

    @property
    def orp_high_alarm_level(self) -> int:
        """ORP level that triggers a high ORP alarm in millivolts."""
        return self.mspconfig.orp_high_alarm_level

    @property
    def orp_forced_on_time(self) -> int:
        """Duration in minutes for forced ORP dispensing mode."""
        return self.mspconfig.orp_forced_on_time

    @property
    def orp_forced_enabled(self) -> bool:
        """Whether forced ORP dispensing mode is enabled."""
        return self.mspconfig.orp_forced_enabled

    # Expose Telemetry attributes
    @property
    def status(self) -> CSADStatus:
        """Raw status value from telemetry."""
        return self.telemetry.status

    @property
    def mode(self) -> CSADMode:
        """Current operating mode of the CSAD.

        Returns:
            CSADMode enum value:
            - OFF (0): CSAD is off
            - AUTO (1): Automatic mode, dispensing as needed
            - FORCE_ON (2): Forced dispensing mode
            - MONITORING (3): Monitoring only, not dispensing
            - DISPENSING_OFF (4): Dispensing is disabled

        Example:
            >>> if csad.mode == CSADMode.AUTO:
            ...     print("CSAD is in automatic mode")
        """
        return self.telemetry.mode

    # Computed properties
    @property
    def state(self) -> CSADStatus:
        """Current dispensing state of the CSAD.

        Returns:
            CSADStatus.NOT_DISPENSING (0): Not currently dispensing
            CSADStatus.DISPENSING (1): Currently dispensing chemicals

        Example:
            >>> if csad.state == CSADStatus.DISPENSING:
            ...     print("Dispensing chemicals")
        """
        return self.status

    @property
    def is_on(self) -> bool:
        """Check if the CSAD is currently enabled and operational.

        A CSAD is considered "on" if it is enabled in configuration and
        not in OFF mode.

        Returns:
            True if the CSAD is enabled and operational, False otherwise

        Example:
            >>> if csad.is_on:
            ...     print(f"CSAD is monitoring pH: {csad.current_ph:.2f}")
        """
        return self.enabled and self.mode != CSADMode.OFF

    @property
    def is_dispensing(self) -> bool:
        """Check if the CSAD is currently dispensing chemicals.

        Returns:
            True if actively dispensing, False otherwise

        Example:
            >>> if csad.is_dispensing:
            ...     print(f"Dispensing to reach target pH: {csad.target_ph:.2f}")
        """
        return self.state == CSADStatus.DISPENSING

    @property
    def has_alert(self) -> bool:
        """Check if there are any pH or ORP alerts.

        Checks if current readings are outside the configured alarm thresholds.

        Returns:
            True if pH or ORP is outside alarm levels, False otherwise

        Example:
            >>> if csad.has_alert:
            ...     print(f"Alert! {csad.alert_status}")
        """
        ph_alert = self.ph_current_value < self.ph_low_alarm_level or self.ph_current_value > self.ph_high_alarm_level
        orp_alert = self.orp_current_level < self.orp_low_alarm_level or self.orp_current_level > self.orp_high_alarm_level
        return ph_alert or orp_alert

    @property
    def alert_status(self) -> str:
        """Get a human-readable status of any active alerts.

        Returns:
            A descriptive string of alert conditions, or 'OK' if no alerts

        Example:
            >>> status = csad.alert_status
            >>> if status != 'OK':
            ...     print(f"Chemistry alert: {status}")
        """
        alerts = []

        if self.ph_current_value < self.ph_low_alarm_level:
            alerts.append(f"pH too low ({self.ph_current_value:.2f} < {self.ph_low_alarm_level:.2f})")
        elif self.ph_current_value > self.ph_high_alarm_level:
            alerts.append(f"pH too high ({self.ph_current_value:.2f} > {self.ph_high_alarm_level:.2f})")

        if self.orp_current_level < self.orp_low_alarm_level:
            alerts.append(f"ORP too low ({self.orp_current_level} < {self.orp_low_alarm_level} mV)")
        elif self.orp_current_level > self.orp_high_alarm_level:
            alerts.append(f"ORP too high ({self.orp_current_level} > {self.orp_high_alarm_level} mV)")

        return "; ".join(alerts) if alerts else "OK"

    @control_method
    async def set_ph_target(self, ph_target: float) -> None:
        """Set the target pH for the CSAD.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot set pH: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        if not 7.0 <= ph_target <= 8.0:
            msg = f"Invalid pH target: {ph_target}. Target pH must be between 7.0 and 8.0"
            raise ValueError(msg)

        await self._api.async_set_csad_ph_target_value(pool_id=self.bow_id, csad_id=self.system_id, ph_target=ph_target)

    @control_method
    async def set_orp_target(self, orp_target: int) -> None:
        """Set the target ORP for the CSAD.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot set ORP: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        if not 400 <= orp_target <= 900:
            msg = f"Invalid ORP target: {orp_target}. Target ORP must be between 400 and 900 mV"
            raise ValueError(msg)

        await self._api.async_set_csad_orp_target_level(pool_id=self.bow_id, csad_id=self.system_id, orp_target=orp_target)
