from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.components.climate import (
    DOMAIN as ENTITY_DOMAIN,
    ClimateEntity as BaseEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
    UnitOfTemperature,
    ATTR_TEMPERATURE,
)

from . import XEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        async_add_entities([ClimateEntity(coordinator, conv)])


class ClimateEntity(XEntity, BaseEntity):
    _attr_hvac_mode = None
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.COOL,
        HVACMode.HEAT,
    ]
    _attr_fan_mode = None
    _attr_max_temp = 33
    _attr_min_temp = 17
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1

    @property
    def car_status(self):
        return self.coordinator.car_status or {}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._attr_fan_modes = ['1', '2', '3', '4', '5', '6', '7']
        self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_supported_features |= ClimateEntityFeature.FAN_MODE

    @callback
    def async_set_state(self, data: dict):
        super().async_set_state(data)
        if self.attr in data:
            self._attr_hvac_mode = data[self.attr]
        self._attr_hvac_action = {
            HVACMode.COOL: HVACAction.COOLING,
            HVACMode.HEAT: HVACAction.HEATING,
        }.get(self._attr_hvac_mode)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        ret = False
        if ATTR_TEMPERATURE in kwargs:
            num = kwargs[ATTR_TEMPERATURE]
            if ret := await self.async_ac_control(temperature=num):
                self._attr_target_temperature = num
        return ret

    async def async_set_hvac_mode(self, hvac_mode):
        ret = None
        if hvac_mode == HVACMode.OFF:
            ret = await self.async_ac_control(accOnOff='0', status='0')
        elif hvac_mode == HVACMode.COOL:
            ret = await self.async_ac_control(status='1')
        elif hvac_mode == HVACMode.HEAT:
            ret = await self.async_ac_control(status='2')
        else:
            ret = await self.async_ac_control(accOnOff='1')
        if ret:
            self._attr_hvac_mode = hvac_mode
        return ret

    async def async_set_fan_mode(self, fan_mode: str):
        """Set new target fan mode."""
        if await self.async_ac_control(blowerLvl=fan_mode):
            self._attr_fan_mode = fan_mode

    async def async_ac_control(self, **kwargs):
        result = await self.coordinator.async_request('car/control/acc', json={
            # 'vin': self.vin,
            'accOnOff': '1',
            'duration': '10', # minutes
            'blowerLvl': str(self.fan_mode or 3),
            'temperature': str(self.target_temperature or 23),
            **kwargs,
        }) or {}
        return result.get('result')
