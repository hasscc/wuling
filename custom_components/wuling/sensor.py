from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.components.sensor import (
    DOMAIN as ENTITY_DOMAIN,
    SensorEntity as BaseEntity,
)
from . import XEntity, Converter, StateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        async_add_entities([SensorEntity(coordinator, conv)])

class SensorEntity(XEntity, BaseEntity):
    def __init__(self, coordinator: StateCoordinator, conv: Converter):
        super().__init__(coordinator, conv)
        self._attr_state_class = self._option.get('state_class')
        self._attr_native_unit_of_measurement = self._option.get('unit_of_measurement')

    @callback
    def async_set_state(self, data: dict):
        super().async_set_state(data)
        self._attr_native_value = self._attr_state

    @callback
    def async_restore_last_state(self, state: str, attrs: dict):
        self._attr_native_value = attrs.get(self.attr, state)
        self._attr_extra_state_attributes.update(attrs)
