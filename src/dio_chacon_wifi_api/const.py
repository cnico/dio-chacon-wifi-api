# -*- coding: utf-8 -*-
"""Consts for Dio Chacon wifi python client API."""
from enum import Enum

DIOCHACON_WS_URL = "wss://l4hfront-prod.chacon.cloud/ws"


class DeviceTypeEnum(Enum):

    def from_dio_api(label: str):
        dict_array = [
            {'label': ".wifi.shutter.", 'code': "SHUTTER"},
            {'label': ".wifi.genericSwitch.", 'code': "SWITCH_LIGHT"},
            {'label': ".wifi.plug.", 'code': "SWITCH_PLUG"},
        ]
        for d in dict_array:
            if d['label'] in label:
                return DeviceTypeEnum(d['code'])
        return DeviceTypeEnum.UNKNOWN

    def equals(self, other_label: str) -> bool:
        if DeviceTypeEnum.from_dio_api(other_label) == self:
            return True
        if other_label in [e.value for e in DeviceTypeEnum]:
            return True
        return False

    SHUTTER = "SHUTTER"
    SWITCH_LIGHT = "SWITCH_LIGHT"
    SWITCH_PLUG = "SWITCH_PLUG"
    UNKNOWN = "UNKNOWN"


class ShutterMoveEnum(Enum):
    UP = "up"
    STOP = "stop"
    DOWN = "down"


class SwitchOnOffEnum(Enum):
    ON = 1
    OFF = 0
