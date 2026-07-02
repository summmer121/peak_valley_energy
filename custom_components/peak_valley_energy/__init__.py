"""The Peak Valley Energy integration.

Tracks energy consumption from a total energy sensor and splits it into
peak / valley / shoulder periods with cost calculation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ENABLE_SHOULDER,
    CONF_PEAK_END_1,
    CONF_PEAK_END_2,
    CONF_PEAK_PRICE,
    CONF_PEAK_START_1,
    CONF_PEAK_START_2,
    CONF_SHOULDER_END_1,
    CONF_SHOULDER_PRICE,
    CONF_SHOULDER_START_1,
    CONF_VALLEY_PRICE,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    TARIFF_PEAK,
    TARIFF_SHOULDER,
    TARIFF_VALLEY,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


def _parse_time(time_str: str) -> tuple[int, int, int]:
    """Parse HH:MM:SS string into (hour, minute, second)."""
    parts = time_str.split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    s = int(parts[2]) if len(parts) > 2 else 0
    return h, m, s


class PeakValleyEnergyCoordinator:
    """Central coordinator for peak/valley energy tracking.

    Strategy: We listen to the total kWh entity's state changes. Each time the
    energy value increases, we attribute the delta to whichever tariff period
    the *current* time falls into. Periodically (at midnight, month start, and
    year start) we roll over the daily/monthly/yearly counters.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.energy_entity = entry.data["energy_entity"]

        # Parse config
        self.peak_start_1 = _parse_time(entry.data.get(CONF_PEAK_START_1, "08:00:00"))
        self.peak_end_1 = _parse_time(entry.data.get(CONF_PEAK_END_1, "11:00:00"))
        self.peak_start_2 = _parse_time(entry.data.get(CONF_PEAK_START_2, "18:00:00"))
        self.peak_end_2 = _parse_time(entry.data.get(CONF_PEAK_END_2, "21:00:00"))
        self.peak_price = float(entry.data.get(CONF_PEAK_PRICE, 0.68))
        self.valley_price = float(entry.data.get(CONF_VALLEY_PRICE, 0.31))
        self.shoulder_price = float(entry.data.get(CONF_SHOULDER_PRICE, 0.0))
        self.enable_shoulder = entry.data.get(CONF_ENABLE_SHOULDER, False)

        self.shoulder_start_1 = _parse_time(entry.data.get(CONF_SHOULDER_START_1, "06:00:00"))
        self.shoulder_end_1 = _parse_time(entry.data.get(CONF_SHOULDER_END_1, "08:00:00"))

        self._last_energy_value: float | None = None
        self._store: Store | None = None
        self._data: dict[str, Any] = {}
        self._listeners: list = []
        self._current_price: float = 0.0

    def get_tariff(self, now: datetime) -> str:
        """Determine which tariff period the given time falls into."""
        current = now.hour * 3600 + now.minute * 60 + now.second

        # Check peak periods
        peak1_start = self.peak_start_1[0] * 3600 + self.peak_start_1[1] * 60 + self.peak_start_1[2]
        peak1_end = self.peak_end_1[0] * 3600 + self.peak_end_1[1] * 60 + self.peak_end_1[2]
        if peak1_start <= current < peak1_end:
            return TARIFF_PEAK

        peak2_start = self.peak_start_2[0] * 3600 + self.peak_start_2[1] * 60 + self.peak_start_2[2]
        peak2_end = self.peak_end_2[0] * 3600 + self.peak_end_2[1] * 60 + self.peak_end_2[2]
        if peak2_start <= current < peak2_end:
            return TARIFF_PEAK

        # Check shoulder period (only if enabled)
        if self.enable_shoulder:
            shoulder_start = self.shoulder_start_1[0] * 3600 + self.shoulder_start_1[1] * 60 + self.shoulder_start_1[2]
            shoulder_end = self.shoulder_end_1[0] * 3600 + self.shoulder_end_1[1] * 60 + self.shoulder_end_1[2]
            if shoulder_start <= current < shoulder_end:
                return TARIFF_SHOULDER

        # Default is valley
        return TARIFF_VALLEY

    def _default_data(self) -> dict[str, Any]:
        """Default empty data structure."""
        return {
            "daily": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "monthly": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "yearly": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "daily_cost": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "monthly_cost": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "yearly_cost": {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0},
            "daily_date": None,
            "monthly_date": None,
            "yearly_date": None,
            "last_energy": None,
            "last_update": None,
        }

    async def async_load(self) -> None:
        """Load data from persistent storage."""
        self._store = Store(self.hass, STORAGE_VERSION, f"{STORAGE_KEY}_{self.entry.entry_id}")
        data = await self._store.async_load()
        if data is None:
            self._data = self._default_data()
            _LOGGER.info("No saved data found for %s, starting fresh", self.entry.entry_id)
        else:
            self._data = {**self._default_data(), **data}

        self._last_energy_value = self._data.get("last_energy")

    async def async_save(self) -> None:
        """Save data to persistent storage."""
        if self._store:
            await self._store.async_save(self._data)

    def _check_rollover(self, now: datetime) -> None:
        """Check if we need to roll over daily/monthly/yearly counters."""
        today_str = now.strftime("%Y-%m-%d")
        this_month = now.month
        this_year = now.year

        # Daily rollover
        if self._data["daily_date"] != today_str:
            _LOGGER.info("Daily rollover: %s -> %s", self._data["daily_date"], today_str)
            self._data["daily"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["daily_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["daily_date"] = today_str

        # Monthly rollover
        month_key = f"{this_year}-{this_month:02d}"
        if self._data["monthly_date"] != month_key:
            _LOGGER.info("Monthly rollover: %s -> %s", self._data["monthly_date"], month_key)
            self._data["monthly"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["monthly_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["monthly_date"] = month_key

        # Yearly rollover
        year_key = str(this_year)
        if self._data["yearly_date"] != year_key:
            _LOGGER.info("Yearly rollover: %s -> %s", self._data["yearly_date"], year_key)
            self._data["yearly"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["yearly_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
            self._data["yearly_date"] = year_key

    def _get_price_for_tariff(self, tariff: str) -> float:
        """Get unit price for a tariff type."""
        if tariff == TARIFF_PEAK:
            return self.peak_price
        if tariff == TARIFF_SHOULDER:
            return self.shoulder_price
        return self.valley_price

    @callback
    def async_handle_state_change(self, event: Event) -> None:
        """Handle state changes of the monitored energy entity."""
        now = datetime.now()

        # Get current energy value
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (None, "unavailable", "unknown"):
            return

        try:
            new_energy = float(new_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not convert energy state '%s' to float", new_state.state)
            return

        # First reading - just store the value
        if self._last_energy_value is None:
            self._last_energy_value = new_energy
            self._data["last_energy"] = new_energy
            _LOGGER.info("First energy reading: %.3f kWh", new_energy)
            return

        # Calculate delta
        delta = new_energy - self._last_energy_value

        if delta < 0:
            # Meter reset or source changed - re-baseline
            _LOGGER.warning(
                "Energy value decreased from %.3f to %.3f - resetting baseline",
                self._last_energy_value,
                new_energy,
            )
            self._last_energy_value = new_energy
            self._data["last_energy"] = new_energy
            return

        if delta == 0:
            return

        # Check rollover before adding
        self._check_rollover(now)

        # Determine tariff period
        tariff = self.get_tariff(now)
        price = self._get_price_for_tariff(tariff)
        cost = delta * price

        _LOGGER.debug(
            "Energy delta %.3f kWh at %s -> %s tariff @ %.4f = %.4f cost",
            delta, now.isoformat(), tariff, price, cost
        )

        # Accumulate
        self._data["daily"][tariff] += delta
        self._data["daily"]["total"] += delta
        self._data["daily_cost"][tariff] += cost
        self._data["daily_cost"]["total"] += cost

        self._data["monthly"][tariff] += delta
        self._data["monthly"]["total"] += delta
        self._data["monthly_cost"][tariff] += cost
        self._data["monthly_cost"]["total"] += cost

        self._data["yearly"][tariff] += delta
        self._data["yearly"]["total"] += delta
        self._data["yearly_cost"][tariff] += cost
        self._data["yearly_cost"]["total"] += cost

        # Update last values
        self._last_energy_value = new_energy
        self._data["last_energy"] = new_energy
        self._data["last_update"] = now.isoformat()

        # Notify listeners
        self._notify_listeners()

        # Update current price
        self._current_price = self._get_price_for_tariff(tariff)

    def _notify_listeners(self) -> None:
        """Notify registered listeners that data has updated."""
        for listener in self._listeners:
            listener()

    def add_listener(self, listener) -> None:
        """Add a listener callback."""
        self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        """Remove a listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    @property
    def data(self) -> dict[str, Any]:
        """Return current data."""
        return self._data

    def get_all_values(self) -> dict[str, float]:
        """Get a flat dict of all sensor values."""
        d = self._data
        return {
            # Daily
            "daily_peak_kwh": d["daily"]["peak"],
            "daily_valley_kwh": d["daily"]["valley"],
            "daily_shoulder_kwh": d["daily"]["shoulder"],
            "daily_total_kwh": d["daily"]["total"],
            "daily_peak_cost": d["daily_cost"]["peak"],
            "daily_valley_cost": d["daily_cost"]["valley"],
            "daily_shoulder_cost": d["daily_cost"]["shoulder"],
            "daily_total_cost": d["daily_cost"]["total"],
            # Monthly
            "monthly_peak_kwh": d["monthly"]["peak"],
            "monthly_valley_kwh": d["monthly"]["valley"],
            "monthly_shoulder_kwh": d["monthly"]["shoulder"],
            "monthly_total_kwh": d["monthly"]["total"],
            "monthly_peak_cost": d["monthly_cost"]["peak"],
            "monthly_valley_cost": d["monthly_cost"]["valley"],
            "monthly_shoulder_cost": d["monthly_cost"]["shoulder"],
            "monthly_total_cost": d["monthly_cost"]["total"],
            # Yearly
            "yearly_peak_kwh": d["yearly"]["peak"],
            "yearly_valley_kwh": d["yearly"]["valley"],
            "yearly_shoulder_kwh": d["yearly"]["shoulder"],
            "yearly_total_kwh": d["yearly"]["total"],
            "yearly_peak_cost": d["yearly_cost"]["peak"],
            "yearly_valley_cost": d["yearly_cost"]["valley"],
            "yearly_shoulder_cost": d["yearly_cost"]["shoulder"],
            "yearly_total_cost": d["yearly_cost"]["total"],
            # Current price
            "current_price": self._get_price_for_tariff(self.get_tariff(datetime.now())),
        }

    async def async_save_periodic(self, _now: datetime) -> None:
        """Periodic save task."""
        await self.async_save()

    async def async_midnight_rollover(self, _now: datetime) -> None:
        """Trigger rollover at midnight to ensure clean daily reset."""
        self._check_rollover(_now)
        await self.async_save()
        self._notify_listeners()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Peak Valley Energy from a config entry."""
    coordinator = PeakValleyEnergyCoordinator(hass, entry)

    # Load saved data
    await coordinator.async_load()

    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Listen to energy entity state changes
    unsub = async_track_state_change_event(
        hass,
        [coordinator.energy_entity],
        coordinator.async_handle_state_change,
    )
    entry.async_on_unload(unsub)

    # Schedule periodic saves (every 5 minutes)
    from homeassistant.helpers.event import async_track_time_interval

    unsub_save = async_track_time_interval(
        hass,
        coordinator.async_save_periodic,
        timedelta(minutes=5),
    )
    entry.async_on_unload(unsub_save)

    # Schedule midnight rollover check
    from homeassistant.helpers.event import async_track_time_change

    unsub_midnight = async_track_time_change(
        hass,
        coordinator.async_midnight_rollover,
        hour=0, minute=0, second=1,
    )
    entry.async_on_unload(unsub_midnight)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Save final state
        await coordinator.async_save()

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry and clean up storage."""
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
    await store.async_remove()
    _LOGGER.info("Removed storage for %s", entry.entry_id)


async def async_reset_data(
    hass: HomeAssistant, entry: ConfigEntry, reset_type: str = "all"
) -> None:
    """Reset energy data. reset_type: all / daily / monthly / yearly."""
    coordinator: PeakValleyEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    now = datetime.now()

    if reset_type in ("all", "daily"):
        coordinator.data["daily"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["daily_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["daily_date"] = now.strftime("%Y-%m-%d")

    if reset_type in ("all", "monthly"):
        coordinator.data["monthly"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["monthly_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["monthly_date"] = f"{now.year}-{now.month:02d}"

    if reset_type in ("all", "yearly"):
        coordinator.data["yearly"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["yearly_cost"] = {"peak": 0.0, "valley": 0.0, "shoulder": 0.0, "total": 0.0}
        coordinator.data["yearly_date"] = str(now.year)

    await coordinator.async_save()
    coordinator._notify_listeners()
    _LOGGER.info("Reset %s data for %s", reset_type, entry.entry_id)
