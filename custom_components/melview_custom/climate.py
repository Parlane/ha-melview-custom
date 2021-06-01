"""Platform for climate integration."""
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from pymelview import DEVICE_TYPE_ATA, AtaDevice
import pymelview.ata_device as ata
from pymelview.device import PROPERTY_POWER

from homeassistant.components.climate.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    # SUPPORT_PRESET_MODE,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.typing import HomeAssistantType

from . import MelViewDevice
from .const import (
    ATTR_STATUS,
    ATTR_VANE_VERTICAL,
    ATTR_VANE_HORIZONTAL,
    DOMAIN,
    MEL_DEVICES,
    HorSwingModes,
    VertSwingModes,
)

try:
    from homeassistant.components.climate import ClimateEntity
except ImportError:
    from homeassistant.components.climate import ClimateDevice as ClimateEntity

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


ATA_HVAC_MODE_LOOKUP = {
    ata.OPERATION_MODE_HEAT: HVAC_MODE_HEAT,
    ata.OPERATION_MODE_DRY: HVAC_MODE_DRY,
    ata.OPERATION_MODE_COOL: HVAC_MODE_COOL,
    ata.OPERATION_MODE_FAN_ONLY: HVAC_MODE_FAN_ONLY,
    ata.OPERATION_MODE_HEAT_COOL: HVAC_MODE_HEAT_COOL,
}
ATA_HVAC_MODE_REVERSE_LOOKUP = {v: k for k, v in ATA_HVAC_MODE_LOOKUP.items()}


ATA_HVAC_VVANE_LOOKUP = {
    ata.V_VANE_POSITION_AUTO: VertSwingModes.Auto,
    ata.V_VANE_POSITION_1: VertSwingModes.Top,
    ata.V_VANE_POSITION_2: VertSwingModes.MiddleTop,
    ata.V_VANE_POSITION_3: VertSwingModes.Middle,
    ata.V_VANE_POSITION_4: VertSwingModes.MiddleBottom,
    ata.V_VANE_POSITION_5: VertSwingModes.Bottom,
    ata.V_VANE_POSITION_SWING: VertSwingModes.Swing,
}
ATA_HVAC_VVANE_REVERSE_LOOKUP = {v: k for k, v in ATA_HVAC_VVANE_LOOKUP.items()}


ATA_HVAC_HVANE_LOOKUP = {
    ata.H_VANE_POSITION_AUTO: HorSwingModes.Auto,
    ata.H_VANE_POSITION_1: HorSwingModes.Left,
    ata.H_VANE_POSITION_2: HorSwingModes.MiddleLeft,
    ata.H_VANE_POSITION_3: HorSwingModes.Middle,
    ata.H_VANE_POSITION_4: HorSwingModes.MiddleRight,
    ata.H_VANE_POSITION_5: HorSwingModes.Right,
    ata.H_VANE_POSITION_SPLIT: HorSwingModes.Split,
    ata.H_VANE_POSITION_SWING: HorSwingModes.Swing,
}
ATA_HVAC_HVANE_REVERSE_LOOKUP = {v: k for k, v in ATA_HVAC_HVANE_LOOKUP.items()}

async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Set up MelView device climate based on config_entry."""
    mel_devices = hass.data[DOMAIN][entry.entry_id].get(MEL_DEVICES)
    _LOGGER.warning("Devices=")
    _LOGGER.warning(mel_devices)
    _LOGGER.warning(mel_devices[DEVICE_TYPE_ATA])

    async_add_entities(
        [
            AtaDeviceClimate(mel_device, mel_device.device)
            for mel_device in mel_devices[DEVICE_TYPE_ATA]
        ],
        True,
    )


class MelViewClimate(ClimateEntity):
    """Base climate device."""

    def __init__(self, device: MelViewDevice):
        """Initialize the climate."""
        self.api = device
        self._base_device = self.api.device
        self._name = device.name

    async def async_update(self):
        """Update state from MELView."""
        await self.api.async_update()

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self.api.device_info

    @property
    def target_temperature_step(self) -> Optional[float]:
        """Return the supported step of target temperature."""
        return self._base_device.temperature_increment


class AtaDeviceClimate(MelViewClimate):
    """Air-to-Air climate device."""

    def __init__(self, device: MelViewDevice, ata_device: AtaDevice):
        """Initialize the climate."""
        super().__init__(device)
        self._device = ata_device
        self._support_ver_swing = len(self._device.vane_vertical_positions) > 0
        self._support_hor_swing = len(self._device.vane_horizontal_positions) > 0
        self._set_hor_swing = self._support_hor_swing and not self._support_ver_swing

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return f"heatpump_{self._device.device_id}"

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the optional state attributes with device specific additions."""
        attr = {}

        vane_horizontal = self._device.vane_horizontal
        if vane_horizontal:
            attr.update(
                {ATTR_VANE_HORIZONTAL: ATA_HVAC_HVANE_LOOKUP.get(vane_horizontal, None)}
            )

        vane_vertical = self._device.vane_vertical
        if vane_vertical:
            attr.update(
                {ATTR_VANE_VERTICAL: ATA_HVAC_VVANE_LOOKUP.get(vane_vertical, None)}
            )
        return attr

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation ie. heat, cool mode."""
        mode = self._device.operation_mode
        if not self._device.power or mode is None:
            return HVAC_MODE_OFF
        return ATA_HVAC_MODE_LOOKUP.get(mode)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            await self._device.set({PROPERTY_POWER: False})
            return

        operation_mode = ATA_HVAC_MODE_REVERSE_LOOKUP.get(hvac_mode)
        if operation_mode is None:
            raise ValueError(f"Invalid hvac_mode [{hvac_mode}]")

        props = {ata.PROPERTY_OPERATION_MODE: operation_mode}
        if self.hvac_mode == HVAC_MODE_OFF:
            props[PROPERTY_POWER] = True
        await self._device.set(props)

    @property
    def hvac_modes(self) -> List[str]:
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_OFF] + [
            ATA_HVAC_MODE_LOOKUP.get(mode) for mode in self._device.operation_modes
        ]

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._device.room_temperature

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._device.target_temperature

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        await self._device.set(
            {ata.PROPERTY_TARGET_TEMPERATURE: kwargs.get("temperature", self.target_temperature)}
        )

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the fan setting."""
        return self._device.fan_speed

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._device.set({ata.PROPERTY_FAN_SPEED: fan_mode})

    @property
    def fan_modes(self) -> Optional[List[str]]:
        """Return the list of available fan modes."""
        return self._device.fan_speeds

    @property
    def swing_mode(self) -> Optional[str]:
        """Return the swing mode setting."""
        swing = None
        if self._set_hor_swing and self._support_hor_swing:
            mode = self._device.vane_horizontal
            if mode is not None:
                swing = ATA_HVAC_HVANE_LOOKUP.get(mode)
        elif self._support_ver_swing:
            mode = self._device.vane_vertical
            if mode is not None:
                swing = ATA_HVAC_VVANE_LOOKUP.get(mode)

        if swing is None:
            return "Auto"

        return swing

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing mode."""
        is_hor_swing = False
        operation_mode = ATA_HVAC_VVANE_REVERSE_LOOKUP.get(swing_mode)
        if operation_mode is None:
            operation_mode = ATA_HVAC_HVANE_REVERSE_LOOKUP.get(swing_mode)
            if operation_mode is None:
                raise ValueError(f"Invalid swing_mode [{swing_mode}].")

            is_hor_swing = True
            curr_mode = self._device.vane_horizontal
            valid_swing_modes = self._device.vane_horizontal_positions
            props = {ata.PROPERTY_VANE_HORIZONTAL: operation_mode}
        else:
            curr_mode = self._device.vane_vertical
            valid_swing_modes = self._device.vane_vertical_positions
            props = {ata.PROPERTY_VANE_VERTICAL: operation_mode}

        if operation_mode not in valid_swing_modes:
            raise ValueError(f"Invalid swing_mode [{swing_mode}].")

        self._set_hor_swing = is_hor_swing
        if curr_mode != operation_mode:
            await self._device.set(props)

    @property
    def swing_modes(self) -> Optional[List[str]]:
        """Return the list of available swing modes."""
        list_modes = [
            ATA_HVAC_VVANE_LOOKUP.get(mode)
            for mode in self._device.vane_vertical_positions
        ]
        for mode in self._device.vane_horizontal_positions:
            list_modes.append(ATA_HVAC_HVANE_LOOKUP.get(mode))

        return list_modes

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._device.set({PROPERTY_POWER: True})

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self._device.set({PROPERTY_POWER: False})

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supp_feature = SUPPORT_FAN_MODE | SUPPORT_TARGET_TEMPERATURE
        if self._support_ver_swing or self._support_hor_swing:
            supp_feature |= SUPPORT_SWING_MODE

        # if self._support_hor_swing == True:
        #     supp_feature |= SUPPORT_PRESET_MODE

        return supp_feature

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        min_value = self._device.target_temperature_min
        if min_value is not None:
            return min_value

        return DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        max_value = self._device.target_temperature_max
        if max_value is not None:
            return max_value

        return DEFAULT_MAX_TEMP
