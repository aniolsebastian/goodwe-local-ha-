"""Harmonogram ładowania/rozładowania baterii sterowany z HA."""
import logging
from datetime import time, timedelta

from goodwe import OperationMode
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

SLOTS = 4
ACTIONS = ["wyłączony", "ładowanie", "rozładowanie"]
DEFAULT_SLOT = {"enabled": False, "start": "00:00", "end": "06:00",
                "action": "ładowanie", "power": 50, "soc": 100}


def _t(s: str) -> time:
    h, m = s.split(":")[:2]
    return time(int(h), int(m))


class BatteryScheduler:
    def __init__(self, hass, coord, entry_id):
        self.hass = hass
        self.inv = coord.inverter
        self._store = Store(hass, 1, f"goodwe_local_schedule_{entry_id}")
        self.active = False
        self.slots = [dict(DEFAULT_SLOT) for _ in range(SLOTS)]
        self.status = "nieaktywny"
        self._applied = None
        self._listeners = []
        self._unsub = None

    async def async_load(self):
        data = await self._store.async_load()
        if data:
            self.active = data.get("active", False)
            saved = data.get("slots", [])
            for i in range(min(SLOTS, len(saved))):
                self.slots[i] = {**DEFAULT_SLOT, **saved[i]}
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(seconds=30))
        await self._tick()

    def async_unload(self):
        if self._unsub:
            self._unsub()

    def add_listener(self, cb):
        self._listeners.append(cb)

    async def async_update(self, slot=None, **changes):
        if slot is None:
            if "active" in changes:
                self.active = changes["active"]
        else:
            self.slots[slot].update(changes)
        await self._store.async_save({"active": self.active, "slots": self.slots})
        self._applied = None
        if not self.active:
            try:
                await self._apply(("general", 0, 0))
            except Exception as err:
                _LOGGER.error("Nie udało się przywrócić trybu GENERAL: %s", err)
            self.status = "nieaktywny"
            self._notify()
        else:
            await self._tick()

    @staticmethod
    def _in_window(now, start, end):
        if start == end:
            return False
        if start < end:
            return start <= now < end
        return now >= start or now < end

    def desired(self):
        now = dt_util.now().time()
        for i, s in enumerate(self.slots):
            if not s["enabled"] or s["action"] == "wyłączony":
                continue
            if self._in_window(now, _t(s["start"]), _t(s["end"])):
                return (s["action"], int(s["power"]), int(s["soc"]), i)
        return ("general", 0, 0, None)

    async def _apply(self, want):
        action, power, soc = want[:3]
        if action == "ładowanie":
            await self.inv.set_operation_mode(OperationMode.ECO_CHARGE, power, soc)
        elif action == "rozładowanie":
            await self.inv.set_operation_mode(OperationMode.ECO_DISCHARGE, power, soc)
        else:
            await self.inv.set_operation_mode(OperationMode.GENERAL)

    async def _tick(self, *_):
        if not self.active:
            return
        want = self.desired()
        if want == self._applied:
            return
        try:
            await self._apply(want)
            self._applied = want
            action, power, soc, idx = want
            self.status = ("autokonsumpcja" if idx is None
                           else f"slot {idx + 1}: {action} {power}% do SOC {soc}%")
            _LOGGER.info("GoodWe harmonogram: %s", self.status)
        except Exception as err:
            self.status = f"błąd: {err}"
            _LOGGER.error("Nie udało się ustawić trybu: %s", err)
        self._notify()

    def _notify(self):
        for cb in self._listeners:
            cb()


class SlotEntity(Entity):
    _attr_should_poll = False

    def __init__(self, coord, slot, key, name):
        self._sch = coord.scheduler
        self._slot = slot
        self._key = key
        prefix = f"Slot {slot + 1} " if slot is not None else ""
        self._attr_name = f"{prefix}{name}"
        self._attr_unique_id = f"{coord.inverter.serial_number}_sched_{slot}_{key}"
        self._attr_device_info = coord.device_info

    @property
    def _val(self):
        return self._sch.slots[self._slot][self._key]

    async def _save(self, value):
        await self._sch.async_update(self._slot, **{self._key: value})
        self.async_write_ha_state()
