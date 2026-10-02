from homeassistant.components.number import NumberEntity, NumberMode

from .scheduler import SLOTS, SlotEntity
from . import settings as gw_settings


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    inv = coord.inverter
    async_add_entities([
        GoodWeNumber(coord, "export_limit", "Limit eksportu do sieci", "W", 0, 10000, 100,
                     inv.get_grid_export_limit, inv.set_grid_export_limit),
        GoodWeNumber(coord, "battery_dod", "Głębokość rozładowania baterii", "%", 0, 99, 1,
                     inv.get_ongrid_battery_dod, inv.set_ongrid_battery_dod),
    ], update_before_add=True)

    slot_ents = []
    for i in range(SLOTS):
        slot_ents.append(SlotNumber(coord, i, "power", "moc", 1, 100, "mdi:flash"))
        slot_ents.append(SlotNumber(coord, i, "soc", "docelowy SOC", 0, 100, "mdi:battery-high"))
    async_add_entities(slot_ents)

    numbers, _ = gw_settings.build(coord)
    async_add_entities(numbers)


class GoodWeNumber(NumberEntity):
    def __init__(self, coord, key, name, unit, lo, hi, step, getter, setter):
        self._get, self._set = getter, setter
        self._attr_name = name
        self._attr_unique_id = f"{coord.inverter.serial_number}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value, self._attr_native_max_value = lo, hi
        self._attr_native_step = step
        self._attr_device_info = coord.device_info

    async def async_update(self):
        try:
            self._attr_native_value = await self._get()
            self._attr_available = True
        except Exception:
            self._attr_available = False

    async def async_set_native_value(self, value):
        await self._set(int(value))
        self._attr_native_value = value
        self.async_write_ha_state()


class SlotNumber(SlotEntity, NumberEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coord, slot, key, name, lo, hi, icon):
        super().__init__(coord, slot, key, name)
        self._attr_native_min_value = lo
        self._attr_native_max_value = hi
        self._attr_icon = icon

    @property
    def native_value(self):
        return self._val

    async def async_set_native_value(self, value):
        await self._save(int(value))
