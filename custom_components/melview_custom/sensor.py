"""Support for MelView device sensors."""
import logging

from pymelview import DEVICE_TYPE_ATA

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    STATE_ON,
    STATE_OFF
)
from homeassistant.components.binary_sensor import DEVICE_CLASS_PROBLEM
from homeassistant.helpers.entity import Entity

from . import MelViewDevice
from .const import DOMAIN, MEL_DEVICES

ATTR_MEASUREMENT_NAME = "measurement_name"
ATTR_ICON = "icon"
ATTR_UNIT = "unit"
ATTR_DEVICE_CLASS = "device_class"
ATTR_VALUE_FN = "value_fn"
ATTR_ENABLED_FN = "enabled"

ATTR_STATE_DEVICE_ID = "device_id"
ATTR_STATE_DEVICE_LAST_SEEN = "last_communication"

ATA_SENSORS = {
    "room_temperature": {
        ATTR_MEASUREMENT_NAME: "Room Temperature",
        ATTR_ICON: "mdi:thermometer",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_VALUE_FN: lambda x: x.device.room_temperature,
        ATTR_ENABLED_FN: lambda x: True,
    },
}

ATA_BINARY_SENSORS = {
    "error_state": {
        ATTR_MEASUREMENT_NAME: "Error State",
        ATTR_ICON: None,
        ATTR_UNIT: None,
        ATTR_DEVICE_CLASS: DEVICE_CLASS_PROBLEM,
        ATTR_VALUE_FN: lambda x: x.error_state,
        ATTR_ENABLED_FN: lambda x: True,
    },
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_sensors(hass, entry, async_add_entities, type_binary, init_status=False):
    """Set up MELView device sensors and bynary sensor based on config_entry."""
    entry_config = hass.data[DOMAIN][entry.entry_id]
    ata_sensors = ATA_BINARY_SENSORS if type_binary else ATA_SENSORS

    mel_devices = entry_config.get(MEL_DEVICES)
    async_add_entities(
        [
            MelDeviceSensor(mel_device, measurement, definition, type_binary)
            for measurement, definition in ata_sensors.items()
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
            if definition[ATTR_ENABLED_FN](mel_device)
        ],
        init_status,
    )


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up MELView device sensors based on config_entry."""
    await async_setup_sensors(hass, entry, async_add_entities, False)


class MelDeviceSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, device: MelViewDevice, measurement, definition, isbinary):
        """Initialize the sensor."""
        self._api = device
        self._name_slug = device.name
        self._measurement = measurement
        self._def = definition
        self._isbinary = isbinary

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"melview_custom_heatpump_{self._api.device.device_id}"

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._def[ATTR_ICON]

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_slug} {self._def[ATTR_MEASUREMENT_NAME]}"

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        if self._isbinary:
            return self._def[ATTR_VALUE_FN](self._api)

        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._isbinary:
            return STATE_ON if self.is_on else STATE_OFF

        return self._def[ATTR_VALUE_FN](self._api)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._def[ATTR_UNIT]

    @property
    def device_class(self):
        """Return device class."""
        return self._def[ATTR_DEVICE_CLASS]

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {
            ATTR_STATE_DEVICE_ID: self._api.device_id,
        }
        return data
