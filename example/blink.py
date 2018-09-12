import sys
sys.path.append('../')

from flowercare import FlowerCare

# Initialize the FlowerCare device
device = FlowerCare(
    mac='c4:7c:8d:xx:xx:xx', # device address
    interface='hci0' # hci0 is default, explicitly static for demo purpose
)

# Blink
device.blink()
