from bluepy.btle import Peripheral
from datetime import datetime, timedelta
from logging import getLogger
from time import time, sleep

from .exception import FlowerCareException

_BYTE_ORDER = 'little'

_HANDLE_DEVICE_NAME = 0x03
_HANDLE_DEVICE_TIME = 0x41
_HANDLE_DATA_READ = 0x35
_HANDLE_MODE_CHANGE = 0x33
_HANDLE_FIRMWARE_AND_BATTERY = 0x38
_HANDLE_HISTORY_CONTROL = 0x3e
_HANDLE_HISTORY_READ = 0x3c

_CMD_BLINK_LED = bytes([0xfd, 0xff])
_CMD_REAL_TIME_READ_INIT = bytes([0xa0, 0x1f])
_CMD_HISTORY_READ_INIT = bytes([0xa0, 0x00, 0x00])
_CMD_HISTORY_READ_SUCCESS = bytes([0xa2, 0x00, 0x00])
_CMD_HISTORY_READ_FAILED = bytes([0xa3, 0x00, 0x00])

_LOGGER = getLogger(__name__)

class FlowerCare(object):
    '''
    Represents a Xiaomi Flower Care device
    '''

    def __init__(self, mac, interface='hci0'):
        '''Initialize a Xiaomi Flower Care for the given MAC address.'''
        self._mac = mac
        self._interface = interface

    @property
    def name(self):
        '''Return the name of the device'''
        response = self._read_handle(_HANDLE_DEVICE_NAME)
        return ''.join(chr(byte) for byte in response)

    @property
    def mac(self):
        '''Return the MAC of the device'''
        return self._mac

    @property
    def firmware_version(self):
        '''Return the current firmware version'''
        response = self._read_handle(_HANDLE_FIRMWARE_AND_BATTERY)
        return ''.join(map(chr, response[2:]))

    @property
    def battery_level(self):
        '''Return the current battery level'''
        response = self._read_handle(_HANDLE_FIRMWARE_AND_BATTERY)
        return response[0]

    @property
    def real_time_data(self):
        '''Return the current readings from the 4 sensors'''
        # For the newer models we need to explicitly set the device in real-time data reading mode
        if self.firmware_version >= '2.6.6':
            self._write_handle(_HANDLE_MODE_CHANGE, _CMD_REAL_TIME_READ_INIT)

        response = self._read_handle(_HANDLE_DATA_READ)
        return RealTimeEntry(response)

    @property
    def historical_data(self):
        '''Return list of historical readings from the 4 sensors'''
        self._write_handle(_HANDLE_HISTORY_CONTROL, _CMD_HISTORY_READ_INIT)

        historical_data = []
        raw_historical_data = self._read_handle(_HANDLE_HISTORY_READ)
        history_length = int.from_bytes(raw_historical_data[:2], _BYTE_ORDER)
        
        _LOGGER.info('Detected %d entries in device history', history_length)

        if history_length > 0:
            epoch_time = self._epoch_time
            for i in range(history_length):
                payload = self._calculate_historical_entry_address(i)
                try:
                    _LOGGER.info('Reading historical entry %d of %d', i, history_length)
                    self._write_handle(_HANDLE_HISTORY_CONTROL, payload)
                    response = self._read_handle(_HANDLE_HISTORY_READ)
                    historical_data.append(HistoricalEntry(response, epoch_time))
                except Exception as exception:
                    _LOGGER.error('Could only retrieve %d of %d entries from the history. The rest is not readable.', i, history_length)
                    break

        return historical_data

    def clear_history(self):
        '''Remove historical entries from device'''
        self._write_handle(_HANDLE_HISTORY_CONTROL, _CMD_HISTORY_READ_SUCCESS)

    def blink(self):
        '''Blink the status LED'''
        self._write_handle(_HANDLE_MODE_CHANGE, _CMD_BLINK_LED)

    def _calculate_historical_entry_address(self, addr):
        '''Calculate address of provided historical entry index'''
        return b'\xa1' + addr.to_bytes(2, _BYTE_ORDER)

    def _format_bytes(self, raw_data):
        '''Pretty print an array of bytes'''
        if raw_data is None:
            return 'None'
        return ' '.join([format(c, '02x') for c in raw_data]).upper()

    @property
    def _epoch_time(self):
        '''Return the device epoch (boot) time'''
        start = time()
        response = self._read_handle(_HANDLE_DEVICE_TIME)
        
        wall_time = (time() + start) / 2
        epoch_offset = int.from_bytes(response, _BYTE_ORDER)
        epoch_time = wall_time - epoch_offset        

        return epoch_time

    def _read_handle(self, handle):
        '''Read a handle from the device'''
        with Peripheral(self._mac, iface=self._interface) as connection:
            response = connection.readCharacteristic(handle)
            _LOGGER.debug('Received response for handle %s: %s', handle, self._format_bytes(response))
        return response

    def _write_handle(self, handle, command):
        '''Write a value to a handle'''
        with Peripheral(self._mac, iface=self._interface) as connection:
            connection.writeCharacteristic(handle, command, True)
            _LOGGER.debug('Wrote command %s to handle %s', self._format_bytes(command), handle)

class RealTimeEntry(object):
    '''
    Represents a real time entry of sensor values by parsing the byte array returned by the device.
    
    The sensor returns 16 bytes in total.
    It's unclear what the meaning of these bytes is beyond what is decoded in this method.
    
    Semantics of the data (in little endian encoding):
    bytes   0-1: temperature in 0.1 °C
    byte      2: unknown
    bytes   3-6: brightness in lux
    byte      7: moisture in %
    byted   8-9: conductivity in µS/cm
    bytes 10-15: unknown
    '''

    def __init__(self, byte_array):
        self.temperature = int.from_bytes(byte_array[:2], _BYTE_ORDER) / 10.0
        self.light = int.from_bytes(byte_array[3:7], _BYTE_ORDER)
        self.moisture = byte_array[7]
        self.conductivity = int.from_bytes(byte_array[8:10], _BYTE_ORDER)

class HistoricalEntry(object):
    '''
    Represents a historical entry of sensor values by parsing the byte array returned by the device.
    
    The sensor returns 16 bytes in total.
    It's unclear what the meaning of these bytes is beyond what is decoded in this method.
    
    Semantics of the data (in little endian encoding):
    bytes   0-3: timestamp, seconds since boot
    bytes   4-5: temperature in 0.1 °C
    byte      6: unknown
    bytes   7-9: brightness in lux
    byte     10: unknown
    byte     11: moisture in %
    bytes 12-13: conductivity in µS/cm
    bytes 14-15: unknown
    '''
    def __init__(self, byte_array, epoch_time):
        epoch_offset = int.from_bytes(byte_array[:4], _BYTE_ORDER)
        self.timestamp = datetime.fromtimestamp(epoch_time + epoch_offset)
        self.timestamp = self.timestamp.replace(minute=0, second=0, microsecond=0) # compensate for wall time
        self.temperature = int.from_bytes(byte_array[4:6], _BYTE_ORDER) / 10.0
        self.light = int.from_bytes(byte_array[7:10], _BYTE_ORDER)
        self.moisture = byte_array[11]
        self.conductivity = int.from_bytes(byte_array[12:14], _BYTE_ORDER)
