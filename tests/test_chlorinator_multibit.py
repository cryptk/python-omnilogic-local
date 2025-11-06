"""Tests for chlorinator multi-bit field special case handling."""

# pylint: skip-file

from pyomnilogic_local.models.telemetry import TelemetryChlorinator


def test_cell_temp_high_special_case() -> None:
    """Test that CELL_TEMP_HIGH replaces both LOW and SCALEBACK when both bits are set."""
    # Cell Water Temp bits 5:4 = 11 (both CELL_TEMP_LOW and CELL_TEMP_SCALEBACK set)
    # This should be replaced with "CELL_TEMP_HIGH"
    data = {
        "system_id": 5,
        "status_raw": 2,  # ALERT_PRESENT
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0b11_0000,  # bits 5:4 = 11
        "chlr_error_raw": 0,
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    alerts = chlorinator.alerts
    # Should have CELL_TEMP_HIGH instead of the individual bits
    assert "CELL_TEMP_HIGH" in alerts
    assert "CELL_TEMP_LOW" not in alerts
    assert "CELL_TEMP_SCALEBACK" not in alerts
    assert len(alerts) == 1


def test_cell_temp_low_only() -> None:
    """Test that CELL_TEMP_LOW appears normally when only that bit is set."""
    data = {
        "system_id": 5,
        "status_raw": 2,
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0b01_0000,  # bits 5:4 = 01
        "chlr_error_raw": 0,
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    alerts = chlorinator.alerts
    assert "CELL_TEMP_LOW" in alerts
    assert "CELL_TEMP_SCALEBACK" not in alerts
    assert "CELL_TEMP_HIGH" not in alerts


def test_cell_temp_scaleback_only() -> None:
    """Test that CELL_TEMP_SCALEBACK appears normally when only that bit is set."""
    data = {
        "system_id": 5,
        "status_raw": 2,
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0b10_0000,  # bits 5:4 = 10
        "chlr_error_raw": 0,
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    alerts = chlorinator.alerts
    assert "CELL_TEMP_SCALEBACK" in alerts
    assert "CELL_TEMP_LOW" not in alerts
    assert "CELL_TEMP_HIGH" not in alerts


def test_cell_comm_loss_special_case() -> None:
    """Test that CELL_COMM_LOSS replaces both TYPE and AUTH when both bits are set."""
    # Cell Error bits 13:12 = 11 (both CELL_ERROR_TYPE and CELL_ERROR_AUTH set)
    # This should be replaced with "CELL_COMM_LOSS"
    data = {
        "system_id": 5,
        "status_raw": 1,  # ERROR_PRESENT
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0,
        "chlr_error_raw": 0b11_000000000000,  # bits 13:12 = 11
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    errors = chlorinator.errors
    # Should have CELL_COMM_LOSS instead of the individual bits
    assert "CELL_COMM_LOSS" in errors
    assert "CELL_ERROR_TYPE" not in errors
    assert "CELL_ERROR_AUTH" not in errors
    assert len(errors) == 1


def test_cell_error_type_only() -> None:
    """Test that CELL_ERROR_TYPE appears normally when only that bit is set."""
    data = {
        "system_id": 5,
        "status_raw": 1,
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0,
        "chlr_error_raw": 0b01_000000000000,  # bits 13:12 = 01
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    errors = chlorinator.errors
    assert "CELL_ERROR_TYPE" in errors
    assert "CELL_ERROR_AUTH" not in errors
    assert "CELL_COMM_LOSS" not in errors


def test_cell_error_auth_only() -> None:
    """Test that CELL_ERROR_AUTH appears normally when only that bit is set."""
    data = {
        "system_id": 5,
        "status_raw": 1,
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0,
        "chlr_error_raw": 0b10_000000000000,  # bits 13:12 = 10
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    errors = chlorinator.errors
    assert "CELL_ERROR_AUTH" in errors
    assert "CELL_ERROR_TYPE" not in errors
    assert "CELL_COMM_LOSS" not in errors


def test_combined_with_other_flags() -> None:
    """Test special cases work correctly when combined with other flags."""
    # Multiple alerts including CELL_TEMP_HIGH
    data = {
        "system_id": 5,
        "status_raw": 2,
        "instant_salt_level": 3000,
        "avg_salt_level": 3000,
        "chlr_alert_raw": 0x31,  # SALT_LOW + CELL_TEMP_HIGH (0b00110001)
        "chlr_error_raw": 0,
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    alerts = chlorinator.alerts
    assert "SALT_LOW" in alerts
    assert "CELL_TEMP_HIGH" in alerts
    assert "CELL_TEMP_LOW" not in alerts
    assert "CELL_TEMP_SCALEBACK" not in alerts

    # Multiple errors including CELL_COMM_LOSS
    data = {
        "system_id": 5,
        "status_raw": 1,
        "instant_salt_level": 4082,
        "avg_salt_level": 4042,
        "chlr_alert_raw": 0,
        "chlr_error_raw": 0x3001,  # CURRENT_SENSOR_SHORT + CELL_COMM_LOSS
        "sc_mode": 0,
        "operating_state": 1,
        "operating_mode": 1,
        "enable": True,
    }
    chlorinator = TelemetryChlorinator.model_validate(data)

    errors = chlorinator.errors
    assert "CURRENT_SENSOR_SHORT" in errors
    assert "CELL_COMM_LOSS" in errors
    assert "CELL_ERROR_TYPE" not in errors
    assert "CELL_ERROR_AUTH" not in errors
