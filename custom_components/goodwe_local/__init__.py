"""GoodWe Local - lokalne sterowanie inwerterem GoodWe."""
import goodwe
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import GoodWeCoordinator
from .scheduler import BatteryScheduler

DOMAIN = "goodwe_local"
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.NUMBER,
             Platform.SWITCH, Platform.TIME]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        inverter = await goodwe.connect(
            entry.data[CONF_HOST], port=entry.data.get(CONF_PORT, 8899), retries=5
        )
    except Exception as err:
        raise ConfigEntryNotReady(f"Brak połączenia z inwerterem: {err}") from err

    coordinator = GoodWeCoordinator(hass, inverter)
    await coordinator.async_config_entry_first_refresh()
    coordinator.scheduler = BatteryScheduler(hass, coordinator, entry.entry_id)
    await coordinator.scheduler.async_load()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coord = hass.data[DOMAIN].pop(entry.entry_id)
        coord.scheduler.async_unload()
    return ok
