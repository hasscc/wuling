from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.components.switch import (
    DOMAIN as ENTITY_DOMAIN,
    SwitchEntity as BaseEntity,
)

from . import XEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        async_add_entities([SwitchEntity(coordinator, conv)])


class SwitchEntity(XEntity, BaseEntity):
    @callback
    def async_set_state(self, data: dict):
        super().async_set_state(data)
        if self.attr in data:
            self._attr_is_on = data[self.attr]
