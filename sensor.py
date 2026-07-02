"""Sensor platform for Peak Valley Energy integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PeakValleyEnergyCoordinator
from .const import (
    CONF_CURRENCY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class PeakValleySensorDescription(SensorEntityDescription):
    """Describe a peak valley sensor."""


ENERGY_SENSORS: tuple[PeakValleySensorDescription, ...] = (
    # Daily
    PeakValleySensorDescription(
        key="daily_peak_kwh",
        name="本日峰电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    PeakValleySensorDescription(
        key="daily_valley_kwh",
        name="本日谷电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-outline",
    ),
    PeakValleySensorDescription(
        key="daily_shoulder_kwh",
        name="本日平电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
    ),
    PeakValleySensorDescription(
        key="daily_total_kwh",
        name="本日总电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    # Monthly
    PeakValleySensorDescription(
        key="monthly_peak_kwh",
        name="本月峰电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    PeakValleySensorDescription(
        key="monthly_valley_kwh",
        name="本月谷电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-outline",
    ),
    PeakValleySensorDescription(
        key="monthly_shoulder_kwh",
        name="本月平电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
    ),
    PeakValleySensorDescription(
        key="monthly_total_kwh",
        name="本月总电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    # Yearly
    PeakValleySensorDescription(
        key="yearly_peak_kwh",
        name="本年峰电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash",
    ),
    PeakValleySensorDescription(
        key="yearly_valley_kwh",
        name="本年谷电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-outline",
    ),
    PeakValleySensorDescription(
        key="yearly_shoulder_kwh",
        name="本年平电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-alert",
    ),
    PeakValleySensorDescription(
        key="yearly_total_kwh",
        name="本年总电量",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
)

COST_SENSORS: tuple[PeakValleySensorDescription, ...] = (
    # Daily cost
    PeakValleySensorDescription(
        key="daily_peak_cost",
        name="本日峰电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="daily_valley_cost",
        name="本日谷电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="daily_shoulder_cost",
        name="本日平电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="daily_total_cost",
        name="本日总电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:cash",
    ),
    # Monthly cost
    PeakValleySensorDescription(
        key="monthly_peak_cost",
        name="本月峰电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="monthly_valley_cost",
        name="本月谷电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="monthly_shoulder_cost",
        name="本月平电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="monthly_total_cost",
        name="本月总电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:cash",
    ),
    # Yearly cost
    PeakValleySensorDescription(
        key="yearly_peak_cost",
        name="本年峰电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="yearly_valley_cost",
        name="本年谷电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="yearly_shoulder_cost",
        name="本年平电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:currency-cny",
    ),
    PeakValleySensorDescription(
        key="yearly_total_cost",
        name="本年总电费",
        native_unit_of_measurement="¥",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:cash",
    ),
)

CURRENT_PRICE_SENSORS: tuple[PeakValleySensorDescription, ...] = (
    PeakValleySensorDescription(
        key="current_price",
        name="当前电价",
        native_unit_of_measurement="¥/kWh",
        suggested_display_precision=4,
        icon="mdi:cash-clock",
    ),
)


class PeakValleySensor(SensorEntity):
    """Representation of a Peak Valley Energy sensor."""

    entity_description: PeakValleySensorDescription

    def __init__(
        self,
        coordinator: PeakValleyEnergyCoordinator,
        description: PeakValleySensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self.entity_description = description
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title or "峰谷电价",
            manufacturer="Peak Valley Energy",
            model="Electricity Tariff Tracker",
            sw_version="1.0.0",
        )

        # Register for updates
        self._coordinator.add_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        """Handle update notification from coordinator."""
        self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        values = self._coordinator.get_all_values()
        val = values.get(self.entity_description.key, 0.0)
        # Round to 3 decimal places for kWh, 4 for cost
        if "kwh" in self.entity_description.key:
            return round(val, 3)
        if self.entity_description.key == "current_price":
            return round(val, 4)
        return round(val, 4)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.data is not None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Peak Valley Energy sensors."""
    coordinator: PeakValleyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Add all energy sensors
    for description in ENERGY_SENSORS:
        entities.append(PeakValleySensor(coordinator, description, entry))

    # Add all cost sensors
    for description in COST_SENSORS:
        entities.append(PeakValleySensor(coordinator, description, entry))

    # Add current price sensor
    for description in CURRENT_PRICE_SENSORS:
        entities.append(PeakValleySensor(coordinator, description, entry))

    async_add_entities(entities)
    _LOGGER.info("Created %d peak valley energy sensors for %s", len(entities), entry.title)
