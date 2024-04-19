# -*- coding: utf-8 -*-
"""Consts for Dio Chacon wifi python client API."""
from enum import Enum

DIOCHACON_API_URL = "https://l4hfront-prod.chacon.cloud"
DIOCHACON_AUTH_URL = DIOCHACON_API_URL + "/api/session/login"
DIOCHACON_WS_URL = "wss://l4hfront-prod.chacon.cloud/ws"


class DeviceTypeEnum(Enum):

    def from_dio_api(label: str):
        dict_array = [
            {'label': ".dio1.wifi.shutter.mvt_linear.", 'code': "SHUTTER"},
            {'label': ".dio1.wifi.genericSwitch.switch.", 'code': "SWITCH_LIGHT"},
            {'label': ".dio1.wifi.plug.switch.", 'code': "SWITCH_PLUG"},
        ]
        for d in dict_array:
            if d['label'] == label:
                return DeviceTypeEnum(d['code'])
        return None

    def equals(self, other_label: str) -> bool:
        if DeviceTypeEnum.from_dio_api(other_label) == self:
            return True
        if other_label in [e.value for e in DeviceTypeEnum]:
            return True
        return False

    SHUTTER = "SHUTTER"
    SWITCH_LIGHT = "SWITCH_LIGHT"
    SWITCH_PLUG = "SWITCH_PLUG"


class ShutterMoveEnum(Enum):
    UP = "up"
    STOP = "stop"
    DOWN = "down"


class SwitchOnOffEnum(Enum):
    ON = 1
    OFF = 0
