from homeassistant.components.select import SelectEntity

from .scheduler import ACTIONS, SLOTS, SlotEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    async_add_entities([SlotAction(coord, i) for i in range(SLOTS)])
    try:
        modes = await coord.inverter.get_operation_modes(True)
    except Exception:
        return
    async_add_entities([GoodWeMode(coord, modes)], update_before_add=True)


class GoodWeMode(SelectEntity):
    _attr_name = "Tryb pracy"

    def __init__(self, coord, modes):
        self._inv = coord.inverter
        self._modes = {m.name.lower(): m for m in modes}
        self._attr_options = list(self._modes)
        self._attr_unique_id = f"{self._inv.serial_number}_mode"
        self._attr_device_info = coord.device_info

    async def async_update(self):
        try:
            self._attr_current_option = (await self._inv.get_operation_mode()).name.lower()
        except Exception:
            pass

    async def async_select_option(self, option):
        await self._inv.set_operation_mode(self._modes[option])
        self._attr_current_option = option
        self.async_write_ha_state()


class SlotAction(SlotEntity, SelectEntity):
    _attr_options = ACTIONS
    _attr_icon = "mdi:battery-sync"

    def __init__(self, coord, slot):
        super().__init__(coord, slot, "action", "akcja")

    @property
    def current_option(self):
        return self._val

    async def async_select_option(self, option):
        await self._save(option)
