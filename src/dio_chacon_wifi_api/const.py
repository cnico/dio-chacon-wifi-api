# -*- coding: utf-8 -*-
"""Consts for Dio Chacon wifi python client API."""

from enum import Enum

DIOCHACON_API_URL = "https://l4hfront-prod.chacon.cloud"
DIOCHACON_AUTH_URL = DIOCHACON_API_URL + "/api/session/login"
DIOCHACON_WS_URL = "wss://l4hfront-prod.chacon.cloud/ws"


class DeviceTypeEnum(Enum):
    SHUTTER = ".dio1.wifi.shutter.mvt_linear."
    SWITCH = ".dio1.wifi.genericSwitch.switch."
