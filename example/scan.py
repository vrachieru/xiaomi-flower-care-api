import sys
import json
from collections import OrderedDict
sys.path.append('../')

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
