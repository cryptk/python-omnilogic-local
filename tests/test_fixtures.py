"""Tests for validating real-world fixture data from GitHub issues.

This test suite uses JSON fixture files from tests/fixtures/ directory, which contain
actual MSPConfig and Telemetry XML data from real OmniLogic hardware. Each fixture
represents a specific configuration reported in GitHub issues.

The tests validate:
- MSPConfig: System IDs, equipment names, counts, and types
- Telemetry: System IDs, state values, and telemetry counts
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest
from pytest_subtests import SubTests

from pyomnilogic_local.models.mspconfig import MSPConfig
from pyomnilogic_local.models.telemetry import Telemetry
from pyomnilogic_local.omnitypes import OmniType

# Path to fixtures directory
FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> dict[str, str]:
    """Load a fixture file and return the mspconfig and telemetry XML strings.

    Args:
        filename: Name of the fixture file (e.g., "issue-60.json")

    Returns:
        Dictionary with 'mspconfig' and 'telemetry' keys containing XML strings
    """
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_equipment_by_type(msp: MSPConfig, omni_type: OmniType) -> list[Any]:
    """Get all equipment of a specific type from MSPConfig.

    Args:
        msp: Parsed MSPConfig
        omni_type: Type of equipment to find

    Returns:
        List of equipment matching the type
    """
    equipment = []
    # Check backyard-level equipment
    for attr_name in ("relay", "sensor", "colorlogic_light"):
        if items := getattr(msp.backyard, attr_name, None):
            for item in items:
                if item.omni_type == omni_type:
                    equipment.append(item)

    # Check BoW-level equipment
    if msp.backyard.bow:  # pylint: disable=too-many-nested-blocks
        for bow in msp.backyard.bow:
            for attr_name in ("filter", "heater", "pump", "relay", "sensor", "colorlogic_light", "chlorinator"):
                if items := getattr(bow, attr_name, None):
                    # Handle single items or lists
                    items_list = items if isinstance(items, list) else [items]
                    for item in items_list:
                        if item.omni_type == omni_type:
                            equipment.append(item)
                        # Check child equipment (e.g., heater equipment within virtual heater)
                        if hasattr(item, "heater_equipment") and item.heater_equipment:
                            for child in item.heater_equipment:
                                if child.omni_type == omni_type:
                                    equipment.append(child)
    return equipment


class TestIssue144:
    """Tests for issue-144.json fixture.

    System configuration:
    - 1 Body of Water (Pool)
    - ColorLogic UCL light
    - Heat pump
    - Filter pump
    """

    @pytest.fixture
    def fixture_data(self) -> dict[str, str]:
        """Load issue-144 fixture data."""
        return load_fixture("issue-144.json")

    def test_mspconfig(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test MSPConfig parsing for issue-144."""
        msp = MSPConfig.load_xml(fixture_data["mspconfig"])

        with subtests.test(msg="backyard exists"):
            assert msp.backyard is not None
            assert msp.backyard.name == "Backyard"

        with subtests.test(msg="body of water count"):
            assert msp.backyard.bow is not None
            assert len(msp.backyard.bow) == 1

        with subtests.test(msg="pool configuration"):
            assert msp.backyard.bow is not None
            pool = msp.backyard.bow[0]
            assert pool.system_id == 3
            assert pool.name == "Pool"
            assert pool.omni_type == OmniType.BOW

        with subtests.test(msg="filter configuration"):
            filters = get_equipment_by_type(msp, OmniType.FILTER)
            assert len(filters) == 1
            assert filters[0].system_id == 4
            assert filters[0].name == "Filter Pump"

        with subtests.test(msg="heater equipment configuration"):
            heaters = get_equipment_by_type(msp, OmniType.HEATER_EQUIP)
            assert len(heaters) == 1
            assert heaters[0].system_id == 16
            assert heaters[0].name == "Heat Pump"

        with subtests.test(msg="colorlogic light configuration"):
            lights = get_equipment_by_type(msp, OmniType.CL_LIGHT)
            assert len(lights) == 1
            assert lights[0].system_id == 9
            assert lights[0].name == "UCL"

    def test_telemetry(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test Telemetry parsing for issue-144."""
        telem = Telemetry.from_xml(fixture_data["telemetry"])

        with subtests.test(msg="backyard telemetry"):
            assert telem.backyard is not None
            assert telem.backyard.system_id == 0
            assert telem.backyard.air_temp == 66

        with subtests.test(msg="body of water telemetry"):
            assert len(telem.bow) == 1
            pool = telem.bow[0]
            assert pool.system_id == 3
            assert pool.water_temp == -1  # No valid reading

        with subtests.test(msg="filter telemetry"):
            assert telem.filter is not None
            assert len(telem.filter) == 1
            filter_telem = telem.filter[0]
            assert filter_telem.system_id == 4

        with subtests.test(msg="virtual heater telemetry"):
            assert telem.virtual_heater is not None
            assert len(telem.virtual_heater) == 1
            vh = telem.virtual_heater[0]
            assert vh.system_id == 15
            assert vh.current_set_point == 65

        with subtests.test(msg="heater equipment telemetry"):
            assert telem.heater is not None
            assert len(telem.heater) == 1
            heater = telem.heater[0]
            assert heater.system_id == 16

        with subtests.test(msg="colorlogic light telemetry"):
            assert telem.colorlogic_light is not None
            assert len(telem.colorlogic_light) == 1
            light = telem.colorlogic_light[0]
            assert light.system_id == 9


class TestIssue163:
    """Tests for issue-163.json fixture.

    System configuration:
    - 1 Body of Water (Pool)
    - Salt chlorinator
    - Variable speed pump
    - Fountain pump
    """

    @pytest.fixture
    def fixture_data(self) -> dict[str, str]:
        """Load issue-163 fixture data."""
        return load_fixture("issue-163.json")

    def test_mspconfig(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test MSPConfig parsing for issue-163."""
        msp = MSPConfig.load_xml(fixture_data["mspconfig"])

        with subtests.test(msg="backyard exists"):
            assert msp.backyard is not None
            assert msp.backyard.name == "Backyard"

        with subtests.test(msg="body of water count"):
            assert msp.backyard.bow is not None
            assert len(msp.backyard.bow) == 1

        with subtests.test(msg="pool configuration"):
            assert msp.backyard.bow is not None
            pool = msp.backyard.bow[0]
            assert pool.system_id == 10
            assert pool.name == "Pool"
            assert pool.omni_type == OmniType.BOW

        with subtests.test(msg="filter configuration"):
            filters = get_equipment_by_type(msp, OmniType.FILTER)
            assert len(filters) == 1
            assert filters[0].system_id == 11
            assert filters[0].name == "Filter Pump"

        with subtests.test(msg="chlorinator configuration"):
            chlorinators = get_equipment_by_type(msp, OmniType.CHLORINATOR)
            assert len(chlorinators) == 1
            assert chlorinators[0].system_id == 12
            assert chlorinators[0].name == "Chlorinator"

        with subtests.test(msg="pump configuration"):
            pumps = get_equipment_by_type(msp, OmniType.PUMP)
            assert len(pumps) == 1
            assert pumps[0].system_id == 14
            assert pumps[0].name == "Fountain"

        with subtests.test(msg="backyard sensors"):
            assert msp.backyard.sensor is not None
            assert len(msp.backyard.sensor) == 1
            assert msp.backyard.sensor[0].system_id == 16

    def test_telemetry(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test Telemetry parsing for issue-163."""
        telem = Telemetry.from_xml(fixture_data["telemetry"])

        with subtests.test(msg="backyard telemetry"):
            assert telem.backyard is not None
            assert telem.backyard.system_id == 0
            assert telem.backyard.air_temp == 110

        with subtests.test(msg="body of water telemetry"):
            assert len(telem.bow) == 1
            pool = telem.bow[0]
            assert pool.system_id == 10
            assert pool.water_temp == 84

        with subtests.test(msg="filter telemetry"):
            assert telem.filter is not None
            assert len(telem.filter) == 1
            filter_telem = telem.filter[0]
            assert filter_telem.system_id == 11
            assert filter_telem.speed == 60
            assert filter_telem.state.name == "ON"

        with subtests.test(msg="chlorinator telemetry"):
            assert telem.chlorinator is not None
            assert len(telem.chlorinator) == 1
            chlor = telem.chlorinator[0]
            assert chlor.system_id == 12
            assert chlor.status_raw == 68
            assert chlor.avg_salt_level == 2942

        with subtests.test(msg="pump telemetry"):
            assert telem.pump is not None
            assert len(telem.pump) == 1
            pump = telem.pump[0]
            assert pump.system_id == 14
            assert pump.speed == 0
            assert pump.state.name == "OFF"


class TestIssue60:
    """Tests for issue-60.json fixture.

    System configuration:
    - 2 Bodies of Water (Pool and Spa)
    - Multiple lights, relays, pumps, heaters
    - ColorLogic lights with V2 support
    - Solar and gas heaters
    """

    @pytest.fixture
    def fixture_data(self) -> dict[str, str]:
        """Load issue-60 fixture data."""
        return load_fixture("issue-60.json")

    def test_mspconfig(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test MSPConfig parsing for issue-60."""
        msp = MSPConfig.load_xml(fixture_data["mspconfig"])

        with subtests.test(msg="backyard exists"):
            assert msp.backyard is not None
            assert msp.backyard.name == "Backyard"

        with subtests.test(msg="body of water count"):
            assert msp.backyard.bow is not None
            assert len(msp.backyard.bow) == 2

        with subtests.test(msg="pool configuration"):
            assert msp.backyard.bow is not None
            pool = msp.backyard.bow[0]
            assert pool.system_id == 1
            assert pool.name == "Pool"
            assert pool.omni_type == OmniType.BOW

        with subtests.test(msg="spa configuration"):
            assert msp.backyard.bow is not None
            spa = msp.backyard.bow[1]
            assert spa.system_id == 8
            assert spa.name == "Spa"

        with subtests.test(msg="colorlogic light count"):
            lights = get_equipment_by_type(msp, OmniType.CL_LIGHT)
            assert len(lights) == 3
            # Pool has 2 lights, Spa has 1
            light_ids = sorted([light.system_id for light in lights])
            assert light_ids == [13, 23, 24]

        with subtests.test(msg="relay count"):
            relays = get_equipment_by_type(msp, OmniType.RELAY)
            assert len(relays) >= 3
            relay_names = [relay.name for relay in relays]
            assert "Yard Lights" in relay_names
            assert "Blower" in relay_names

        with subtests.test(msg="pump count"):
            pumps = get_equipment_by_type(msp, OmniType.PUMP)
            assert len(pumps) == 1
            assert pumps[0].system_id == 14
            assert pumps[0].name == "Jet"

        with subtests.test(msg="filter count"):
            filters = get_equipment_by_type(msp, OmniType.FILTER)
            # Should have 2 filters (one per BoW)
            assert len(filters) == 2

        with subtests.test(msg="heater equipment"):
            heaters = get_equipment_by_type(msp, OmniType.HEATER_EQUIP)
            # Should have 4 heater equipment (2 gas + 2 solar)
            assert len(heaters) == 4
            heater_names = [h.name for h in heaters]
            assert heater_names.count("Gas") == 2
            assert heater_names.count("Solar") == 2

    def test_telemetry(self, fixture_data: dict[str, str], subtests: SubTests) -> None:
        """Test Telemetry parsing for issue-60."""
        telem = Telemetry.from_xml(fixture_data["telemetry"])

        with subtests.test(msg="backyard telemetry"):
            assert telem.backyard is not None
            assert telem.backyard.system_id == 0
            assert telem.backyard.air_temp == 67

        with subtests.test(msg="body of water telemetry count"):
            assert len(telem.bow) == 2
            bow_ids = sorted([bow.system_id for bow in telem.bow])
            assert bow_ids == [1, 8]

        with subtests.test(msg="pool water temp"):
            pool_bow = [bow for bow in telem.bow if bow.system_id == 1][0]
            assert pool_bow.water_temp == 74

        with subtests.test(msg="spa water temp"):
            spa_bow = [bow for bow in telem.bow if bow.system_id == 8][0]
            assert spa_bow.water_temp == -1  # No valid reading

        with subtests.test(msg="filter telemetry"):
            assert telem.filter is not None
            assert len(telem.filter) == 2
            # Pool filter running
            pool_filter = [f for f in telem.filter if f.system_id == 3][0]
            assert pool_filter.speed == 31
            assert pool_filter.power == 79

        with subtests.test(msg="colorlogic light telemetry"):
            assert telem.colorlogic_light is not None
            assert len(telem.colorlogic_light) == 3
            light_ids = sorted([light.system_id for light in telem.colorlogic_light])
            assert light_ids == [13, 23, 24]

        with subtests.test(msg="relay telemetry"):
            assert telem.relay is not None
            assert len(telem.relay) == 3
            # Check yard lights relay is on
            yard_relay = [r for r in telem.relay if r.system_id == 27][0]
            assert yard_relay.state.value == 1  # ON

        with subtests.test(msg="pump telemetry"):
            assert telem.pump is not None
            assert len(telem.pump) == 1
            assert telem.pump[0].system_id == 14
            assert telem.pump[0].state.value == 0  # OFF

        with subtests.test(msg="heater telemetry"):
            assert telem.heater is not None
            assert len(telem.heater) == 4
            heater_ids = sorted([h.system_id for h in telem.heater])
            assert heater_ids == [5, 12, 18, 19]

        with subtests.test(msg="group telemetry"):
            assert telem.group is not None
            assert len(telem.group) == 2
            group_ids = sorted([g.system_id for g in telem.group])
            assert group_ids == [33, 40]


# Add a parametrized test to quickly check all fixtures can be parsed
FIXTURE_FILES = sorted([f.name for f in FIXTURES_DIR.glob("issue-*.json")])


@pytest.mark.parametrize("fixture_file", FIXTURE_FILES)
def test_fixture_parses_without_error(fixture_file: str) -> None:
    """Verify that all fixture files can be parsed without errors.

    This is a smoke test to ensure basic parsing works for all fixtures.
    Detailed validation is done in fixture-specific test classes.

    Args:
        fixture_file: Name of the fixture file to test
    """
    data = load_fixture(fixture_file)

    # Parse MSPConfig
    if "mspconfig" in data and data["mspconfig"]:
        msp = MSPConfig.load_xml(data["mspconfig"])
        assert msp is not None
        assert msp.backyard is not None

    # Parse Telemetry
    if "telemetry" in data and data["telemetry"]:
        telem = Telemetry.from_xml(data["telemetry"])
        assert telem is not None
        assert telem.backyard is not None
