"""Custom collection types for OmniLogic equipment management."""

import logging
from collections import Counter
from collections.abc import Iterator
from typing import Any, Generic, TypeVar, overload

from pyomnilogic_local._base import OmniEquipment

_LOGGER = logging.getLogger(__name__)

# Track which duplicate names we've already warned about to avoid log spam
_WARNED_DUPLICATE_NAMES: set[str] = set()

# Type variable for equipment types
T = TypeVar("T", bound=OmniEquipment[Any, Any])


class EquipmentDict(Generic[T]):
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

    def __init__(self, items: list[T] | None = None) -> None:
        """Initialize the equipment collection.

        Args:
            items: Optional list of equipment items to populate the collection.

        Raises:
            ValueError: If any item has neither a system_id nor a name.
        """
        self._items: list[T] = items if items is not None else []
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
            raise ValueError(
                f"Equipment collection contains {len(invalid_items)} item(s) "
                "with neither a system_id nor a name. All equipment must have "
                "at least one identifier for addressing."
            )

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
    def _by_name(self) -> dict[str, T]:
        """Dynamically build name-to-equipment mapping."""
        return {item.name: item for item in self._items if item.name is not None}

    @property
    def _by_id(self) -> dict[int, T]:
        """Dynamically build system_id-to-equipment mapping."""
        return {item.system_id: item for item in self._items if item.system_id is not None}

    @overload
    def __getitem__(self, key: str) -> T: ...

    @overload
    def __getitem__(self, key: int) -> T: ...

    def __getitem__(self, key: str | int) -> T:
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

        raise TypeError(f"Key must be str or int, got {type(key).__name__}")

    def __setitem__(self, key: str | int, value: T) -> None:
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
                raise ValueError(f"Equipment name '{value.name}' does not match key '{key}'")
        elif isinstance(key, int):
            if value.system_id != key:
                raise ValueError(f"Equipment system_id {value.system_id} does not match key {key}")
        else:
            raise TypeError(f"Key must be str or int, got {type(key).__name__}")

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

    def __iter__(self) -> Iterator[T]:
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
        # names = [item.name or f"<ID:{item.system_id}>" for item in self._items]
        return f"EquipmentDict({names})"

    def append(self, item: T) -> None:
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

    def get_by_name(self, name: str) -> T | None:
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

    def get_by_id(self, system_id: int) -> T | None:
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

    def get(self, key: str | int, default: T | None = None) -> T | None:
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

    def values(self) -> list[T]:
        """Get list of all equipment items.

        Returns:
            List of equipment items

        Examples:
            >>> for equipment in bows.values():
            ...     print(equipment.name)
        """
        return self._items.copy()

    def items(self) -> list[tuple[int | None, str | None, T]]:
        """Get list of (system_id, name, equipment) tuples.

        Returns:
            List of (system_id, name, equipment) tuples where both system_id
            and name can be None (though at least one must be set per validation).

        Examples:
            >>> for system_id, name, bow in bows.items():
            ...     print(f"ID: {system_id}, Name: {name}")
        """
        return [(item.system_id, item.name, item) for item in self._items]
