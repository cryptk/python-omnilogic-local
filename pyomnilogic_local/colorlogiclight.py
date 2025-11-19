from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.collections import LightEffectsCollection
from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.models.mspconfig import MSPColorLogicLight
from pyomnilogic_local.models.telemetry import TelemetryColorLogicLight
from pyomnilogic_local.omnitypes import ColorLogicBrightness, ColorLogicLightType, ColorLogicPowerState, ColorLogicSpeed
from pyomnilogic_local.util import OmniEquipmentNotInitializedError

if TYPE_CHECKING:
    from pyomnilogic_local.models.telemetry import Telemetry
    from pyomnilogic_local.omnilogic import OmniLogic
    from pyomnilogic_local.omnitypes import LightShows

_LOGGER = logging.getLogger(__name__)


class ColorLogicLight(OmniEquipment[MSPColorLogicLight, TelemetryColorLogicLight]):
    """Represents a ColorLogic or compatible LED light in the OmniLogic system.

    ColorLogic lights are intelligent LED pool and spa lights that can display
    various color shows, patterns, and effects. The OmniLogic system supports
    multiple light models with different capabilities:

    Light Models:
        - ColorLogic 2.5
        - ColorLogic 4.0
        - ColorLogic UCL
        - ColorLogic SAM
        - Pentair and Zodiac compatible lights (limited functionality)

    Each light model supports different shows, speeds, and brightness levels.
    The ColorLogicLight class automatically handles these differences.

    Attributes:
        mspconfig: Configuration data for this light from MSP XML
        telemetry: Real-time operational state and settings

    Properties (Configuration):
        model: Light model type (TWO_FIVE, FOUR_ZERO, UCL, SAM, etc.)
        v2_active: Whether V2 protocol features are active
        effects: Collection of available light shows for this model with
                 attribute and dict-like access patterns

    Properties (Telemetry):
        state: Current power state (ON, OFF, transitional states)
        show: Currently selected light show
        speed: Show animation speed (1x, 2x, 4x, 8x)
        brightness: Light brightness (25%, 50%, 75%, 100%)
        special_effect: Special effect setting

    Properties (Computed):
        is_on: True if light is currently on
        is_ready: True if light can accept commands (not in transitional state)

    Control Methods:
        turn_on(): Turn on light (starts at saved show)
        turn_off(): Turn off light
        toggle(): Toggle light on/off
        set_show(show): Set light to specific show
        set_speed(speed): Set animation speed (1x-8x)
        set_brightness(brightness): Set brightness (25%-100%)

    Example:
        >>> pool = omni.backyard.bow["Pool"]
        >>> pool_light = pool.lights["Pool Light"]
        >>>
        >>> # Check light capabilities
        >>> print(f"Light model: {pool_light.model}")
        >>> print(f"Available shows: {pool_light.effects}")
        >>>
        >>> # Check current state
        >>> if pool_light.is_on:
        ...     print(f"Show: {pool_light.show}")
        ...     print(f"Speed: {pool_light.speed}")
        ...     print(f"Brightness: {pool_light.brightness}")
        >>>
        >>> # Control light - use attribute access for available effects!
        >>> await pool_light.turn_on()
        >>> await pool_light.set_show(pool_light.effects.TROPICAL)
        >>> await pool_light.set_speed(ColorLogicSpeed.TWO_TIMES)
        >>> await pool_light.set_brightness(ColorLogicBrightness.SEVENTY_FIVE_PERCENT)
        >>> await pool_light.turn_off()
        >>>
        >>> # Or use traditional enum imports
        >>> from pyomnilogic_local import ColorLogicShow25
        >>> await pool_light.set_show(ColorLogicShow25.TROPICAL)

    Important - Light State Transitions:
        ColorLogic lights go through several transitional states when changing
        settings. During these states, the light is NOT ready to accept commands:

        - FIFTEEN_SECONDS_WHITE: 15-second white period after power on
        - CHANGING_SHOW: Actively cycling through shows
        - POWERING_OFF: In process of turning off
        - COOLDOWN: Cooling down after being turned off

        Always check is_ready before sending commands, or wait for state to
        stabilize after each command.

    Note:
        - Different light models support different show sets
        - Non-ColorLogic lights (Pentair, Zodiac) have limited control
        - Speed and brightness may not be adjustable on all models
        - Some shows may require specific light hardware
        - V2 protocol enables enhanced features on compatible lights
    """

    mspconfig: MSPColorLogicLight
    telemetry: TelemetryColorLogicLight

    def __init__(self, omni: OmniLogic, mspconfig: MSPColorLogicLight, telemetry: Telemetry) -> None:
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
    def effects(self) -> LightEffectsCollection | None:
        """Returns the available light effects as a collection with attribute and dict-like access.

        The effects collection provides multiple access patterns:
        - Attribute access: `light.effects.VOODOO_LOUNGE`
        - Dict-like access: `light.effects["VOODOO_LOUNGE"]`
        - Index access: `light.effects[0]`
        - Membership testing: `"TROPICAL" in light.effects`
        - Iteration: `for effect in light.effects: ...`

        Returns:
            LightEffectsCollection containing the available shows for this light model,
            or None if effects are not available.

        Example:
            >>> # Attribute access - most intuitive
            >>> await light.set_show(light.effects.TROPICAL)
            >>>
            >>> # Dict-like access
            >>> await light.set_show(light.effects["TROPICAL"])
            >>>
            >>> # Check availability
            >>> if "VOODOO_LOUNGE" in light.effects:
            ...     await light.set_show(light.effects.VOODOO_LOUNGE)
            >>>
            >>> # List all available effects
            >>> for effect in light.effects:
            ...     print(f"{effect.name}: {effect.value}")
        """
        if self.mspconfig.effects is None:
            return None
        return LightEffectsCollection(self.mspconfig.effects)

    @property
    def state(self) -> ColorLogicPowerState:
        """Returns the state of the light."""
        return self.telemetry.state

    @property
    def show(self) -> LightShows:
        """Returns the current light show."""
        return self.telemetry.show_name(self.model, self.v2_active)

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
        """Return whether the light is ready to accept commands.

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

    @control_method
    async def turn_on(self) -> None:
        """Turn the light on.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn on light: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_equipment(self.bow_id, self.system_id, True)

    @control_method
    async def turn_off(self) -> None:
        """Turn the light off.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.
        """
        if self.bow_id is None or self.system_id is None:
            msg = "Cannot turn off light: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)
        await self._api.async_set_equipment(self.bow_id, self.system_id, False)

    @control_method
    async def set_show(
        self, show: LightShows | None = None, speed: ColorLogicSpeed | None = None, brightness: ColorLogicBrightness | None = None
    ) -> None:
        """Set the light show, speed, and brightness.

        Args:
            show: The light show to set. If None, uses the current show.
            speed: The speed to set. If None, uses the current speed.
            brightness: The brightness to set. If None, uses the current brightness.

        Raises:
            OmniEquipmentNotInitializedError: If bow_id or system_id is None.

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
            msg = "Cannot set light show: bow_id or system_id is None"
            raise OmniEquipmentNotInitializedError(msg)

        await self._api.async_set_light_show(
            self.bow_id,
            self.system_id,
            show if show is not None else self.show,  # use current value if None
            speed if speed is not None else self.speed,  # use current value if None
            brightness if brightness is not None else self.brightness,  # use current value if None
        )
