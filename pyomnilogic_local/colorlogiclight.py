import logging
from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.decorators import dirties_state
from pyomnilogic_local.models.mspconfig import MSPColorLogicLight
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryColorLogicLight
from pyomnilogic_local.omnitypes import (
    ColorLogicBrightness,
    ColorLogicLightType,
    ColorLogicPowerState,
    ColorLogicSpeed,
    LightShows,
)
from pyomnilogic_local.util import (
    OmniEquipmentNotInitializedError,
    OmniEquipmentNotReadyError,
)

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic

_LOGGER = logging.getLogger(__name__)


class ColorLogicLight(OmniEquipment[MSPColorLogicLight, TelemetryColorLogicLight]):
    """Represents a color logic light."""

    mspconfig: MSPColorLogicLight
    telemetry: TelemetryColorLogicLight

    def __init__(self, omni: "OmniLogic", mspconfig: MSPColorLogicLight, telemetry: Telemetry) -> None:
        super().__init__(omni, mspconfig, telemetry)

    @property
    def model(self) -> ColorLogicLightType:
        """Returns the model of the light."""
        return self.mspconfig.equip_type

    @property
    def v2_active(self) -> bool:
        """Returns whether the light is v2 active."""
        return self.mspconfig.v2_active

    @property
    def effects(self) -> list[LightShows] | None:
        """Returns the effects of the light."""
        return self.mspconfig.effects

    @property
    def state(self) -> ColorLogicPowerState:
        """Returns the state of the light."""
        return self.telemetry.state

    @property
    def show(self) -> LightShows:
        """Returns the current light show."""
        return self.telemetry.show

    @property
    def speed(self) -> ColorLogicSpeed:
        """Returns the current speed."""
        if self.model in [ColorLogicLightType.SAM, ColorLogicLightType.TWO_FIVE, ColorLogicLightType.FOUR_ZERO, ColorLogicLightType.UCL]:
            return self.telemetry.speed
        # Non color-logic lights only support 1x speed
        return ColorLogicSpeed.ONE_TIMES

    @property
    def brightness(self) -> ColorLogicBrightness:
        """Returns the current brightness."""
        if self.model in [ColorLogicLightType.SAM, ColorLogicLightType.TWO_FIVE, ColorLogicLightType.FOUR_ZERO, ColorLogicLightType.UCL]:
            return self.telemetry.brightness
        # Non color-logic lights only support 100% brightness
        return ColorLogicBrightness.ONE_HUNDRED_PERCENT

    @property
    def special_effect(self) -> int:
        """Returns the current special effect."""
        return self.telemetry.special_effect

    @property
    def is_ready(self) -> bool:
        """
        Returns whether the light is ready to accept commands.

        The light is not ready when:
        - The backyard is in service/config mode (checked by parent class)
        - The light is in a transitional state:
          - FIFTEEN_SECONDS_WHITE: Light is in the 15-second white period after power on
          - CHANGING_SHOW: Light is actively changing between shows
          - POWERING_OFF: Light is in the process of turning off
          - COOLDOWN: Light is in cooldown period after being turned off

        Returns:
            bool: True if the light can accept commands, False otherwise.
        """
        # First check if backyard is ready
        if not super().is_ready:
            return False

        # Then check light-specific readiness
        return self.state not in [
            ColorLogicPowerState.FIFTEEN_SECONDS_WHITE,
            ColorLogicPowerState.CHANGING_SHOW,
            ColorLogicPowerState.POWERING_OFF,
            ColorLogicPowerState.COOLDOWN,
        ]

    @dirties_state()
    async def turn_on(self) -> None:
        """
        Turns the light on.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the light is not ready to accept commands
                (in FIFTEEN_SECONDS_WHITE, CHANGING_SHOW, POWERING_OFF, or COOLDOWN state).
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn on light: bow_id or system_id is None")
        if not self.is_ready:
            raise OmniEquipmentNotReadyError(
                f"Cannot turn on light: light is in {self.state.pretty()} state. Wait for the light to be ready before issuing commands."
            )
        await self._api.async_set_equipment(self.bow_id, self.system_id, True)

    @dirties_state()
    async def turn_off(self) -> None:
        """
        Turns the light off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the light is not ready to accept commands
                (in FIFTEEN_SECONDS_WHITE, CHANGING_SHOW, POWERING_OFF, or COOLDOWN state).
        """
        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot turn off light: bow_id or system_id is None")
        if not self.is_ready:
            raise OmniEquipmentNotReadyError(
                f"Cannot turn off light: light is in {self.state.pretty()} state. Wait for the light to be ready before issuing commands."
            )
        await self._api.async_set_equipment(self.bow_id, self.system_id, False)

    @dirties_state()
    async def set_show(
        self, show: LightShows | None = None, speed: ColorLogicSpeed | None = None, brightness: ColorLogicBrightness | None = None
    ) -> None:
        """
        Sets the light show, speed, and brightness.

        Args:
            show: The light show to set. If None, uses the current show.
            speed: The speed to set. If None, uses the current speed.
            brightness: The brightness to set. If None, uses the current brightness.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
            OmniEquipmentNotReadyError: If the light is not ready to accept commands
                (in FIFTEEN_SECONDS_WHITE, CHANGING_SHOW, POWERING_OFF, or COOLDOWN state).

        Note:
            Non color-logic lights do not support speed or brightness control.
            If speed or brightness are provided for non color-logic lights, they will be ignored
            and a warning will be logged.
        """

        # Non color-logic lights do not support speed or brightness control
        if self.model not in [
            ColorLogicLightType.SAM,
            ColorLogicLightType.TWO_FIVE,
            ColorLogicLightType.FOUR_ZERO,
            ColorLogicLightType.UCL,
        ]:
            if speed is not None:
                _LOGGER.warning("Non colorlogic lights do not support speed control %s", self.model.name)
                speed = ColorLogicSpeed.ONE_TIMES
            if brightness is not None:
                _LOGGER.warning("Non colorlogic lights do not support brightness control %s", self.model.name)
                brightness = ColorLogicBrightness.ONE_HUNDRED_PERCENT

        if self.bow_id is None or self.system_id is None:
            raise OmniEquipmentNotInitializedError("Cannot set light show: bow_id or system_id is None")

        if not self.is_ready:
            raise OmniEquipmentNotReadyError(
                f"Cannot set light show: light is in {self.state.pretty()} state. Wait for the light to be ready before issuing commands."
            )

        await self._api.async_set_light_show(
            self.bow_id,
            self.system_id,
            show or self.show,  # use current value if None
            speed or self.speed,  # use current value if None
            brightness or self.brightness,  # use current value if None
        )
