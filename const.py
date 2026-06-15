"""Constants for the Peak Valley Energy integration."""

DOMAIN = "peak_valley_energy"

# Config flow keys
CONF_ENERGY_ENTITY = "energy_entity"
CONF_PEAK_START_1 = "peak_start_1"
CONF_PEAK_END_1 = "peak_end_1"
CONF_PEAK_START_2 = "peak_start_2"
CONF_PEAK_END_2 = "peak_end_2"
CONF_VALLEY_PRICE = "valley_price"
CONF_PEAK_PRICE = "peak_price"
CONF_SHOULDER_PRICE = "shoulder_price"
CONF_ENABLE_SHOULDER = "enable_shoulder"
CONF_SHOULDER_START_1 = "shoulder_start_1"
CONF_SHOULDER_END_1 = "shoulder_end_1"
CONF_CURRENCY = "currency"

# Default values
DEFAULT_PEAK_START_1 = "08:00:00"
DEFAULT_PEAK_END_1 = "11:00:00"
DEFAULT_PEAK_START_2 = "18:00:00"
DEFAULT_PEAK_END_2 = "21:00:00"
DEFAULT_PEAK_PRICE = 0.68
DEFAULT_VALLEY_PRICE = 0.31
DEFAULT_SHOULDER_PRICE = 0.0
DEFAULT_CURRENCY = "CNY"

# Storage keys
STORAGE_KEY = "peak_valley_energy_data"
STORAGE_VERSION = 1

# Sensor prefixes
SENSOR_DAILY_PEAK_KWH = "daily_peak_kwh"
SENSOR_DAILY_VALLEY_KWH = "daily_valley_kwh"
SENSOR_DAILY_SHOULDER_KWH = "daily_shoulder_kwh"
SENSOR_DAILY_TOTAL_KWH = "daily_total_kwh"
SENSOR_DAILY_PEAK_COST = "daily_peak_cost"
SENSOR_DAILY_VALLEY_COST = "daily_valley_cost"
SENSOR_DAILY_SHOULDER_COST = "daily_shoulder_cost"
SENSOR_DAILY_TOTAL_COST = "daily_total_cost"

SENSOR_MONTHLY_PEAK_KWH = "monthly_peak_kwh"
SENSOR_MONTHLY_VALLEY_KWH = "monthly_valley_kwh"
SENSOR_MONTHLY_SHOULDER_KWH = "monthly_shoulder_kwh"
SENSOR_MONTHLY_TOTAL_KWH = "monthly_total_kwh"
SENSOR_MONTHLY_PEAK_COST = "monthly_peak_cost"
SENSOR_MONTHLY_VALLEY_COST = "monthly_valley_cost"
SENSOR_MONTHLY_SHOULDER_COST = "monthly_shoulder_cost"
SENSOR_MONTHLY_TOTAL_COST = "monthly_total_cost"

SENSOR_YEARLY_PEAK_KWH = "yearly_peak_kwh"
SENSOR_YEARLY_VALLEY_KWH = "yearly_valley_kwh"
SENSOR_YEARLY_SHOULDER_KWH = "yearly_shoulder_kwh"
SENSOR_YEARLY_TOTAL_KWH = "yearly_total_kwh"
SENSOR_YEARLY_PEAK_COST = "yearly_peak_cost"
SENSOR_YEARLY_VALLEY_COST = "yearly_valley_cost"
SENSOR_YEARLY_SHOULDER_COST = "yearly_shoulder_cost"
SENSOR_YEARLY_TOTAL_COST = "yearly_total_cost"

SENSOR_LAST_UPDATED = "last_updated"

# Tariff types
TARIFF_PEAK = "peak"
TARIFF_VALLEY = "valley"
TARIFF_SHOULDER = "shoulder"
