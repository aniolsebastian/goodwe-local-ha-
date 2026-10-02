from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    ids = {s.id_ for s, _ in coord.settings}
    ents = [RefreshButton(coord)]
    if "time" in ids:
        ents.append(SyncTimeButton(coord))
    async_add_entities(ents)


class _Btn(ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coord, key, name, icon):
        self._coord = coord
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coord.inverter.serial_number}_btn_{key}"
        self._attr_device_info = coord.device_info


class SyncTimeButton(_Btn):
    def __init__(self, coord):
        super().__init__(coord, "sync_time", "Synchronizuj zegar inwertera", "mdi:clock-check")

    async def async_press(self):
        await self._coord.inverter.write_setting("time", datetime.now())


class RefreshButton(_Btn):
    def __init__(self, coord):
        super().__init__(coord, "refresh", "Odśwież dane", "mdi:refresh")

    async def async_press(self):
        await self._coord.async_request_refresh()
