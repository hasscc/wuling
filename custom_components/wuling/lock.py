from __future__ import annotations

import logging

from homeassistant.core import callback
from homeassistant.components.lock import (
    DOMAIN as ENTITY_DOMAIN,
    LockEntity as BaseEntity,
)

from . import XEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        if conv.attr == 'door_lock':
            entity = DoorLockEntity(coordinator, conv)
        else:
            entity = LockEntity(coordinator, conv)
        async_add_entities([entity])


class LockEntity(XEntity, BaseEntity):
    @callback
    def async_set_state(self, data: dict):
        super().async_set_state(data)
        if self.attr in data:
            self._attr_is_locked = data[self.attr]

class DoorLockEntity(LockEntity):
    async def async_lock(self, **kwargs) -> None:
        """Turn the entity on."""
        await self.coordinator.async_request('car/control/doorLock', json={
            'vin': self.vin,
            'status': kwargs.get('status', 0),
        })

    async def async_unlock(self, **kwargs) -> None:
        """Turn the entity off."""
        await self.async_lock(status=1)
