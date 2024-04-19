# coding: utf-8
"""Tests client.py. DIOChaconAPIClient class."""
from dio_chacon_wifi_api.const import DeviceTypeEnum


def test_enum() -> None:
    """Test DeviceTypeEnum."""
    assert DeviceTypeEnum.from_dio_api(".dio1.wifi.genericSwitch.switch.").value == "SWITCH_LIGHT"
    assert DeviceTypeEnum.SWITCH_LIGHT != DeviceTypeEnum.SHUTTER
    assert DeviceTypeEnum.SWITCH_LIGHT.equals(".dio1.wifi.genericSwitch.switch.")
    assert DeviceTypeEnum.SWITCH_LIGHT.equals("SWITCH_LIGHT")
    assert not DeviceTypeEnum.SWITCH_LIGHT.equals("toto")
    assert DeviceTypeEnum("SWITCH_PLUG") in [DeviceTypeEnum.SWITCH_LIGHT, DeviceTypeEnum.SWITCH_PLUG]
    assert "SWITCH_PLUG" not in [DeviceTypeEnum.SWITCH_LIGHT, DeviceTypeEnum.SWITCH_PLUG]
    # ValueError : assert DeviceTypeEnum("toto") not in [DeviceTypeEnum.SWITCH_LIGHT, DeviceTypeEnum.SWITCH_PLUG]
