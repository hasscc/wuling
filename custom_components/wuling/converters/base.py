from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING
from homeassistant.const import EntityCategory
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

if TYPE_CHECKING:
    from .. import StateCoordinator as Client


def get_value(obj, key, def_value=None):
    keys = f'{key}'.split('.')
    result = obj
    for k in keys:
        if result is None:
            return None
        if isinstance(result, dict):
            result = result.get(k, def_value)
        if isinstance(result, (list, tuple)):
            try:
                result = result[int(key)]
            except Exception:
                result = def_value
    return result


@dataclass
class Converter:
    attr: str  # hass attribute
    domain: Optional[str] = None  # hass domain

    prop: Optional[str] = None
    parent: Optional[str] = None

    enabled: Optional[bool] = True  # support: True, False, None (lazy setup)
    poll: bool = False  # hass should_poll

    # don't init with dataclass because no type:
    childs: Optional[set] = None
    option = None

    # to hass
    def decode(self, client: "Client", payload: dict, value: Any):
        payload[self.attr] = value

    # from hass
    def encode(self, client: "Client", payload: dict, value: Any):
        payload[self.prop or self.attr] = value

    def with_option(self, option: dict):
        self.option = option
        return self

@dataclass
class BoolConv(Converter):
    reverse: bool = None

    def decode(self, device: "Client", payload: dict, value: int):
        val = True if value else False
        if value in ['0', 'no', 'off', 'false']:
            val = False
        val = (not val) if self.reverse else bool(val)
        payload[self.attr] = val

    def encode(self, device: "Client", payload: dict, value: bool):
        val = (not value) if self.reverse else value
        super().encode(device, payload, int(val))

@dataclass
class MapConv(Converter):
    map: dict = None
    default: Any = None

    def decode(self, device: "Client", payload: dict, value: int):
        payload[self.attr] = self.map.get(value, self.default)

    def encode(self, device: "Client", payload: dict, value: Any):
        value = next(k for k, v in self.map.items() if v == value)
        super().encode(device, payload, value)

@dataclass
class SensorConv(Converter):
    domain: Optional[str] = 'sensor'

@dataclass
class BinarySensorConv(BoolConv):
    domain: Optional[str] = 'binary_sensor'

@dataclass
class ProblemConv(BinarySensorConv):

    def __post_init__(self):
        self.option = {
            'device_class': BinarySensorDeviceClass.PROBLEM,
            'entity_category': EntityCategory.DIAGNOSTIC,
            **(self.option or {}),
        }

@dataclass
class NumberSensorConv(SensorConv):
    ratio: Optional[float] = 1
    precision: Optional[int] = 1

    def decode(self, client: "Client", payload: dict, value: Any):
        try:
            val = float(f'{value}'.strip())
            val = val * self.ratio
            val = round(val, self.precision)
        except (TypeError, ValueError):
            val = None
        payload[self.attr] = val

@dataclass
class MapSensorConv(MapConv, SensorConv):
    domain: Optional[str] = 'sensor'

@dataclass
class ButtonConv(Converter):
    domain: Optional[str] = 'button'
    press: Optional[str] = ''

    def encode(self, client: "Client", payload: dict, value: Any):
        async def press(*args, **kwargs):
            if self.press and hasattr(client, self.press):
                return await getattr(client, self.press)()
            return False
        return press
