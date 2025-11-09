"""Custom collection types for OmniLogic equipment management."""

from __future__ import annotations

import logging
from collections import Counter
from enum import Enum
from typing import TYPE_CHECKING, Any, overload

from pyomnilogic_local._base import OmniEquipment
from pyomnilogic_local.omnitypes import LightShows

if TYPE_CHECKING:
    from collections.abc import Iterator

_LOGGER = logging.getLogger(__name__)

# Track which duplicate names we've already warned about to avoid log spam
_WARNED_DUPLICATE_NAMES: set[str] = set()


class EquipmentDict[OE: OmniEquipment[Any, Any]]:
    """A dictionary-like collection that supports lookup by both name and system_id.

    This collection allows accessing equipment using either their name (str) or
    system_id (int), providing flexible and intuitive access patterns.

    Type Safety:
        The lookup key type determines the lookup method:
        - str keys lookup by equipment name
        - int keys lookup by equipment system_id

    Examples:
        >>> # Create collection from list of equipment
        >>> bows = EquipmentDict([pool_bow, spa_bow])
        >>>
        >>> # Access by name (string key)
        >>> pool = bows["Pool"]
        >>>
        >>> # Access by system_id (integer key)
        >>> pool = bows[3]
        >>>
        >>> # Explicit methods for clarity
        >>> pool = bows.get_by_name("Pool")
        >>> pool = bows.get_by_id(3)
        >>>
        >>> # Standard dict operations
        >>> for bow in bows:
        ...     print(bow.name)
        >>> len(bows)
        >>> if "Pool" in bows:
        ...     print("Pool exists")

    Note:
        If an equipment item has a name that looks like a number (e.g., "123"),
        you must use an actual int type to lookup by system_id, as string keys
        always lookup by name. This type-based differentiation prevents ambiguity.
    """

    def __init__(self, items: list[OE] | None = None) -> None:
        """Initialize the equipment collection.

        Args:
            items: Optional list of equipment items to populate the collection.

        Raises:
            ValueError: If any item has neither a system_id nor a name.
        """
        self._items: list[OE] = items if items is not None else []
        self._validate()

    def _validate(self) -> None:
        """Validate the equipment collection.

        Checks for:
        1. Items without both system_id and name (raises ValueError)
        2. Duplicate names (logs warning once per unique duplicate)

        Raises:
            ValueError: If any item has neither a system_id nor a name.
        """
        # Check for items with no system_id AND no name
        if invalid_items := [item for item in self._items if item.system_id is None and item.name is None]:
            msg = (
                f"Equipment collection contains {len(invalid_items)} item(s) "
                "with neither a system_id nor a name. All equipment must have "
                "at least one identifier for addressing."
            )
            raise ValueError(msg)

        # Find duplicate names that we haven't warned about yet
        name_counts = Counter(item.name for item in self._items if item.name is not None)
        duplicate_names = {name for name, count in name_counts.items() if count > 1}
        unwarned_duplicates = duplicate_names.difference(_WARNED_DUPLICATE_NAMES)

        # Log warnings for new duplicates
        for name in unwarned_duplicates:
            _LOGGER.warning(
                "Equipment collection contains %d items with the same name '%s'. "
                "Name-based lookups will return the first match. "
                "Consider using system_id-based lookups for reliability "
                "or renaming equipment to avoid duplicates.",
                name_counts[name],
                name,
            )
            _WARNED_DUPLICATE_NAMES.add(name)

    @property
    def _by_name(self) -> dict[str, OE]:
        """Dynamically build name-to-equipment mapping."""
        return {item.name: item for item in self._items if item.name is not None}

    @property
    def _by_id(self) -> dict[int, OE]:
        """Dynamically build system_id-to-equipment mapping."""
        return {item.system_id: item for item in self._items if item.system_id is not None}

    @overload
    def __getitem__(self, key: str) -> OE: ...

    @overload
    def __getitem__(self, key: int) -> OE: ...

    def __getitem__(self, key: str | int) -> OE:
        """Get equipment by name (str) or system_id (int).

        Args:
            key: Equipment name (str) or system_id (int)

        Returns:
            The equipment item matching the key

        Raises:
            KeyError: If no equipment matches the key
            TypeError: If key is not str or int

        Examples:
            >>> bows["Pool"]  # Lookup by name
            >>> bows[3]  # Lookup by system_id
        """
        if isinstance(key, str):
            return self._by_name[key]
        if isinstance(key, int):
            return self._by_id[key]

        msg = f"Key must be str or int, got {type(key).__name__}"
        raise TypeError(msg)

    def __setitem__(self, key: str | int, value: OE) -> None:
        """Add or update equipment in the collection.

        The key is only used to determine the operation type (add vs update).
        The actual name and system_id are taken from the equipment object itself.

        Args:
            key: Equipment name (str) or system_id (int) - must match the equipment's values
            value: Equipment item to add or update

        Raises:
            TypeError: If key is not str or int
            ValueError: If key doesn't match the equipment's name or system_id

        Examples:
            >>> # Add by name
            >>> bows["Pool"] = new_pool_bow
            >>> # Add by system_id
            >>> bows[3] = new_pool_bow
        """
        if isinstance(key, str):
            if value.name != key:
                msg = f"Equipment name '{value.name}' does not match key '{key}'"
                raise ValueError(msg)
        elif isinstance(key, int):
            if value.system_id != key:
                msg = f"Equipment system_id {value.system_id} does not match key {key}"
                raise ValueError(msg)
        else:
            msg = f"Key must be str or int, got {type(key).__name__}"
            raise TypeError(msg)

        # Check if we're updating an existing item (prioritize system_id)
        existing_item = None
        if value.system_id and value.system_id in self._by_id:
            existing_item = self._by_id[value.system_id]
        elif value.name and value.name in self._by_name:
            existing_item = self._by_name[value.name]

        if existing_item:
            # Replace existing item in place
            idx = self._items.index(existing_item)
            self._items[idx] = value
        else:
            # Add new item
            self._items.append(value)

        # Validate after modification
        self._validate()

    def __delitem__(self, key: str | int) -> None:
        """Remove equipment from the collection.

        Args:
            key: Equipment name (str) or system_id (int)

        Raises:
            KeyError: If no equipment matches the key
            TypeError: If key is not str or int

        Examples:
            >>> del bows["Pool"]  # Remove by name
            >>> del bows[3]  # Remove by system_id
        """
        # First, get the item to remove
        item = self[key]  # This will raise KeyError if not found

        # Remove from the list (indexes rebuild automatically via properties)
        self._items.remove(item)

    def __contains__(self, key: str | int) -> bool:
        """Check if equipment exists by name (str) or system_id (int).

        Args:
            key: Equipment name (str) or system_id (int)

        Returns:
            True if equipment exists, False otherwise

        Examples:
            >>> if "Pool" in bows:
            ...     print("Pool exists")
            >>> if 3 in bows:
            ...     print("System ID 3 exists")
        """
        if isinstance(key, str):
            return key in self._by_name
        if isinstance(key, int):
            return key in self._by_id

        return False

    def __iter__(self) -> Iterator[OE]:
        """Iterate over all equipment items in the collection.

        Returns:
            Iterator over equipment items

        Examples:
            >>> for bow in bows:
            ...     print(bow.name)
        """
        return iter(self._items)

    def __len__(self) -> int:
        """Get the number of equipment items in the collection.

        Returns:
            Number of items

        Examples:
            >>> len(bows)
            2
        """
        return len(self._items)

    def __repr__(self) -> str:
        """Get string representation of the collection.

        Returns:
            String representation showing item count and names
        """
        names = [f"<ID:{item.system_id},NAME:{item.name}>" for item in self._items]
        return f"EquipmentDict({names})"

    def append(self, item: OE) -> None:
        """Add or update equipment in the collection (list-like interface).

        If equipment with the same system_id or name already exists, it will be
        replaced. System_id is checked first as it's the more reliable unique identifier.

        Args:
            item: Equipment item to add or update

        Examples:
            >>> # Add new equipment
            >>> bows.append(new_pool_bow)
            >>>
            >>> # Update existing equipment (replaces if system_id or name matches)
            >>> bows.append(updated_pool_bow)
        """
        # Check if we're updating an existing item (prioritize system_id as it's guaranteed unique)
        existing_item = None
        if item.system_id and item.system_id in self._by_id:
            existing_item = self._by_id[item.system_id]
        elif item.name and item.name in self._by_name:
            existing_item = self._by_name[item.name]

        if existing_item:
            # Replace existing item in place
            idx = self._items.index(existing_item)
            self._items[idx] = item
        else:
            # Add new item
            self._items.append(item)

        # Validate after modification
        self._validate()

    def get_by_name(self, name: str) -> OE | None:
        """Get equipment by name with explicit method (returns None if not found).

        Args:
            name: Equipment name

        Returns:
            Equipment item or None if not found

        Examples:
            >>> pool = bows.get_by_name("Pool")
            >>> if pool is not None:
            ...     await pool.filters[0].turn_on()
        """
        return self._by_name.get(name)

    def get_by_id(self, system_id: int) -> OE | None:
        """Get equipment by system_id with explicit method (returns None if not found).

        Args:
            system_id: Equipment system_id

        Returns:
            Equipment item or None if not found

        Examples:
            >>> pool = bows.get_by_id(3)
            >>> if pool is not None:
            ...     print(pool.name)
        """
        return self._by_id.get(system_id)

    def get(self, key: str | int, default: OE | None = None) -> OE | None:
        """Get equipment by name or system_id with optional default.

        Args:
            key: Equipment name (str) or system_id (int)
            default: Default value to return if key not found

        Returns:
            Equipment item or default if not found

        Examples:
            >>> pool = bows.get("Pool")
            >>> pool = bows.get(3)
            >>> pool = bows.get("NonExistent", default=None)
        """
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> list[str]:
        """Get list of all equipment names.

        Returns:
            List of equipment names (excluding items without names)

        Examples:
            >>> bows.keys()
            ['Pool', 'Spa']
        """
        return list(self._by_name.keys())

    def values(self) -> list[OE]:
        """Get list of all equipment items.

        Returns:
            List of equipment items

        Examples:
            >>> for equipment in bows.values():
            ...     print(equipment.name)
        """
        return self._items.copy()

    def items(self) -> list[tuple[int | None, str | None, OE]]:
        """Get list of (system_id, name, equipment) tuples.

        Returns:
            List of (system_id, name, equipment) tuples where both system_id
            and name can be None (though at least one must be set per validation).

        Examples:
            >>> for system_id, name, bow in bows.items():
            ...     print(f"ID: {system_id}, Name: {name}")
        """
        return [(item.system_id, item.name, item) for item in self._items]


class EffectsCollection[E: Enum]:
    """A collection that provides both attribute and dict-like access to light effects.

    This class wraps a list of light shows and exposes them through multiple access patterns:
    - Attribute access: `effects.VOODOO_LOUNGE`
    - Dict-like access: `effects["VOODOO_LOUNGE"]`
    - Iteration: `for effect in effects: ...`
    - Length: `len(effects)`
    - Membership: `effect in effects`

    The collection is read-only and provides type-safe access to only the shows
    supported by a specific light model.

    Example:
        >>> light = pool.lights["Pool Light"]
        >>> # Attribute access
        >>> await light.set_show(light.effects.TROPICAL)
        >>> # Dict-like access
        >>> await light.set_show(light.effects["TROPICAL"])
        >>> # Check if a show is available
        >>> if "VOODOO_LOUNGE" in light.effects:
        ...     await light.set_show(light.effects.VOODOO_LOUNGE)
        >>> # Iterate through available shows
        >>> for effect in light.effects:
        ...     print(f"{effect.name}: {effect.value}")
    """

    def __init__(self, effects: list[E]) -> None:
        """Initialize the effects collection.

        Args:
            effects: List of light show enums available for this light model.
        """
        self._effects = effects
        # Create a lookup dict for fast access by name
        self._effects_by_name = {effect.name: effect for effect in effects}

    def __getattr__(self, name: str) -> E:
        """Enable attribute access to effects by name.

        Args:
            name: The name of the light show (e.g., "VOODOO_LOUNGE")

        Returns:
            The light show enum value.

        Raises:
            AttributeError: If the show name is not available for this light model.
        """
        if name.startswith("_"):
            # Avoid infinite recursion for internal attributes
            msg = f"'{type(self).__name__}' object has no attribute '{name}'"
            raise AttributeError(msg)

        try:
            return self._effects_by_name[name]
        except KeyError as exc:
            msg = f"Light effect '{name}' is not available for this light model"
            raise AttributeError(msg) from exc

    def __getitem__(self, key: str | int) -> E:
        """Enable dict-like and index access to effects.

        Args:
            key: Either the effect name (str) or index position (int)

        Returns:
            The light show enum value.

        Raises:
            KeyError: If the show name is not available for this light model.
            IndexError: If the index is out of range.
            TypeError: If key is not a string or integer.
        """
        if isinstance(key, str):
            try:
                return self._effects_by_name[key]
            except KeyError as exc:
                msg = f"Light effect '{key}' is not available for this light model"
                raise KeyError(msg) from exc
        elif isinstance(key, int):
            return self._effects[key]
        else:
            msg = f"indices must be integers or strings, not {type(key).__name__}"
            raise TypeError(msg)

    def __contains__(self, item: str | E) -> bool:
        """Check if an effect is available in this collection.

        Args:
            item: Either the effect name (str) or the effect enum value

        Returns:
            True if the effect is available, False otherwise.

        Note:
            When checking enum membership, this uses identity checking (is),
            not value equality (==). This ensures that only the exact enum
            instance from this collection's type is matched, even if different
            enum types share the same value.
        """
        if isinstance(item, str):
            return item in self._effects_by_name
        # Use identity check to ensure exact type match
        return any(item is effect for effect in self._effects)

    def __iter__(self) -> Iterator[E]:
        """Enable iteration over the effects."""
        return iter(self._effects)

    def __len__(self) -> int:
        """Return the number of effects in the collection."""
        return len(self._effects)

    def __repr__(self) -> str:
        """Return a string representation of the collection."""
        effect_names = [effect.name for effect in self._effects]
        return f"EffectsCollection({effect_names})"

    def to_list(self) -> list[E]:
        """Return the underlying list of effects.

        Returns:
            A list of all light show enums in this collection.
        """
        return self._effects.copy()


# Type alias for light effects specifically
LightEffectsCollection = EffectsCollection[LightShows]
