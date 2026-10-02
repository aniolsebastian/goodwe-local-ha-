"""Encje dla wszystkich parametrów (settings) inwertera."""
from datetime import timedelta

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory

SCAN_INTERVAL = timedelta(minutes=5)

RANGES = {"%": (0, 100), "V": (0, 1000), "A": (0, 300), "W": (-30000, 30000),
          "kW": (-30, 30), "Hz": (40, 70), "C": (-40, 100), "°C": (-40, 100),
          "s": (0, 65535), "min": (0, 65535)}


def is_numeric(val):
    return isinstance(val, (int, float)) and not isinstance(val, bool)


class _Base:
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False  # włącz ręcznie potrzebne

    def _init(self, coord, sdef, value):
        self._inv = coord.inverter
        self._id = sdef.id_
        self._attr_name = f"Ustawienie: {sdef.name or sdef.id_}"
        self._attr_unique_id = f"{coord.inverter.serial_number}_setting_{sdef.id_}"
        self._attr_device_info = coord.device_info
        self._attr_extra_state_attributes = {"setting_id": sdef.id_}


class SettingNumber(_Base, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, coord, sdef, value):
        self._init(coord, sdef, value)
        self._is_int = isinstance(value, int)
        unit = sdef.unit or None
        self._attr_native_unit_of_measurement = unit
        lo, hi = RANGES.get(unit, (-32768, 65535))
        self._attr_native_min_value, self._attr_native_max_value = lo, hi
        self._attr_native_step = 1 if self._is_int else 0.1
        self._attr_native_value = value

    async def async_update(self):
        try:
            self._attr_native_value = await self._inv.read_setting(self._id)
            self._attr_available = True
        except Exception:
            self._attr_available = False

    async def async_set_native_value(self, value):
        v = int(round(value)) if self._is_int else float(value)
        await self._inv.write_setting(self._id, v)
        self._attr_native_value = await self._inv.read_setting(self._id)
        self.async_write_ha_state()


class SettingSensor(_Base, SensorEntity):
    """Parametr tylko do odczytu (złożony typ albo edycja wyłączona)."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coord, sdef, value):
        self._init(coord, sdef, value)
        self._attr_native_unit_of_measurement = sdef.unit if is_numeric(value) and sdef.unit else None
        self._attr_native_value = self._fmt(value)

    @staticmethod
    def _fmt(v):
        if is_numeric(v):
            return v
        s = str(v.name if hasattr(v, "name") else v)
        return s[:250]

    async def async_update(self):
        try:
            self._attr_native_value = self._fmt(await self._inv.read_setting(self._id))
            self._attr_available = True
        except Exception:
            self._attr_available = False


def build(coord):
    numbers, sensors = [], []
    for sdef, val in coord.settings:
        if coord.advanced and is_numeric(val):
            numbers.append(SettingNumber(coord, sdef, val))
        else:
            sensors.append(SettingSensor(coord, sdef, val))
    return numbers, sensors
