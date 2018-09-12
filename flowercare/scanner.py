from re import search
from bluepy.btle import Scanner, ScanEntry, DefaultDelegate

from .exception import FlowerCareException

_DEVICE_PREFIX = 'c4:7c:8d:'
_DEVICE_NAMES = ['flower mate', 'flower care']

_DEVICE_NAME = lambda dev: dev.getValueText(ScanEntry.COMPLETE_LOCAL_NAME)
_DEFAULT_CALLBACK = lambda dev: print('Found new device', dev.addr, _DEVICE_NAME(dev))
_DEVICE_FILTER = lambda dev: (dev.addr and dev.addr.lower().startswith(_DEVICE_PREFIX)) \
    and (_DEVICE_NAME(dev) and _DEVICE_NAME(dev).lower() in _DEVICE_NAMES)


class FlowerCareScanner(object):
    '''
    Represents a Xiaomi Flower Care discovery service
    '''

    def __init__(self, interface='hci0', callback=_DEFAULT_CALLBACK):
        self._interface = self._parse_interface(interface)
        self._callback = callback

    def _parse_interface(self, interface):
        match_result = search(r'hci([\d]+)', interface)
        if match_result is None:
            raise FlowerCareException(
                'Invalid pattern "{}" for Bluetooth interface. '
                'Expected something like "hci0".'.format(interface))
        return int(match_result.group(1))

    def scan(self, timeout=10.0):
        delegate = _ScanDelegate(self._callback)
        scanner = Scanner(self._interface).withDelegate(delegate)
        devices = list(filter(_DEVICE_FILTER, scanner.scan(float(timeout))))
        return devices


class _ScanDelegate(DefaultDelegate):
    '''
    Represents a delegate called upon the discovery of each new device
    '''

    def __init__(self, callback):
        DefaultDelegate.__init__(self)
        self.callback = callback
 
    def handleDiscovery(self, dev, is_new_device, is_new_data):
        if is_new_device and _DEVICE_FILTER(dev):
                self.callback(dev)
