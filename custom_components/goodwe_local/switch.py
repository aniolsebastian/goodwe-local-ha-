from homeassistant.components.switch import SwitchEntity

from .scheduler import SLOTS, SlotEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    async_add_entities([MasterSwitch(coord)] + [SlotSwitch(coord, i) for i in range(SLOTS)])


class MasterSwitch(SlotEntity, SwitchEntity):
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coord):
        super().__init__(coord, None, "active", "Harmonogram aktywny")

    @property
    def is_on(self):
        return self._sch.active

    async def async_turn_on(self, **kw):
        await self._sch.async_update(active=True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kw):
        await self._sch.async_update(active=False)
        self.async_write_ha_state()


class SlotSwitch(SlotEntity, SwitchEntity):
    _attr_icon = "mdi:battery-clock"

    def __init__(self, coord, slot):
        super().__init__(coord, slot, "enabled", "włączony")

    @property
    def is_on(self):
        return self._val

    async def async_turn_on(self, **kw):
        await self._save(True)

    async def async_turn_off(self, **kw):
        await self._save(False)
