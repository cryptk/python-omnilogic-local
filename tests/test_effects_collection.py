"""Tests for the EffectsCollection class."""

import pytest

from pyomnilogic_local.collections import EffectsCollection, LightEffectsCollection
from pyomnilogic_local.omnitypes import (
    ColorLogicShow25,
    ColorLogicShow40,
    ColorLogicShowUCL,
)


class TestEffectsCollection:
    """Test suite for EffectsCollection."""

    def test_attribute_access(self) -> None:
        """Test that we can access effects by attribute name."""
        effects = EffectsCollection(list(ColorLogicShow25))

        # Test attribute access
        assert effects.VOODOO_LOUNGE == ColorLogicShow25.VOODOO_LOUNGE
        assert effects.EMERALD == ColorLogicShow25.EMERALD
        assert effects.DEEP_BLUE_SEA == ColorLogicShow25.DEEP_BLUE_SEA

    def test_dict_like_access(self) -> None:
        """Test that we can access effects by string key."""
        effects = EffectsCollection(list(ColorLogicShow25))

        # Test dict-like access
        assert effects["VOODOO_LOUNGE"] == ColorLogicShow25.VOODOO_LOUNGE
        assert effects["EMERALD"] == ColorLogicShow25.EMERALD
        assert effects["DEEP_BLUE_SEA"] == ColorLogicShow25.DEEP_BLUE_SEA

    def test_index_access(self) -> None:
        """Test that we can access effects by index."""
        effects = EffectsCollection(list(ColorLogicShow25))

        # Test index access
        assert effects[0] == ColorLogicShow25.VOODOO_LOUNGE
        assert effects[1] == ColorLogicShow25.DEEP_BLUE_SEA
        assert effects[-1] == ColorLogicShow25.COOL_CABARET

    def test_attribute_error(self) -> None:
        """Test that accessing non-existent effect raises AttributeError."""
        effects = EffectsCollection(list(ColorLogicShow25))

        with pytest.raises(AttributeError, match="Light effect 'NONEXISTENT' is not available"):
            _ = effects.NONEXISTENT

    def test_key_error(self) -> None:
        """Test that accessing non-existent effect by key raises KeyError."""
        effects = EffectsCollection(list(ColorLogicShow25))

        with pytest.raises(KeyError, match="Light effect 'NONEXISTENT' is not available"):
            _ = effects["NONEXISTENT"]

    def test_index_error(self) -> None:
        """Test that accessing out of range index raises IndexError."""
        effects = EffectsCollection(list(ColorLogicShow25))

        with pytest.raises(IndexError):
            _ = effects[999]

    def test_type_error_invalid_key(self) -> None:
        """Test that accessing with invalid key type raises TypeError."""
        effects = EffectsCollection(list(ColorLogicShow25))

        with pytest.raises(TypeError, match="indices must be integers or strings"):
            _ = effects[3.14]  # type: ignore

    def test_contains_string(self) -> None:
        """Test membership testing with string names."""
        effects = EffectsCollection(list(ColorLogicShow25))

        assert "VOODOO_LOUNGE" in effects
        assert "EMERALD" in effects
        assert "NONEXISTENT" not in effects

    def test_contains_enum(self) -> None:
        """Test membership testing with enum values."""
        effects = EffectsCollection(list(ColorLogicShow25))

        assert ColorLogicShow25.VOODOO_LOUNGE in effects
        assert ColorLogicShow25.EMERALD in effects
        # Test that an enum from a different type is not in the collection
        # Note: We need to check by type since enum values might overlap
        ucl_effects = EffectsCollection(list(ColorLogicShowUCL))
        assert ColorLogicShowUCL.ROYAL_BLUE in ucl_effects
        assert ColorLogicShowUCL.ROYAL_BLUE not in effects  # type: ignore  # ROYAL_BLUE doesn't exist in Show25

    def test_iteration(self) -> None:
        """Test iterating over effects."""
        effects = EffectsCollection(list(ColorLogicShow25))

        # Test that we can iterate
        effects_list = list(effects)
        assert len(effects_list) == len(ColorLogicShow25)
        assert effects_list[0] == ColorLogicShow25.VOODOO_LOUNGE

        # Test iteration in for loop
        count = 0
        for effect in effects:
            assert isinstance(effect, ColorLogicShow25)
            count += 1
        assert count == len(ColorLogicShow25)

    def test_length(self) -> None:
        """Test that len() works correctly."""
        effects25 = EffectsCollection(list(ColorLogicShow25))
        effects40 = EffectsCollection(list(ColorLogicShow40))
        effectsUCL = EffectsCollection(list(ColorLogicShowUCL))  # pylint: disable=invalid-name

        assert len(effects25) == len(ColorLogicShow25)
        assert len(effects40) == len(ColorLogicShow40)
        assert len(effectsUCL) == len(ColorLogicShowUCL)

    def test_repr(self) -> None:
        """Test string representation."""
        effects = EffectsCollection(list(ColorLogicShow25))

        repr_str = repr(effects)
        assert "EffectsCollection" in repr_str
        assert "VOODOO_LOUNGE" in repr_str
        assert "EMERALD" in repr_str

    def test_to_list(self) -> None:
        """Test converting back to a list."""
        original_list = list(ColorLogicShow25)
        effects = EffectsCollection(original_list)

        result_list = effects.to_list()
        assert result_list == original_list
        # Verify it's a copy
        assert result_list is not original_list

    def test_type_alias(self) -> None:
        """Test that the LightEffectsCollection type alias works."""
        effects: LightEffectsCollection = EffectsCollection(list(ColorLogicShow25))

        # Should work with any LightShows type
        assert effects.VOODOO_LOUNGE == ColorLogicShow25.VOODOO_LOUNGE

    def test_different_show_types(self) -> None:
        """Test that different show types are correctly distinguished."""
        effects25 = EffectsCollection(list(ColorLogicShow25))
        effectsUCL = EffectsCollection(list(ColorLogicShowUCL))  # pylint: disable=invalid-name

        # UCL has ROYAL_BLUE, 2.5 doesn't
        assert "ROYAL_BLUE" not in effects25
        assert "ROYAL_BLUE" in effectsUCL

        # Both have VOODOO_LOUNGE and they're from different enums
        assert effects25.VOODOO_LOUNGE is ColorLogicShow25.VOODOO_LOUNGE
        assert effectsUCL.VOODOO_LOUNGE is ColorLogicShowUCL.VOODOO_LOUNGE
        # Even though they have the same value (0), they're different enum types
        assert type(effects25.VOODOO_LOUNGE) is not type(effectsUCL.VOODOO_LOUNGE)  # type: ignore
        assert isinstance(effects25.VOODOO_LOUNGE, ColorLogicShow25)
        assert isinstance(effectsUCL.VOODOO_LOUNGE, ColorLogicShowUCL)
