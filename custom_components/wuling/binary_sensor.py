from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.const import STATE_ON
from homeassistant.components.binary_sensor import (
    DOMAIN as ENTITY_DOMAIN,
    BinarySensorEntity as BaseEntity,
)

from . import XEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        async_add_entities([BinarySensorEntity(coordinator, conv)])


class BinarySensorEntity(XEntity, BaseEntity):
    @callback
    def async_set_state(self, data: dict):
        super().async_set_state(data)
        if self.attr in data:
            self._attr_is_on = data[self.attr]

    @callback
    def async_restore_last_state(self, state: str, attrs: dict):
        self._attr_is_on = state == STATE_ON
        self._attr_extra_state_attributes.update(attrs)
