"""GoodWe Local - lokalne sterowanie inwerterem GoodWe."""
import asyncio
import logging
from datetime import datetime

import goodwe
import voluptuous as vol
from goodwe import OperationMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .coordinator import GoodWeCoordinator
from .scheduler import BatteryScheduler

_LOGGER = logging.getLogger(__name__)
DOMAIN = "goodwe_local"
CONF_ADVANCED = "advanced_write"
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.NUMBER,
             Platform.SWITCH, Platform.TIME, Platform.BUTTON]


async def _discover_settings(inverter):
    """Odczytaj wszystkie parametry (settings) udostępniane przez model."""
    found = []
    for s in inverter.settings():
        if not s.id_:
            continue
        try:
            val = await asyncio.wait_for(inverter.read_setting(s.id_), 5)
        except Exception as err:  # parametr nieobsługiwany przez firmware
            _LOGGER.debug("Pomijam %s: %s", s.id_, err)
            continue
        found.append((s, val))
    _LOGGER.info("GoodWe: wykryto %d parametrów", len(found))
    return found


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    try:
        inverter = await goodwe.connect(
            entry.data[CONF_HOST], port=entry.data.get(CONF_PORT, 8899), retries=5
        )
    except Exception as err:
        raise ConfigEntryNotReady(f"Brak połączenia z inwerterem: {err}") from err

    coordinator = GoodWeCoordinator(hass, inverter)
    await coordinator.async_config_entry_first_refresh()
    coordinator.settings = await _discover_settings(inverter)
    coordinator.advanced = entry.options.get(CONF_ADVANCED, False)
    coordinator.scheduler = BatteryScheduler(hass, coordinator, entry.entry_id)
    await coordinator.scheduler.async_load()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    _register_services(hass)
    return True


async def _reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coord = hass.data[DOMAIN].pop(entry.entry_id)
        coord.scheduler.async_unload()
    return ok


def _get_inverter(hass, call):
    coords = list(hass.data.get(DOMAIN, {}).values())
    serial = call.data.get("serial")
    for c in coords:
        if not serial or c.inverter.serial_number == serial:
            return c.inverter
    raise HomeAssistantError("Nie znaleziono inwertera")


def _register_services(hass):
    if hass.services.has_service(DOMAIN, "write_setting"):
        return

    async def read_setting(call: ServiceCall):
        inv = _get_inverter(hass, call)
        val = await inv.read_setting(call.data["setting"])
        return {"setting": call.data["setting"], "value": str(val)}

    async def write_setting(call: ServiceCall):
        inv = _get_inverter(hass, call)
        await inv.write_setting(call.data["setting"], call.data["value"])

    async def list_settings(call: ServiceCall):
        inv = _get_inverter(hass, call)
        return {"settings": [
            {"id": s.id_, "name": s.name, "unit": s.unit} for s in inv.settings()]}

    async def set_mode(call: ServiceCall):
        inv = _get_inverter(hass, call)
        mode = OperationMode[call.data["mode"].upper()]
        await inv.set_operation_mode(mode, call.data.get("power", 100),
                                     call.data.get("soc", 100))

    async def sync_time(call: ServiceCall):
        inv = _get_inverter(hass, call)
        await inv.write_setting("time", datetime.now())

    base = {vol.Optional("serial"): cv.string}
    hass.services.async_register(
        DOMAIN, "read_setting", read_setting,
        vol.Schema({**base, vol.Required("setting"): cv.string}),
        supports_response=SupportsResponse.ONLY)
    hass.services.async_register(
        DOMAIN, "write_setting", write_setting,
        vol.Schema({**base, vol.Required("setting"): cv.string,
                    vol.Required("value"): vol.Any(int, float, str)}))
    hass.services.async_register(
        DOMAIN, "list_settings", list_settings, vol.Schema(base),
        supports_response=SupportsResponse.ONLY)
    hass.services.async_register(
        DOMAIN, "set_operation_mode", set_mode,
        vol.Schema({**base, vol.Required("mode"): cv.string,
                    vol.Optional("power"): vol.All(int, vol.Range(1, 100)),
                    vol.Optional("soc"): vol.All(int, vol.Range(0, 100))}))
    hass.services.async_register(DOMAIN, "sync_time", sync_time, vol.Schema(base))
