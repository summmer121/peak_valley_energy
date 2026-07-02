"""Config flow for Peak Valley Energy integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CURRENCY,
    CONF_ENABLE_SHOULDER,
    CONF_ENERGY_ENTITY,
    CONF_PEAK_END_1,
    CONF_PEAK_END_2,
    CONF_PEAK_PRICE,
    CONF_PEAK_START_1,
    CONF_PEAK_START_2,
    CONF_SHOULDER_END_1,
    CONF_SHOULDER_PRICE,
    CONF_SHOULDER_START_1,
    CONF_VALLEY_PRICE,
    DEFAULT_CURRENCY,
    DEFAULT_PEAK_END_1,
    DEFAULT_PEAK_END_2,
    DEFAULT_PEAK_PRICE,
    DEFAULT_PEAK_START_1,
    DEFAULT_PEAK_START_2,
    DEFAULT_SHOULDER_PRICE,
    DEFAULT_VALLEY_PRICE,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="峰谷电价"): str,
        vol.Required(CONF_ENERGY_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="energy")
        ),
        vol.Required(CONF_PEAK_START_1, default=DEFAULT_PEAK_START_1): selector.TimeSelector(),
        vol.Required(CONF_PEAK_END_1, default=DEFAULT_PEAK_END_1): selector.TimeSelector(),
        vol.Optional(CONF_PEAK_START_2, default=DEFAULT_PEAK_START_2): selector.TimeSelector(),
        vol.Optional(CONF_PEAK_END_2, default=DEFAULT_PEAK_END_2): selector.TimeSelector(),
        vol.Required(CONF_PEAK_PRICE, default=DEFAULT_PEAK_PRICE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=10)
        ),
        vol.Required(CONF_VALLEY_PRICE, default=DEFAULT_VALLEY_PRICE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=10)
        ),
        vol.Required(CONF_ENABLE_SHOULDER, default=False): bool,
    }
)


def _get_shoulder_schema(default_enable: bool = False) -> vol.Schema:
    """Get schema for shoulder (平) configuration."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SHOULDER_START_1,
                default="06:00:00",
            ): selector.TimeSelector(),
            vol.Required(
                CONF_SHOULDER_END_1,
                default="08:00:00",
            ): selector.TimeSelector(),
            vol.Required(CONF_SHOULDER_PRICE, default=DEFAULT_SHOULDER_PRICE): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=10)
            ),
            vol.Required(CONF_CURRENCY, default=DEFAULT_CURRENCY): str,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Peak Valley Energy."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlow":
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # If shoulder is enabled, go to shoulder step
            if user_input.get(CONF_ENABLE_SHOULDER, False):
                self._user_data = user_input
                return await self.async_step_shoulder()

            # No shoulder, add defaults
            user_input[CONF_SHOULDER_PRICE] = 0.0
            user_input[CONF_CURRENCY] = DEFAULT_CURRENCY
            return self._create_entry(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={"desc": "设置你的总电量实体和峰谷时段"},
        )

    async def async_step_shoulder(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure shoulder (平) tariff."""
        if user_input is not None:
            self._user_data.update(user_input)
            return self._create_entry(self._user_data)

        return self.async_show_form(
            step_id="shoulder",
            data_schema=_get_shoulder_schema(),
            description_placeholders={"desc": "设置平段时段和电价"},
        )

    def _create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        return self.async_create_entry(
            title=data.get(CONF_NAME, "峰谷电价"),
            data=data,
        )


class OptionsFlow(config_entries.OptionsFlow):
    """Options flow for Peak Valley Energy."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # Don't assign to self.config_entry — it's a read-only property in HA 2025.x+

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_PEAK_START_1,
                    default=data.get(CONF_PEAK_START_1, DEFAULT_PEAK_START_1),
                ): selector.TimeSelector(),
                vol.Required(
                    CONF_PEAK_END_1,
                    default=data.get(CONF_PEAK_END_1, DEFAULT_PEAK_END_1),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_PEAK_START_2,
                    default=data.get(CONF_PEAK_START_2, DEFAULT_PEAK_START_2),
                ): selector.TimeSelector(),
                vol.Optional(
                    CONF_PEAK_END_2,
                    default=data.get(CONF_PEAK_END_2, DEFAULT_PEAK_END_2),
                ): selector.TimeSelector(),
                vol.Required(
                    CONF_PEAK_PRICE,
                    default=data.get(CONF_PEAK_PRICE, DEFAULT_PEAK_PRICE),
                ): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=10)
                ),
                vol.Required(
                    CONF_VALLEY_PRICE,
                    default=data.get(CONF_VALLEY_PRICE, DEFAULT_VALLEY_PRICE),
                ): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=10)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
