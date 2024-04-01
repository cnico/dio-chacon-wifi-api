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
            {'label': ".dio1.wifi.genericSwitch.switch.", 'code': "LIGHT"},
        ]
        result: str = ''
        for d in dict_array:
            if d['label'] == label:
                result = d['code']
        return DeviceTypeEnum(result)

    def equals(self, other_label: str) -> bool:
        return DeviceTypeEnum.from_dio_api(other_label) == self

    SHUTTER = "SHUTTER"
    LIGHT = "LIGHT"


class ShutterMoveEnum(Enum):
    UP = "up"
    STOP = "stop"
    DOWN = "down"


class LightOnOffEnum(Enum):
    ON = 1
    OFF = 0
