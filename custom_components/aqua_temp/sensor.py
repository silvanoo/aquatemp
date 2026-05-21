import logging
from datetime import datetime, time

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .common.base_entity import BaseEntity, async_setup_base_entry
from .common.entity_descriptions import AquaTempSensorEntityDescription
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    await async_setup_base_entry(
        hass,
        entry,
        Platform.SENSOR,
        AquaTempSensorEntity,
        async_add_entities,
    )


class AquaTempSensorEntity(BaseEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: AquaTempSensorEntityDescription,
        coordinator: AquaTempCoordinator,
        device_code: str,
    ):
        super().__init__(entity_description, coordinator, device_code)

        self._attr_device_class = entity_description.device_class
        self._attr_native_unit_of_measurement = (
            entity_description.native_unit_of_measurement
        )

        if entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            self._attr_native_unit_of_measurement = coordinator.get_temperature_unit(
                device_code
            )

        if entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            now = dt_util.now()
            self._attr_last_reset = datetime.combine(now.date(), time.min).astimezone(
                now.tzinfo
            )

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        device_data = self.local_coordinator.get_device_data(self.device_code)

        state = device_data.get(self.entity_description.key)

        if isinstance(state, str):
            try:
                state = float(state)
            except (ValueError, TypeError):
                state = None

        if isinstance(state, (int, float)) and state < 0:
            _LOGGER.warning(
                f"Ignoring negative value {state} for sensor {self.entity_description.key}"
            )
            state = None

        if (
            self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING
            and isinstance(state, (int, float))
        ):
            now = dt_util.now()
            self._attr_last_reset = datetime.combine(now.date(), time.min).astimezone(
                now.tzinfo
            )

        self._attr_native_value = state

        self.async_write_ha_state()
