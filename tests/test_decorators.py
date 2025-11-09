"""Tests for equipment control method decorators.

Focuses on:
- @control_method decorator behavior
- Readiness checking
- State dirtying
- Error message generation
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from pyomnilogic_local.decorators import control_method
from pyomnilogic_local.util import OmniEquipmentNotReadyError

# ============================================================================
# Test Fixtures
# ============================================================================


class MockEquipment:
    """Mock equipment class for testing decorators."""

    def __init__(self, is_ready: bool = True):
        """Initialize mock equipment.

        Args:
            is_ready: Whether equipment should report as ready
        """
        self.is_ready = is_ready
        self._omni = MagicMock()
        self._omni._telemetry_dirty = False
        self.method_called = False
        self.method_args: tuple[Any, ...] | None = None
        self.method_kwargs: dict[str, Any] | None = None

    @control_method
    async def turn_on(self) -> None:
        """Mock turn_on method."""
        self.method_called = True

    @control_method
    async def turn_off(self) -> None:
        """Mock turn_off method."""
        self.method_called = True

    @control_method
    async def set_temperature(self, temperature: int) -> None:
        """Mock set_temperature method with args."""
        self.method_called = True
        self.method_args = (temperature,)

    @control_method
    async def set_complex_operation(self, param1: int, param2: str, flag: bool = False) -> str:
        """Mock method with args, kwargs, and return value."""
        self.method_called = True
        self.method_args = (param1, param2)
        self.method_kwargs = {"flag": flag}
        return f"result: {param1}, {param2}, {flag}"


# ============================================================================
# @control_method Decorator Tests
# ============================================================================


@pytest.mark.asyncio
async def test_control_method_when_ready_executes_function() -> None:
    """Test that control_method executes the wrapped function when equipment is ready."""
    equipment = MockEquipment(is_ready=True)

    await equipment.turn_on()

    assert equipment.method_called is True


@pytest.mark.asyncio
async def test_control_method_when_not_ready_raises_error() -> None:
    """Test that control_method raises OmniEquipmentNotReadyError when equipment is not ready."""
    equipment = MockEquipment(is_ready=False)

    with pytest.raises(OmniEquipmentNotReadyError) as exc_info:
        await equipment.turn_on()

    assert "Cannot turn on: equipment is not ready to accept commands" in str(exc_info.value)
    assert equipment.method_called is False


@pytest.mark.asyncio
async def test_control_method_marks_telemetry_dirty() -> None:
    """Test that control_method marks telemetry as dirty after successful execution."""
    equipment = MockEquipment(is_ready=True)

    assert equipment._omni._telemetry_dirty is False

    await equipment.turn_on()

    assert equipment._omni._telemetry_dirty is True


@pytest.mark.asyncio
async def test_control_method_does_not_mark_dirty_if_not_ready() -> None:
    """Test that control_method does not mark state dirty if readiness check fails."""
    equipment = MockEquipment(is_ready=False)

    with pytest.raises(OmniEquipmentNotReadyError):
        await equipment.turn_on()

    assert equipment._omni._telemetry_dirty is False


@pytest.mark.asyncio
async def test_control_method_passes_arguments() -> None:
    """Test that control_method properly passes arguments to wrapped function."""
    equipment = MockEquipment(is_ready=True)

    await equipment.set_temperature(75)

    assert equipment.method_called is True
    assert equipment.method_args == (75,)


@pytest.mark.asyncio
async def test_control_method_passes_kwargs() -> None:
    """Test that control_method properly passes keyword arguments to wrapped function."""
    equipment = MockEquipment(is_ready=True)

    result = await equipment.set_complex_operation(42, "test", flag=True)

    assert equipment.method_called is True
    assert equipment.method_args == (42, "test")
    assert equipment.method_kwargs == {"flag": True}
    assert result == "result: 42, test, True"


@pytest.mark.asyncio
async def test_control_method_error_message_for_different_methods() -> None:
    """Test that control_method generates appropriate error messages for different method names."""
    equipment = MockEquipment(is_ready=False)

    # Test turn_on
    with pytest.raises(OmniEquipmentNotReadyError) as exc_info:
        await equipment.turn_on()
    assert "Cannot turn on:" in str(exc_info.value)

    # Test turn_off
    with pytest.raises(OmniEquipmentNotReadyError) as exc_info:
        await equipment.turn_off()
    assert "Cannot turn off:" in str(exc_info.value)

    # Test set_temperature
    with pytest.raises(OmniEquipmentNotReadyError) as exc_info:
        await equipment.set_temperature(75)
    assert "Cannot set temperature:" in str(exc_info.value)

    # Test complex operation
    with pytest.raises(OmniEquipmentNotReadyError) as exc_info:
        await equipment.set_complex_operation(1, "test")
    assert "Cannot set complex operation:" in str(exc_info.value)


@pytest.mark.asyncio
async def test_control_method_preserves_function_metadata() -> None:
    """Test that control_method preserves the wrapped function's metadata."""
    equipment = MockEquipment(is_ready=True)

    # Check that functools.wraps preserved the original function name and docstring
    assert equipment.turn_on.__name__ == "turn_on"
    assert equipment.turn_on.__doc__ == "Mock turn_on method."
    assert equipment.set_temperature.__name__ == "set_temperature"
    assert equipment.set_temperature.__doc__ is not None
    assert "args" in equipment.set_temperature.__doc__


@pytest.mark.asyncio
async def test_control_method_without_omni_reference() -> None:
    """Test that control_method logs warning when equipment lacks _omni reference."""
    equipment = MockEquipment(is_ready=True)
    del equipment._omni

    # Should still execute the function without error, just log a warning
    await equipment.turn_on()

    assert equipment.method_called is True
