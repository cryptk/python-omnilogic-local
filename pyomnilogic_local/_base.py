import logging
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from pyomnilogic_local.api.api import OmniLogicAPI
from pyomnilogic_local.models import MSPEquipmentType, Telemetry
from pyomnilogic_local.models.telemetry import TelemetryType
from pyomnilogic_local.omnitypes import BackyardState

if TYPE_CHECKING:
    from pyomnilogic_local.omnilogic import OmniLogic

# Define type variables for generic equipment types
MSPConfigT = TypeVar("MSPConfigT", bound=MSPEquipmentType)
TelemetryT = TypeVar("TelemetryT", bound=TelemetryType | None)


_LOGGER = logging.getLogger(__name__)


class OmniEquipment(Generic[MSPConfigT, TelemetryT]):
    """Base class for all OmniLogic equipment.

    This is an abstract base class that provides common functionality for all equipment
    types in the OmniLogic system. It handles configuration updates, telemetry updates,
    and provides access to the API for control operations.

    All equipment classes inherit from this base and are strongly typed using generic
    parameters for their specific configuration and telemetry types.

    Generic Parameters:
        MSPConfigT: The specific MSP configuration type (e.g., MSPBoW, MSPRelay)
        TelemetryT: The specific telemetry type (e.g., TelemetryBoW, TelemetryRelay, or None)

    Attributes:
        mspconfig: Configuration data from the MSP XML
        telemetry: Live telemetry data (may be None for equipment without telemetry)
        child_equipment: Dictionary of child equipment indexed by system_id

    Properties:
        bow_id: The body of water ID this equipment belongs to
        name: Equipment name from configuration
        system_id: Unique system identifier
        omni_type: OmniLogic type identifier
        is_ready: Whether equipment can accept commands (checks backyard state)

    Example:
        Equipment classes should not be instantiated directly. Access them through
        the OmniLogic instance:

        >>> omni = OmniLogic("192.168.1.100")
        >>> await omni.refresh()
        >>> # Access equipment through the backyard
        >>> pool = omni.backyard.bow["Pool"]
        >>> pump = pool.pumps["Main Pump"]
    """

    mspconfig: MSPConfigT
    telemetry: TelemetryT

    # Use a forward reference for the type hint to avoid issues with self-referential generics
    child_equipment: dict[int, "OmniEquipment[MSPConfigT, TelemetryT]"]

    def __init__(self, omni: "OmniLogic", mspconfig: MSPConfigT, telemetry: Telemetry | None) -> None:
        """Initialize the equipment with configuration and telemetry data.

        Args:
            omni: The OmniLogic instance (parent controller)
            mspconfig: The MSP configuration for this specific equipment
            telemetry: The full Telemetry object containing all equipment telemetry
        """
        self._omni = omni

        self.update(mspconfig, telemetry)

    @property
    def _api(self) -> "OmniLogicAPI":
        """Access the OmniLogic API through the parent controller."""
        return self._omni._api  # pylint: disable=protected-access

    @property
    def bow_id(self) -> int | None:
        """The bow ID of the equipment."""
        return self.mspconfig.bow_id

    @property
    def name(self) -> str | None:
        """The name of the equipment."""
        return self.mspconfig.name

    @property
    def system_id(self) -> int | None:
        """The system ID of the equipment."""
        return self.mspconfig.system_id

    @property
    def omni_type(self) -> str | None:
        """The OmniType of the equipment."""
        return self.mspconfig.omni_type

    @property
    def is_ready(self) -> bool:
        """Check if the equipment is ready to accept commands.

        Equipment is not ready when the backyard is in service or configuration mode.
        This is the base implementation that checks backyard state.
        Subclasses should call super().is_ready first and add their own checks.

        Returns:
            bool: False if backyard is in SERVICE_MODE, CONFIG_MODE, or TIMED_SERVICE_MODE,
                  True otherwise (equipment-specific checks in subclasses)
        """
        # Check if backyard state allows equipment operations
        backyard_state = self._omni.backyard.telemetry.state
        if backyard_state in (
            BackyardState.SERVICE_MODE,
            BackyardState.CONFIG_MODE,
            BackyardState.TIMED_SERVICE_MODE,
        ):
            return False
        return True

    def update(self, mspconfig: MSPConfigT, telemetry: Telemetry | None) -> None:
        """Update both the configuration and telemetry data for the equipment."""
        self.update_config(mspconfig)
        if telemetry is not None:
            self.update_telemetry(telemetry)

        self._update_equipment(mspconfig, telemetry)

    def _update_equipment(self, mspconfig: MSPConfigT, telemetry: Telemetry | None) -> None:
        """Hook to allow classes to trigger updates of sub-equipment."""

    def update_config(self, mspconfig: MSPConfigT) -> None:
        """Update the configuration data for the equipment."""
        try:
            # If the Equipment has subdevices, we don't store those as part of this device's config
            # They will get parsed and stored as their own equipment instances
            self.mspconfig = cast(MSPConfigT, mspconfig.without_subdevices())
        except AttributeError:
            self.mspconfig = mspconfig

    def update_telemetry(self, telemetry: Telemetry) -> None:
        """Update the telemetry data for the equipment."""
        # Only update telemetry if this equipment type has telemetry
        # if hasattr(self, "telemetry"):
        # Extract the specific telemetry for this equipment from the full telemetry object
        # Note: Some equipment (like sensors) don't have their own telemetry, so this may be None
        if (specific_telemetry := telemetry.get_telem_by_systemid(self.mspconfig.system_id)) is not None:
            self.telemetry = cast(TelemetryT, specific_telemetry)
        else:
            self.telemetry = cast(TelemetryT, None)
