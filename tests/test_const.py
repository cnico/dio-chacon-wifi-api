# coding: utf-8
"""Tests client.py. DIOChaconAPIClient class."""
from dio_chacon_wifi_api.const import DeviceTypeEnum


def test_enum() -> None:
    """Test DeviceTypeEnum."""
    assert DeviceTypeEnum.from_dio_api(".dio1.wifi.genericSwitch.switch.").value == "LIGHT"
    assert DeviceTypeEnum.LIGHT != DeviceTypeEnum.SHUTTER
    assert DeviceTypeEnum.LIGHT.equals(".dio1.wifi.genericSwitch.switch.")
    assert DeviceTypeEnum.LIGHT.equals("LIGHT")
    assert not DeviceTypeEnum.LIGHT.equals("toto")
