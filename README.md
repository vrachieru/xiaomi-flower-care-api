<p align="center">
    <img src="https://user-images.githubusercontent.com/5860071/46300250-e5c87800-c5ab-11e8-91b4-6a8af99f9b8d.png" width="200px" border="0" />
    <br/>
    <a href="https://github.com/vrachieru/xiaomi-flower-care-api/releases/latest">
        <img src="https://img.shields.io/badge/version-1.0-brightgreen.svg?style=flat-square" alt="Version">
    </a>
    <a href="https://travis-ci.org/vrachieru/xiaomi-flower-care-api">
        <img src="https://img.shields.io/travis/vrachieru/xiaomi-flower-care-api.svg?style=flat-square" alt="Version">
    </a>
    <br/>
    Poll Xiaomi Flower Care (MiFlora) sensors without relying on the official app
</p>

## About Mi Flora

* [Xiaomi Flower Care (MiFlora) sensors](https://xiaomi-mi.com/sockets-and-sensors/xiaomi-huahuacaocao-flower-care-smart-monitor) ([e.g. 12-17€](https://www.aliexpress.com/wholesale?SearchText=xiaomi+mi+flora+plant+sensor)) are meant to keep your plants alive by monitoring their environment
* Has sensors to relay temperature, light intensity, soil moisture and soil fertility (via electrical conductivity)
* Uses Bluetooth Low Energy (BLE) and has a rather limited range
* A coin cell battery is used as power source, which should last between 1.5 to 2 years under normal conditions
* Food for thought: The sensor can also be used for other things than plants, like in the [fridge](https://community.openhab.org/t/refrigerator-temperature-sensors/40076) or as [door and blind sensor](https://community.openhab.org/t/miflora-cheap-window-and-door-sensor-water-sensor-blind-sensor-etc/38232)

## Features

* Device discovery
* Read name
* Read firmware version
* Read battery level
* Read real-time sensor values
* Read historical sensor values
* Clear historical sensor values
* Blink LED

## Install

```bash
$ pip3 install git+https://github.com/vrachieru/xiaomi-flower-care-api.git
```
or
```bash
$ git clone https://github.com/vrachieru/xiaomi-flower-care-api.git
$ pip3 install ./xiaomi-flower-care-api
```

## Usage

### Device discovery

```python
import json
from collections import OrderedDict
from flowercare import FlowerCare, FlowerCareScanner

# Initialize the scanner with BT interface and a 
# custom callback for newly discovered devices.
scanner = FlowerCareScanner(
    interface='hci0',  # hci0 is default, explicitly stating for demo purpose
    callback=lambda device: print('Found device', device.addr) # any lambda with the device as the sole argument will do
)

# Scan advertisements for 10 seconds 
# and return found device list.
devices = scanner.scan(timeout=10)

# Iterate over results and query the information 
# for each individual device.
device_information = OrderedDict()
for device in devices:
    device = FlowerCare(
        mac=device.addr, # address of the device to connect to
        interface='hci0' # hci0 is default, only explicitly stating for demo purpose
    )
    device_information[device.mac] = OrderedDict([
        ('name', device.name),
        ('firmware', device.firmware_version),
        ('battery', device.battery_level),
        ('measurements', device.real_time_data.__dict__)
    ])

# Pretty print device information
print(json.dumps(device_information, indent=4))
```

```bash
$ sudo python3 scan.py
Found device c4:7c:8d:xx:xx:xx
Found device c4:7c:8d:yy:yy:yy

{
    "c4:7c:8d:xx:xx:xx": {
        "name": "Flower care",
        "firmware": "3.1.9",
        "battery": 99,
        "measurements": {
            "temperature": 23.7,
            "moisture": 23,
            "conductivity": 210,
            "light": 89
        }
    },
    "c4:7c:8d:yy:yy:yy": {
        "name": "Flower care",
        "firmware": "3.1.9",
        "battery": 100,
        "measurements": {
            "temperature": 25.2,
            "moisture": 68,
            "conductivity": 1980,
            "light": 3587
        }
    }
}
```

### Reading device information and sensor data

```python
from flowercare import FlowerCare

# Initialize FlowerCare device
device = FlowerCare(
    mac='c4:7c:8d:xx:xx:xx', # device address
    interface='hci0' # hci0 is default, explicitly static for demo purpose
)

print('Getting data from device..\n')

# Display generic device information
print('Name: {}'.format(device.name))
print('Address: {}'.format(device.mac))
print('Firmware: {}'.format(device.firmware_version))
print('Battery: {}%'.format(device.battery_level))

# Display current sensor readings
print('\nReal-time data\n----')
real_time_data = device.real_time_data
print('Temperature: {}°C'.format(real_time_data.temperature))
print('Moisture: {}%'.format(real_time_data.moisture))
print('Light: {} lux'.format(real_time_data.light))
print('Conductivity: {} µS/cm'.format(real_time_data.conductivity))

# Display historical sensor readings
print('\nHistorical data\n----')
historical_data = device.historical_data
for entry in historical_data:
    print('Timestamp: {}'.format(entry.timestamp))
    print('Temperature: {}°C'.format(entry.temperature))
    print('Moisture: {}%'.format(entry.moisture))
    print('Light: {} lux'.format(entry.light))
    print('Conductivity: {} µS/cm\n'.format(entry.conductivity))
```

```bash
$ sudo python3 read.py
Getting data from device..

Name: Flower care
Address: C4:7C:XX:XX:XX:XX
Firmware: 3.1.9
Battery: 99%

Real-time data
----
Temperature: 23.6°C
Moisture: 23%
Light: 68 lux
Conductivity: 211 µS/cm

Historical data
----
Timestamp: 2018-09-30 23:00:00
Temperature: 23.7°C
Moisture: 23%
Light: 24 lux
Conductivity: 211 µS/cm

Timestamp: 2018-09-30 22:00:00
Temperature: 24.1°C
Moisture: 24%
Light: 24 lux
Conductivity: 212 µS/cm

Timestamp: 2018-09-30 21:00:00
Temperature: 24.5°C
Moisture: 24%
Light: 164 lux
Conductivity: 212 µS/cm

...
```

### Blink

```python
from flowercare import FlowerCare

# Initialize the FlowerCare device
device = FlowerCare(
    mac='c4:7c:8d:xx:xx:xx', # device address
    interface='hci0' # hci0 is default, explicitly static for demo purpose
)

# Blink
device.blink()
```


## Protocol

The device uses BLE GATT for communication, but the sensor values are not immediately available.  
When the original app connects to the device, it performs an elaborate initialization, but most of it isn't required.

### BLE & GATT

The basic technologies behind the sensors communication are [Bluetooth Low Energy (BLE)](https://en.wikipedia.org/wiki/Bluetooth_Low_Energy) and [GATT](https://www.bluetooth.com/specifications/gatt).  
They allow the devices and the app to share data in a defined manner and define the way you can discover the devices and their services.  
In general you have to know about services and characteristics to talk to a BLE device.  

Adafruit's Kevin Townsend has published a really nice introduction on the subject and if you don't know about BLE and/or GATT you should definitely give it a look.

### Services, characteristics and handles

##### Root service

| Service UUID                         | Characteristic UUID                  | Handle | Read/Write | Description               |
| ------------------------------------ | ------------------------------------ | ------ | ---------- | ------------------------- |
| 0000fe95-0000-1000-8000-00805f9b34fb | -                                    | -      | -          | used for device discovery |

##### Generic access

| Service UUID                         | Characteristic UUID                  | Handle | Read/Write | Description |
| ------------------------------------ | ------------------------------------ | ------ | ---------- | ----------- |
| 00001800-0000-1000-8000-00805f9b34fb | 00002800-0000-1000-8000-00805f9b34fb | 0x0003 | read       | device name |

##### Data service

| Service UUID                         | Characteristic UUID                  | Handle | Read/Write | Description                            |
| ------------------------------------ | ------------------------------------ | ------ | ---------- | -------------------------------------- |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a00-0000-1000-8000-00805f9b34fb | 0x0033 | write      | device mode change (send command)      |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a01-0000-1000-8000-00805f9b34fb | 0x0035 | read       | get real-time sensor values            |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a02-0000-1000-8000-00805f9b34fb | 0x0038 | read       | get firmware version and battery level |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a11-0000-1000-8000-00805f9b34fb | 0x003c | read       | get historical sensor values           |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a10-0000-1000-8000-00805f9b34fb | 0x003e | write      | |
| 00001204-0000-1000-8000-00805f9b34fb | 00001a12-0000-1000-8000-00805f9b34fb | 0x0041 | read       | device time                            |

<img src="https://user-images.githubusercontent.com/5860071/46303322-347a1000-c5b4-11e8-802d-35704e510b0a.png" width="200px" alt="Little endian" align="right" />

### Data structure

The data is encoded on bytes in Little endian.  
This means that the data is represented with the least significant byte first.  

To understand multi-byte integer representation, you can consult this [Wikipedia page](https://en.wikipedia.org/wiki/Endianness).

### Name

A read request to the `0x03` handle will return n bytes of data, for example `0x466c6f7765722063617265` corresponding to the device name.

| Position | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 |
| -------- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Value    | 46 | 6c | 6f | 77 | 65 | 72 | 20 | 63 | 61 | 72 | 65 |

| Bytes | Type       | Value       | Description |
| ----- | ---------- | ----------- | ----------- |
| all   | ASCII text | Flower Care | device name |

### Firmware and battery

A read request to the `0x38` handle will return 7 bytes of data, for example `0x6328332e312e39`.

| Position | 00 | 01 | 02 | 03 | 04 | 05 | 06 |
| -------- | -- | -- | -- | -- | -- | -- | -- |
| Value    | 63 | 28 | 33 | 2e | 31 | 2e | 39 |

| Bytes | Type       | Value | Description        |
| ----- | ---------- | ----- | ------------------ |
| 00    | uint8      | 99    | battery level in % |
| 02-06 | ASCII text | 3.1.8 | firmware version   |

The second byte (`0x28`) seems to be a separator. In older firmware versions it always read `0x13`.  
Both are control characters in the ASCII table.

### Device time

A read request to the `0x41` handle will return 4 bytes of data, for example `0x09ef2000`.

| Position | 00 | 01 | 02 | 03 |
| -------- | -- | -- | -- | -- |
| Value    | 09 | ef | 20 | 00 |

| Bytes | Type       | Value   | Description                       |
| ----- | ---------- | ------- | --------------------------------- |
| 00-03 | uint32     | 2158345 | seconds since device epoch (boot) |

Considering the device's epoch as second 0, the value obtained is a delta from now from which we can determine the actual time.  
We use this method while determining the datetime of historical entries.

### Real-time data 

In order to read the sensor values you need to change its mode.  
This can be done by writing 2 bytes (`0xa01f`) to the mode change handle (`0x33`).  
After writing them you can read the actual sensor values from the data handle (`0x35`).

A read request will return 16 bytes of data, for example `0xea0000ab00000015b200023c00fb349b`.

| Position | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 |
| -------- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Value    | ea | 00 | 00 | ab | 00 | 00 | 00 | 15 | b2 | 00 | 02 | 3c | 00 | fb | 34 | 9b |

| Bytes | Type       | Value | Description           |
| ----- | ---------- | ----- | --------------------- |
| 00-01 | uint16     | 234   | temperature in 0.1 °C |
| 02    | ?          | ?     | ?                     |
| 03-06 | uint32     | 171   | brightness in lux     |
| 07    | uint8      | 21    | moisture in %         |
| 08-09 | uint16     | 178   | conductivity in µS/cm |
| 10-15 | ?          | ?     | ?                     |

### Historical data

The device stores historical data when not connected that can be later synchronized.  
As with reading real-time sensor information, we need to change the device mode by writing 3 bytes (`0xa00000`) to the history control handle (`0x3e`).  

##### Entry count 

The next step is to get information about the stored history by reading from the history data handle (`0x3c`).  
This will return 16 bytes of data, for example `0x2b007b04ba130800c815080000000000`.  

| Position | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 |
| -------- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Value    | 2b | 00 | 7b | 04 | ba | 13 | 08 | 00 | c8 | 15 | 08 | 00 | 00 | 00 | 00 | 00 |

| Bytes | Type       | Value | Description                         |
| ----- | ---------- | ----- | ----------------------------------- |
| 00-01 | unint16    | 43    | number of stored historical records |
| 02-15 | ?          | ?     | ?                                   |

##### Read entry

Next we need to read each historical entry individually.  
To do so we need to calculate it's address, write it to the history control handle (`0x3e`) and then read the entry from the history data handle (`0x3c`).  

The address for each individual entry is computed by adding two bytes representing the entry index to `0xa1`.  
Entry `0`'s address will be `0xa10000`, entry `1`'s address `0xa10100`, entry `16`'s address `0xa11000`, and so on...  

After writing the address of the entry to be read, be can do so by requesting the payload from the history read handle (`0x3c`).  
This will return 16 bytes of data, for example `0x70e72000eb00005a00000015b3000000`.  

| Position | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 |
| -------- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| Value    | 70 | e7 | 20 | 00 | eb | 00 | 00 | 5a | 00 | 00 | 00 | 15 | b3 | 00 | 00 | 00 |

| Bytes | Type       | Value   | Description                                  |
| ----- | ---------- | ------- | -------------------------------------------- |
| 00-03 | uint32     | 2156400 | timestamp, seconds since device epoch (boot) |
| 04-05 | uint16     | 235     | temperature in 0.1 °C                        |
| 06    | ?          | ?       | ?                                            |
| 07-09 | uint32     | 90      | brightness in lux                            |
| 10    | ?          | ?       | ?                                            |
| 11    | uint8      | 21      | moisture in %                                |
| 12-13 | uint16     | 179     | conductivity in µS/cm                        |
| 14-15 |            | ?       | ?                                            |

##### Clear entries

Once all entries have been read, they can be wiped from the device by marking the process as `successful`.  
This can be achieved by writing 3 bytes (`0xa20000`) to the history control handle (`0x3e`).

### Blink

Writing 2 bytes (`0xfdff`) to the mode change handle (`0x33`) will make the device blink the top LED once.

## Reference

[1] https://wiki.hackerspace.pl/projects:xiaomi-flora  
[2] https://github.com/open-homeautomation/miflora  
[3] https://github.com/ChrisScheffler/miflora 

## License

MIT