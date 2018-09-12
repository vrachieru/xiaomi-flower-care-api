import sys
sys.path.append('../')

from flowercare import FlowerCare

# Initialize FlowerCare device
sensor = FlowerCare(
    mac='c4:7c:8d:xx:xx:xx', # device address
    interface='hci0' # hci0 is default, explicitly static for demo purpose
)

print('Getting data from device..\n')

# Display generic device information
print('Name: {}'.format(sensor.name))
print('Address: {}'.format(sensor.mac))
print('Firmware: {}'.format(sensor.firmware_version))
print('Battery: {}%'.format(sensor.battery_level))

# Display current sensor readings
print('\nReal-time data\n----')
real_time_data = sensor.real_time_data
print('Temperature: {}°C'.format(real_time_data.temperature))
print('Moisture: {}%'.format(real_time_data.moisture))
print('Light: {} lux'.format(real_time_data.light))
print('Conductivity: {} µS/cm'.format(real_time_data.conductivity))

# Display historical sensor readings
print('\nHistorical data\n----')
historical_data = sensor.historical_data
for entry in historical_data:
    print('Timestamp: {}'.format(entry.timestamp))
    print('Temperature: {}°C'.format(entry.temperature))
    print('Moisture: {}%'.format(entry.moisture))
    print('Light: {} lux'.format(entry.light))
    print('Conductivity: {} µS/cm\n'.format(entry.conductivity))
