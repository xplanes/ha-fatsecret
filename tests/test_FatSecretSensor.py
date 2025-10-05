import pytest
from unittest.mock import Mock

from custom_components.fatsecret.sensor import FatSecretSensor
from custom_components.fatsecret.const import DOMAIN, FATSECRET_FIELDS


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with some data."""
    coordinator = Mock()
    coordinator.data = {
        "calories": 200,
        "protein": 50,
    }
    return coordinator


@pytest.mark.parametrize(
    "field,expected_name,expected_unit",
    [
        (
            "calories",
            FATSECRET_FIELDS["calories"]["name"],
            FATSECRET_FIELDS["calories"]["unit"],
        ),
        (
            "protein",
            FATSECRET_FIELDS["protein"]["name"],
            FATSECRET_FIELDS["protein"]["unit"],
        ),
    ],
)
def test_sensor_init(mock_coordinator, field, expected_name, expected_unit):
    """Test that the sensor initializes correctly."""
    sensor = FatSecretSensor(mock_coordinator, field)

    assert sensor._field == field
    assert sensor._attr_name == expected_name
    assert sensor._attr_unique_id == f"{DOMAIN}_{field}"
    assert sensor._attr_native_unit_of_measurement == expected_unit
    assert sensor.coordinator == mock_coordinator


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("calories", 200, 200.0),
        ("protein", 50, 50.0),
        ("calories", None, None),
    ],
)
def test_native_value(mock_coordinator, field, value, expected):
    """Test the native_value property."""
    mock_coordinator.data[field] = value
    sensor = FatSecretSensor(mock_coordinator, field)
    assert sensor.native_value == expected


@pytest.mark.parametrize(
    "field,expected_unit",
    [
        ("calories", FATSECRET_FIELDS["calories"]["unit"]),
        ("protein", FATSECRET_FIELDS["protein"]["unit"]),
    ],
)
def test_native_unit_of_measurement(mock_coordinator, field, expected_unit):
    """Test native_unit_of_measurement property."""
    sensor = FatSecretSensor(mock_coordinator, field)
    assert sensor.native_unit_of_measurement == expected_unit
