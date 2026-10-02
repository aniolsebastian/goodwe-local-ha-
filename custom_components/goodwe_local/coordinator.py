import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class GoodWeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, inverter):
        super().__init__(hass, _LOGGER, name="goodwe_local",
                         update_interval=timedelta(seconds=10))
        self.inverter = inverter
        self.scheduler = None

    async def _async_update_data(self):
        try:
            return await self.inverter.read_runtime_data()
        except Exception as err:
            raise UpdateFailed(err) from err

    @property
    def device_info(self):
        inv = self.inverter
        return {"identifiers": {("goodwe_local", inv.serial_number)},
                "name": f"GoodWe {inv.model_name}", "manufacturer": "GoodWe",
                "model": inv.model_name, "sw_version": inv.firmware}
