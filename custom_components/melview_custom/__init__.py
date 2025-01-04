"""The MELView Climate integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientConnectionError, ClientSession
from async_timeout import timeout
from pymelview import Device, get_devices
import pymelview.client
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import Throttle

from .const import (
    CONF_DISABLE_SENSORS,
    CONF_LANGUAGE,
    DOMAIN,
    LANGUAGES,
    MEL_DEVICES,
    Language,
)

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

PLATFORMS = ["climate", "sensor", "binary_sensor"]

MELVIEW_SCHEMA = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_LANGUAGE): vol.In(LANGUAGES.keys()),
    vol.Optional(CONF_DISABLE_SENSORS, default=False): bool,
    #vol.Required(CONF_TOKEN): cv.string,
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: MELVIEW_SCHEMA
    },
    extra=vol.ALLOW_EXTRA,
)

class MelViewAuthentication:
    def __init__(self, email: str, password: str, language: int = Language.English):
        self._email: str = email
        self._password: str = password
        self._language: int = language
        self._client = None

    def isLogin(self):
        return self._client != None

    async def login(self, _session: ClientSession) -> bool:
        _LOGGER.debug("Login ...")

        self._client = None

        try:
            self._client = await pymelview.login(self._email, self._password, session=_session)
            return True
        except:
            _LOGGER.error("Login to MELView failed!")
            return False

    def getContextKey(self):
        return self._client


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Establish connection with MELView."""
    if DOMAIN not in config:
        return True

    conf = config.get(DOMAIN)

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=conf,
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Establish connection with MELView."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    language = conf[CONF_LANGUAGE]
    mclanguage = LANGUAGES[language]

    _LOGGER.info(
        "Initializing %s platform with user: %s - language: %s(%s).",
        DOMAIN,
        username,
        language,
        str(mclanguage)
    )

    mcauth = MelViewAuthentication(username, conf[CONF_PASSWORD], mclanguage)
    try:
        result: bool = await mcauth.login(async_get_clientsession(hass))
        if not result:
            raise ConfigEntryNotReady()
    except:
        raise ConfigEntryNotReady()

    client = mcauth.getContextKey()
    mel_devices = await mel_devices_setup(hass, client)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {}).update(
        {
            MEL_DEVICES: mel_devices,
        }
    )
    disable_sensors = conf.get(CONF_DISABLE_SENSORS, False)

    platforms: list[str] = []
    for platform in PLATFORMS:
        if platform == "climate" or not disable_sensors:
            platforms.append(platform)


    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    await asyncio.gather(
        *[
            hass.config_entries.async_forward_entry_unload(config_entry, platform)
            for platform in PLATFORMS
        ]
    )
    hass.data[DOMAIN].pop(config_entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


class MelViewDevice:
    """MELView Device instance."""

    def __init__(self, device: Device) -> None:
        """Construct a device wrapper."""
        self.device: Device = device
        self.name: str = device.name
        self._available = True

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Pull the latest data from MELView."""
        try:
            await self.device.update()
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    async def async_set(self, properties: Dict[str, Any]) -> None:
        """Write state changes to the MELView API."""
        try:
            await self.device.set(properties)
            self._available = True
        except ClientConnectionError:
            _LOGGER.warning("Connection failed for %s", self.name)
            self._available = False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_id(self):
        """Return device ID."""
        return self.device.device_id

    @property
    def building_id(self):
        """Return building ID of the device."""
        return self.device.building_id

    @property
    def device_conf(self):
        """Return device_conf of the device."""
        return self.device._device_conf

    @property
    def error_state(self) -> Optional[bool]:
        """Return error_state."""
        if self.device._device_conf is None:
            return None
        device = self.device._device_conf
        return device.get("HasError", False)

    @property
    def has_wide_van(self) -> Optional[bool]:
        """Return has wide van info."""
        if self.device._device_conf is None:
            return False
        device = self.device._device_conf
        return device.get("HasWideVane", False)

    @property
    def device_info(self):
        """Return a device description for device registry."""
        _device_info = {
            "identifiers": {(DOMAIN, f"heatpump_{self.device.device_id}")},
            "manufacturer": "Mitsubishi Electric",
            "name": self.name,
            "model": "MELView IF (ID: %s)" % (self.device.device_id)
        }
        return _device_info


async def mel_devices_setup(hass: HomeAssistant, client) -> List[MelViewDevice]:
    """Query connected devices from MELView."""
    session: ClientSession = async_get_clientsession(hass)
    try:
        with timeout(10):
            all_devices = await get_devices(
                client,
                session,
                conf_update_interval=timedelta(minutes=5),
                device_set_debounce=timedelta(seconds=1),
            )
    except (asyncio.TimeoutError, ClientConnectionError) as ex:
        raise ConfigEntryNotReady() from ex

    wrapped_devices = {}
    for device_type, devices in all_devices.items():
        wrapped_devices[device_type] = [MelViewDevice(device) for device in devices]
    return wrapped_devices
