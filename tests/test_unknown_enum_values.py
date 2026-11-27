"""Unknown enum values in telemetry must not fail the whole parse.

Controllers report values the enums don't list (new firmware, undocumented states: see #155,
and FilterWhyOn 20-22). A single unknown value used to fail Telemetry validation, so every piece
of equipment disappeared until a library release.
"""

from __future__ import annotations

import json
import logging
import pathlib
import re

import pytest

from pyomnilogic_local.models.exceptions import OmniParsingError
from pyomnilogic_local.models.telemetry import Telemetry, TelemetryFilter, UnknownEnumValue
from pyomnilogic_local.omnitypes import FilterState, FilterWhyOn, HeaterState, RelayWhyOn
from pyomnilogic_local.util import is_unknown_member

TELEMETRY = json.loads((pathlib.Path(__file__).parent / "fixtures" / "issue-60.json").read_text(encoding="utf-8"))["telemetry"]


def with_attr(xml: str, attr: str, value: str) -> str:
    """The telemetry with the first occurrence of attr set to value."""
    new, count = re.subn(rf'{attr}="[^"]*"', f'{attr}="{value}"', xml, count=1)
    assert count == 1, attr
    return new


@pytest.mark.parametrize(
    "attr",
    ["state", "relayState", "whyOn", "filterState", "valvePosition", "whyFilterIsOn", "heaterState", "Mode", "whyHeaterIsOn", "lightState"],
)
def test_unknown_value_parses(attr: str) -> None:
    """An unknown value in any enum-typed attribute no longer fails the whole parse."""
    telemetry = Telemetry.load_xml(with_attr(TELEMETRY, attr, "201"))
    assert telemetry.backyard is not None


def test_unknown_value_becomes_a_pseudo_member() -> None:
    """The value is kept as an UNKNOWN_<n> member of the right enum."""
    telemetry = Telemetry.load_xml(with_attr(TELEMETRY, "whyFilterIsOn", "123"))
    filt = next(t for t in telemetry.filter or [] if t.system_id == 3)
    assert isinstance(filt, TelemetryFilter)
    assert isinstance(filt.why_on, FilterWhyOn)
    assert filt.why_on.name == "UNKNOWN_123"
    assert str(filt.why_on) == "Unknown 123"
    assert filt.why_on == 123


def test_known_values_unchanged() -> None:
    """Known values still map to their named members."""
    telemetry = Telemetry.load_xml(TELEMETRY)
    filt = next(t for t in telemetry.filter or [] if t.system_id == 3)
    assert filt.why_on is FilterWhyOn.MANUAL_ON
    assert filt.state is FilterState.ON


def test_pseudo_members_are_reused_and_not_listed() -> None:
    """The same value gives the same pseudo-member, and iteration lists only real members."""
    assert HeaterState(77) is HeaterState(77)
    assert "UNKNOWN_77" not in HeaterState.__members__
    assert all(not m.name.startswith("UNKNOWN_") for m in HeaterState)


def test_warns_once_per_value(caplog: pytest.LogCaptureFixture) -> None:
    """A warning is logged the first time each unknown value is seen."""
    with caplog.at_level(logging.WARNING, logger="pyomnilogic_local.util"):
        RelayWhyOn(181)
        RelayWhyOn(181)
        RelayWhyOn(182)
    warnings = [r.getMessage() for r in caplog.records if "Unknown RelayWhyOn" in r.getMessage()]
    assert len(warnings) == 2


@pytest.mark.parametrize("bad", ["x", "", "1.5x"])
def test_non_integers_still_rejected(bad: str) -> None:
    """Values that are not integers still fail validation."""
    with pytest.raises(OmniParsingError):
        Telemetry.load_xml(with_attr(TELEMETRY, "whyFilterIsOn", bad))


def test_unknown_values_are_listed() -> None:
    """unknown_enum_values() says which equipment, field, enum and value."""
    telemetry = Telemetry.load_xml(with_attr(with_attr(TELEMETRY, "whyFilterIsOn", "124"), "heaterState", "125"))
    assert telemetry.unknown_enum_values() == [
        UnknownEnumValue("TelemetryFilter", 3, "why_on", "FilterWhyOn", 124),
        UnknownEnumValue("TelemetryHeater", 5, "state", "HeaterState", 125),
    ]
    assert str(telemetry.unknown_enum_values()[0]) == "FilterWhyOn 124 (TelemetryFilter 3, why_on)"


def test_no_unknown_values() -> None:
    """Fully known telemetry lists nothing, and placeholder members like FilterWhyOn.UNKNOWN_1 are real members."""
    assert Telemetry.load_xml(TELEMETRY).unknown_enum_values() == []
    assert not is_unknown_member(FilterWhyOn.UNKNOWN_1)
    assert is_unknown_member(FilterWhyOn(126))
    assert not is_unknown_member(126)


def test_strict_enums_rejects_unknown_values() -> None:
    """strict_enums=True fails the parse on an unknown value, naming it."""
    xml = with_attr(TELEMETRY, "whyFilterIsOn", "127")
    with pytest.raises(OmniParsingError, match=r"FilterWhyOn 127"):
        Telemetry.load_xml(xml, strict_enums=True)
    Telemetry.load_xml(TELEMETRY, strict_enums=True)
