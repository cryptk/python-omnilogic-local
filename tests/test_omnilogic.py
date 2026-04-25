from typing import Any

from pyomnilogic_local.omnilogic import _check_duplicate_item_names


class FakeEquipment:
    """A fake equipment class for testing duplicate detection."""

    def __init__(self, system_id: int, name: str) -> None:
        self.system_id = system_id
        self.name = name


def test__check_duplicate_item_names() -> None:
    """Test the duplicate name warning helper directly."""
    items: Any = [
        FakeEquipment(1, "Solar"),
        FakeEquipment(2, "Solar"),
        FakeEquipment(3, "Gas"),
        FakeEquipment(4, "Gas"),
    ]
    warning = _check_duplicate_item_names(
        items,
        source_id="127.0.0.1:10444",
    )

    assert warning == (
        "OmniLogic 127.0.0.1:10444 contains multiple items with the same name:\n"
        "  - Gas: IDs 3, 4\n"
        "  - Solar: IDs 1, 2\n"
        "Name-based lookups will return the first match. "
        "Consider using system_id-based lookups for reliability "
        "or renaming equipment on the OmniLogic controller to avoid duplicates."
    )


def test__check_duplicate_item_names_different_host() -> None:
    """Test the duplicate name warning helper with a different host."""
    items: Any = [
        FakeEquipment(1, "Solar"),
        FakeEquipment(2, "Solar"),
    ]
    warning = _check_duplicate_item_names(
        items,
        source_id="10.0.0.1:3000",
    )

    assert warning is not None
    assert "OmniLogic 10.0.0.1:3000 contains multiple items with the same name:" in warning


def test__check_duplicate_item_names_no_duplicates() -> None:
    """Test that the helper returns None when there are no duplicates."""
    items: Any = [
        FakeEquipment(1, "Solar"),
        FakeEquipment(2, "Gas"),
    ]
    warning = _check_duplicate_item_names(
        items,
        source_id="127.0.0.1:10444",
    )
    assert warning is None
