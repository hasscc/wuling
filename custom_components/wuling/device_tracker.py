from __future__ import annotations

import logging

from homeassistant.components.device_tracker import (
    DOMAIN as ENTITY_DOMAIN,
    TrackerEntity as BaseEntity,
    SourceType,
)

from . import XEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[entry.entry_id]['coordinator']
    for conv in coordinator.converters:
        if conv.parent or conv.domain != ENTITY_DOMAIN:
            continue
        async_add_entities([TrackerEntity(coordinator, conv)])


class TrackerEntity(XEntity, BaseEntity):
    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device.

        Percentage from 0-100.
        """
        return self._attr_extra_state_attributes.get('battery_level')

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._attr_extra_state_attributes.get('location_name')

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._attr_extra_state_attributes.get('latitude')

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._attr_extra_state_attributes.get('longitude')
