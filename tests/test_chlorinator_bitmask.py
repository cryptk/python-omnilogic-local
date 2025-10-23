"""Tests for chlorinator bitmask decoding."""

from pyomnilogic_local.models.telemetry import TelemetryChlorinator


def test_chlorinator_status_decoding() -> None:
    """Test decoding of chlorinator status bitmask."""
    # Create a chlorinator with status = 134 (0b10000110)
    # Bit 1: ALERT_PRESENT (2)
    # Bit 2: GENERATING (4)
    # Bit 7: K2_ACTIVE (128)
    # Total: 2 + 4 + 128 = 134
    data = {
        "@systemId": 5,
        "@status": 134,
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 0,
        "@chlrError": 0,
        "@scMode": 0,
        "@operatingState": 1,
        "@Timed-Percent": 70,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    # Check raw value
    assert chlorinator.status_raw == 134

    # Check decoded status (returns list of string names)
    status_flags = chlorinator.status
    assert "ALERT_PRESENT" in status_flags
    assert "GENERATING" in status_flags
    assert "K2_ACTIVE" in status_flags
    assert len(status_flags) == 3

    # Verify active property
    assert chlorinator.active is True


def test_chlorinator_alert_decoding() -> None:
    """Test decoding of chlorinator alert bitmask."""
    # Create a chlorinator with chlrAlert = 32 (0b00100000)
    # Bit 5: CELL_TEMP_SCALEBACK (32)
    data = {
        "@systemId": 5,
        "@status": 2,  # ALERT_PRESENT
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 32,
        "@chlrError": 0,
        "@scMode": 0,
        "@operatingState": 1,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    # Check raw value
    assert chlorinator.chlr_alert_raw == 32

    # Check decoded alerts (returns list of string names)
    alert_flags = chlorinator.alerts
    assert "CELL_TEMP_SCALEBACK" in alert_flags
    assert len(alert_flags) == 1


def test_chlorinator_error_decoding() -> None:
    """Test decoding of chlorinator error bitmask."""
    # Create a chlorinator with chlrError = 257 (0b100000001)
    # Bit 0: CURRENT_SENSOR_SHORT (1)
    # Bit 8: K1_RELAY_SHORT (256)
    # Total: 1 + 256 = 257
    data = {
        "@systemId": 5,
        "@status": 1,  # ERROR_PRESENT
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 0,
        "@chlrError": 257,
        "@scMode": 0,
        "@operatingState": 1,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    # Check raw value
    assert chlorinator.chlr_error_raw == 257

    # Check decoded errors (returns list of string names)
    error_flags = chlorinator.errors
    assert "CURRENT_SENSOR_SHORT" in error_flags
    assert "K1_RELAY_SHORT" in error_flags
    assert len(error_flags) == 2


def test_chlorinator_no_flags() -> None:
    """Test chlorinator with no status/alert/error flags set."""
    data = {
        "@systemId": 5,
        "@status": 0,
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 0,
        "@chlrError": 0,
        "@scMode": 0,
        "@operatingState": 1,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    # All should be empty
    assert chlorinator.status == []
    assert chlorinator.alerts == []
    assert chlorinator.errors == []
    assert chlorinator.active is False


def test_chlorinator_complex_alerts() -> None:
    """Test complex multi-bit alert combinations."""
    # chlrAlert = 67 (0b01000011)
    # Bit 0: SALT_LOW (1)
    # Bit 1: SALT_VERY_LOW (2)
    # Bit 6: BOARD_TEMP_HIGH (64)
    # Total: 1 + 2 + 64 = 67
    data = {
        "@systemId": 5,
        "@status": 2,
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 67,
        "@chlrError": 0,
        "@scMode": 0,
        "@operatingState": 1,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    alert_flags = chlorinator.alerts
    assert "SALT_LOW" in alert_flags
    assert "SALT_TOO_LOW" in alert_flags
    assert "BOARD_TEMP_HIGH" in alert_flags
    assert len(alert_flags) == 3


def test_chlorinator_all_status_flags() -> None:
    """Test chlorinator with all status flags set."""
    # status = 255 (0b11111111) - all 8 bits set
    data = {
        "@systemId": 5,
        "@status": 255,
        "@instantSaltLevel": 4082,
        "@avgSaltLevel": 4042,
        "@chlrAlert": 0,
        "@chlrError": 0,
        "@scMode": 0,
        "@operatingState": 1,
        "@operatingMode": 1,
        "@enable": True,
    }

    chlorinator = TelemetryChlorinator.model_validate(data)

    status_flags = chlorinator.status
    assert "ERROR_PRESENT" in status_flags
    assert "ALERT_PRESENT" in status_flags
    assert "GENERATING" in status_flags
    assert "SYSTEM_PAUSED" in status_flags
    assert "LOCAL_PAUSED" in status_flags
    assert "AUTHENTICATED" in status_flags
    assert "K1_ACTIVE" in status_flags
    assert "K2_ACTIVE" in status_flags
    assert len(status_flags) == 8
