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
            {'label': ".dio1.wifi.genericSwitch.switch.", 'code': "SWITCH"},
        ]
        result: str = ''
        for d in dict_array:
            if d['label'] == label:
                result = d['code']
        return DeviceTypeEnum(result)

    SHUTTER = "SHUTTER"
    SWITCH = "SWITCH"


class ShutterMoveEnum(Enum):
    UP = "UP"
    STOP = "STOP"
    DOWN = "DOWN"
