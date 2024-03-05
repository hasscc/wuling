import logging
import aiohttp
import voluptuous as vol
from datetime import timedelta
import hashlib
import time
import random
import string

from homeassistant.core import HomeAssistant, State, ServiceCall, SupportsResponse, callback
from homeassistant.const import (
    Platform,
    CONF_ACCESS_TOKEN,
    PERCENTAGE,
    UnitOfLength,
    UnitOfTemperature,
    UnitOfElectricPotential,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .converters.base import *


DOMAIN = 'wuling'
TITLE = '五菱汽车'
API_BASE = 'https://openapi.baojun.net/junApi/sgmw'

SUPPORTED_PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
]
_LOGGER = logging.getLogger(__name__)


def generate_random_letters(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

sgmwnonce = generate_random_letters(10)
sgmwclientid = '2019041810222516127'
sgmwclientsecret = 'c5ad2a4290faa3df39683865c2e10310'
sgmwappcode = 'sgmw_llb'
sgmwappversion = '1656'
sgmwsystem = 'android'
sgmwsystemversion = '10'


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(entry.entry_id, {})
    hass.data[entry.entry_id].setdefault('entities', {})
    coordinator = StateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data[entry.entry_id]['coordinator'] = coordinator

    hass.services.async_register(
        DOMAIN, 'update_status', coordinator.update_from_service,
        schema=vol.Schema({}, extra=vol.ALLOW_EXTRA),
        supports_response=SupportsResponse.OPTIONAL,
    )

    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)

    return True


class StateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{entry.entry_id}-coordinator",
            update_interval=timedelta(seconds=60),
        )
        self.entry = entry
        self.entities = {}

        from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
        from homeassistant.components.binary_sensor import BinarySensorDeviceClass
        self.converters = [
            NumberSensorConv('battery', prop='carStatus.batterySoc').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'device_class': SensorDeviceClass.BATTERY,
                'unit_of_measurement': PERCENTAGE,
            }),
            NumberSensorConv('total_mileage', prop='carStatus.mileage').with_option({
                'state_class': SensorStateClass.TOTAL,
                'device_class': SensorDeviceClass.DISTANCE,
                'unit_of_measurement': UnitOfLength.KILOMETERS,
            }),
            NumberSensorConv('left_mileage', prop='carStatus.leftMileage').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'device_class': SensorDeviceClass.DISTANCE,
                'unit_of_measurement': UnitOfLength.KILOMETERS,
            }),
            NumberSensorConv('left_mileage_oil', prop='carStatus.oilLeftMileage').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'device_class': SensorDeviceClass.DISTANCE,
                'unit_of_measurement': UnitOfLength.KILOMETERS,
            }),
            NumberSensorConv('oil_level', prop='carStatus.leftFuel').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'unit_of_measurement': PERCENTAGE,
            }),
            NumberSensorConv('battery_temp', prop='carStatus.batAvgTemp').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'device_class': SensorDeviceClass.TEMPERATURE,
                'unit_of_measurement': UnitOfTemperature.CELSIUS,
            }),
            NumberSensorConv('battery_voltage', prop='carStatus.lowBatVol').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'device_class': SensorDeviceClass.VOLTAGE,
                'unit_of_measurement': UnitOfElectricPotential.VOLT,
            }),
            NumberSensorConv('battery_health', prop='carStatus.batHealth').with_option({
                'state_class': SensorStateClass.MEASUREMENT,
                'unit_of_measurement': PERCENTAGE,
            }),
            SensorConv('battery_status', prop='carStatus.batteryStatus').with_option({
                'icon': 'mdi:battery-check-outline',
            }),

            BinarySensorConv('door_status', prop='carStatus.doorOpenStatus').with_option({
                'icon': 'mdi:car-door',
                'device_class': BinarySensorDeviceClass.DOOR,
            }),
            BinarySensorConv('door1_status', prop='carStatus.door1OpenStatus', parent='door_status'),
            BinarySensorConv('door2_status', prop='carStatus.door2OpenStatus', parent='door_status'),
            BinarySensorConv('door3_status', prop='carStatus.door3OpenStatus', parent='door_status'),
            BinarySensorConv('door4_status', prop='carStatus.door4OpenStatus', parent='door_status'),
            BinarySensorConv('tail_door_status', prop='carStatus.tailDoorOpenStatus', parent='door_status'),

            BinarySensorConv('door_locked', prop='carStatus.doorLockStatus').with_option({
                'icon': 'mdi:car-door-lock',
                'device_class': BinarySensorDeviceClass.LOCK,
            }),
            BinarySensorConv('door1_locked', prop='carStatus.door1LockStatus', parent='door_locked'),
            BinarySensorConv('door2_locked', prop='carStatus.door2LockStatus', parent='door_locked'),
            BinarySensorConv('door3_locked', prop='carStatus.door3LockStatus', parent='door_locked'),
            BinarySensorConv('door4_locked', prop='carStatus.door4LockStatus', parent='door_locked'),
            BinarySensorConv('tail_door_locked', prop='carStatus.tailDoorLockStatus', parent='door_locked'),

            BinarySensorConv('window_status', prop='carStatus.windowOpenStatus').with_option({
                'icon': 'mdi:dock-window',
                'device_class': BinarySensorDeviceClass.WINDOW,
            }),
            BinarySensorConv('window1_status', prop='carStatus.window1OpenStatus', parent='window_status'),
            BinarySensorConv('window2_status', prop='carStatus.window2OpenStatus', parent='window_status'),
            BinarySensorConv('window3_status', prop='carStatus.window3OpenStatus', parent='window_status'),
            BinarySensorConv('window4_status', prop='carStatus.window4OpenStatus', parent='window_status'),

            BinarySensorConv('charging', prop='carStatus.charging').with_option({
                'device_class': BinarySensorDeviceClass.BATTERY_CHARGING,
            }),
            MapSensorConv('key_status', prop='carStatus.keyStatus', map={
                '0': '无钥匙',
                '1': '已连接',
                '2': '已启动',
            }).with_option({
                'icon': 'mdi:car-key',
            }),
            MapSensorConv('gear_status', prop='carStatus.autoGearStatus', map={
                '10': 'P',
                '12': 'D',
            }).with_option({
                'icon': 'mdi:cog-outline',
            }),

            Converter('location', Platform.DEVICE_TRACKER, prop='carStatus.location').with_option({
                'icon': 'mdi:car',
            }),
            NumberSensorConv('latitude', prop='carStatus.latitude', parent='location', precision=6),
            NumberSensorConv('longitude', prop='carStatus.longitude', parent='location', precision=6),
            NumberSensorConv('battery_level', prop='carStatus.batterySoc', parent='location'),
            SensorConv('vin', prop='carInfo.vin', parent='location'),
            SensorConv('name', prop='carInfo.carName', parent='location'),
            SensorConv('plate', prop='carInfo.carPlate', parent='location'),
            SensorConv('color', prop='carInfo.colorName', parent='location'),
            SensorConv('entity_picture', prop='carInfo.image', parent='location'),
            SensorConv('collect_time', prop='carStatus.collectTime', parent='location'),
        ]

    @property
    def access_token(self):
        return self.entry.data.get(CONF_ACCESS_TOKEN, '')

    @property
    def car_info(self):
        return self.data.get('carInfo') or {}

    @property
    def car_status(self):
        return self.data.get('carStatus') or {}

    @property
    def car_name(self):
        return self.car_info.get('carName', '')

    @property
    def vin(self):
        return self.car_info.get('vin', '')

    @property
    def vin_sort(self):
        vin = f'{self.vin}'.lower()
        if not vin:
            return DOMAIN
        return f'{vin[:6]}_{vin[-6:]}'

    @property
    def model(self):
        name = self.car_info.get('carTypeName', '')
        model = self.car_info.get('model', '')
        return f'{name} {model}'.strip()

    async def update_from_service(self, call: ServiceCall):
        data = call.data
        await self.async_request_refresh()
        return self.data

    async def _async_update_data(self):
        timestamp = int(time.time() * 1000)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'okhttp/4.9.0',
            'channel': 'linglingbang',
            'platformNo': 'Android',
            'appVersionCode': '1656',
            'version': 'V8.2.3.1',
            'imei': 'a-c62b2f538bf34758',
            'imsi': 'unknown',
            'deviceModel': 'MI 8',
            'deviceBrand': 'Xiaomi',
            'deviceType': 'Android',
            'accessChannel': '1',
            'sgmwaccesstoken': self.access_token,
            'sgmwtimestamp': str(timestamp),
            'sgmwnonce': sgmwnonce,
            'sgmwclientid': sgmwclientid,
            'sgmwclientsecret': sgmwclientsecret,
            'sgmwappcode': sgmwappcode,
            'sgmwappversion': sgmwappversion,
            'sgmwsystem': sgmwsystem,
            'sgmwsystemversion': sgmwsystemversion,
            'sgmwsignature': self.get_sign(timestamp, sgmwnonce),
        }
        try:
            res = await async_get_clientsession(self.hass).request(
                method='POST',
                url=f'{API_BASE}/userCarRelation/queryDefaultCarStatus',
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        except Exception as err:
            _LOGGER.error('Request error: %s', err)
            return {}
        result = await res.json() or {}
        data = result.get('data') or {}
        _LOGGER.info('Update data: %s', result)
        return data

    def get_sign(self, timestamp, nonce):
        # 计算签名
        sign_str = (self.access_token +
                    str(timestamp) +
                    nonce +
                    sgmwclientid +
                    sgmwclientsecret +
                    sgmwappcode +
                    sgmwappversion +
                    sgmwsystem +
                    sgmwsystemversion)
        return hashlib.md5(sign_str.encode()).hexdigest().lower()

    def decode(self, data: dict) -> dict:
        """Decode props for HASS."""
        payload = {}
        for conv in self.converters:
            prop = conv.prop or conv.attr
            value = get_value(data, prop, None)
            if prop is None:
                continue
            conv.decode(self, payload, value)
        return payload

    def push_state(self, value: dict):
        """Push new state to Hass entities."""
        if not value:
            return
        attrs = value.keys()

        for entity in self.entities.values():
            if not hasattr(entity, 'subscribed_attrs'):
                continue
            if not (entity.subscribed_attrs & attrs):
                continue
            entity.async_set_state(value)
            if entity.added:
                entity.async_write_ha_state()

    def subscribe_attrs(self, conv: Converter):
        attrs = {conv.attr}
        if conv.childs:
            attrs |= set(conv.childs)
        attrs.update(c.attr for c in self.converters if c.parent == conv.attr)
        return attrs


class XEntity(CoordinatorEntity):
    log = _LOGGER
    added = False
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, coordinator: StateCoordinator, conv: Converter, option=None):
        super().__init__(coordinator)
        self.conv = conv
        self.attr = conv.attr
        self.hass = coordinator.hass
        self.entry = coordinator.entry
        self._option = option or {}
        if hasattr(conv, 'option'):
            self._option.update(conv.option or {})
        self.entity_id = f'{conv.domain}.{coordinator.vin_sort}_{conv.attr}'
        self._attr_unique_id = f'{DOMAIN}-{self.entry.entry_id}-{self.attr}'
        self._attr_icon = self._option.get('icon')
        self._attr_device_class = self._option.get('device_class')
        self._attr_entity_picture = self._option.get('entity_picture')
        self._attr_entity_category = self._option.get('entity_category')
        self._attr_translation_key = self._option.get('translation_key', conv.attr)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.vin)},
            name=coordinator.car_name,
            model=coordinator.model,
        )
        self._attr_entity_registry_enabled_default = conv.enabled is not False
        self._attr_extra_state_attributes = {}
        self._vars = {}
        self.subscribed_attrs = coordinator.subscribe_attrs(conv)
        coordinator.entities[conv.attr] = self

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if hasattr(self, 'async_get_last_state'):
            state: State = await self.async_get_last_state()
            if state:
                self.async_restore_last_state(state.state, state.attributes)

        self.added = True
        self.update()

    @callback
    def async_restore_last_state(self, state: str, attrs: dict):
        """Restore previous state."""
        self._attr_state = state

    @callback
    def async_set_state(self, data: dict):
        """Handle state update from gateway."""
        if hasattr(self.conv, 'option'):
            self._option.update(self.conv.option or {})
        if self.attr in data:
            self._attr_state = data[self.attr]
            self._attr_entity_picture = self._option.get('entity_picture')
        for k in self.subscribed_attrs:
            if k not in data:
                continue
            self._attr_extra_state_attributes[k] = data[k]
        _LOGGER.info('%s: State changed: %s', self.entity_id, data)

    def update(self):
        payload = self.coordinator.decode(self.coordinator.data)
        self.coordinator.push_state(payload)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
