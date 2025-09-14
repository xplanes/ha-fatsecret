"""FatSecret Sensor."""

from propcache.api import cached_property

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN, SENSOR_TYPES


class FatSecretSensor(SensorEntity):
    """Representation of a FatSecret sensor."""

    def __init__(self, metric: str) -> None:
        """Initialize the sensor."""
        self._metric: str = metric
        self._state: float = 0.0
        self._name: str = f"{DOMAIN}_{SENSOR_TYPES[metric]}"
        self._unique_id: str = self._name

    @cached_property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @cached_property
    def unique_id(self) -> str | None:
        """Return a unique ID for this entity."""
        return self._unique_id

    def update_value(self, value: float) -> None:
        """Update the sensor's value."""
        self._state = value
        self.async_write_ha_state()

    @property  # type: ignore[override]
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self._state
