from datetime import time

from homeassistant.components.time import TimeEntity

from .scheduler import SLOTS, SlotEntity, _t


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    ents = []
    for i in range(SLOTS):
        ents.append(SlotTime(coord, i, "start", "początek"))
        ents.append(SlotTime(coord, i, "end", "koniec"))
    async_add_entities(ents)


class SlotTime(SlotEntity, TimeEntity):
    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> time:
        return _t(self._val)

    async def async_set_value(self, value: time) -> None:
        await self._save(value.strftime("%H:%M"))
