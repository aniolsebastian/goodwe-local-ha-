from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coord = hass.data["goodwe_local"][entry.entry_id]
    ents = [GoodWeSensor(coord, s) for s in coord.inverter.sensors() if s.id_]
    ents.append(ScheduleStatus(coord))
    async_add_entities(ents)


class GoodWeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coord, sensor):
        super().__init__(coord)
        self._s = sensor
        self._attr_name = sensor.name
        self._attr_unique_id = f"{coord.inverter.serial_number}_{sensor.id_}"
        self._attr_native_unit_of_measurement = sensor.unit or None
        self._attr_device_info = coord.device_info
        if sensor.unit in ("W", "V", "A", "°C", "%", "Hz"):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensor.unit == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        val = self.coordinator.data.get(self._s.id_)
        return val.name if hasattr(val, "name") else val


class ScheduleStatus(SensorEntity):
    _attr_should_poll = False
    _attr_name = "Status harmonogramu"
    _attr_icon = "mdi:battery-clock-outline"

    def __init__(self, coord):
        self._sch = coord.scheduler
        self._attr_unique_id = f"{coord.inverter.serial_number}_sched_status"
        self._attr_device_info = coord.device_info

    async def async_added_to_hass(self):
        self._sch.add_listener(self.async_write_ha_state)

    @property
    def native_value(self):
        return self._sch.status
