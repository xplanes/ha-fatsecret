"""FatSecret Sensor."""

from propcache.api import cached_property

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, FATSECRET_FIELDS


class FatSecretSensor(CoordinatorEntity, SensorEntity):
    """Representation of a FatSecret sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, field: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._field: str = field

        field_meta = FATSECRET_FIELDS[field]
        self._attr_name = f"{field_meta['name']}"
        self._attr_unique_id = f"{DOMAIN}_{field}"
        self._attr_native_unit_of_measurement = field_meta["unit"]
        self.coordinator: DataUpdateCoordinator = coordinator

    @property  # type: ignore[override]
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._field)
        if value is None:
            return None
        else:
            return float(value)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self._attr_native_unit_of_measurement
