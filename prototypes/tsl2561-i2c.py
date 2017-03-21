import sys
import smbus
from time import sleep, time

TSL2561_ADDRESS = 0x39

# Bit to indicate a command is "being sent"
TSL2561_COMMAND_BIT = 0x80
# Bit to indicate a word is going to be read
TSL2561_WORD_BIT = 0x20

# Registers
TSL2561_REGISTER_ID = 0x0A
TSL2561_REGISTER_CONTROL = 0x00
TSL2561_REGISTER_TIMING = 0x01
    # Visible light channel
TSL2561_REGISTER_CH0_LOW = 0x0C # low significance byte
TSL2561_REGISTER_CH0_HIGH = 0x0D # high significance byte
    # Infrared light channel
TSL2561_REGISTER_CH1_LOW = 0x0E
TSL2561_REGISTER_CH1_HIGH = 0x0F

# Values that the different registries can take
TSL2561_VALUE_INTEGRATION_13MS = 0x00
TSL2561_VALUE_INTEGRATION_101MS = 0x01
TSL2561_VALUE_INTEGRATION_402MS = 0x02
TSL2561_VALUE_INTEGRATION_IGNORE = 0x03
TSL2561_VALUE_INTEGRATION_MANUAL = 0x08

TSL2561_VALUE_GAIN_1X = 0x00
TSL2561_VALUE_GAIN_16X = 0x10
TSL2561_VALUE_CONTROL_ON = 0x03
TSL2561_VALUE_CONTROL_OFF = 0x00

def begin(bus):
    l = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_REGISTER_ID)
    if l & 0x0A:
        return True
    return False

def enable(bus):
    # address, register (command | control), value (0x03 enable)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_ON)

def disable(bus):
    # address, register (command | control), value (0x00 disable)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_OFF)

def setIntegrationTime(bus):
    # enable(bus)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_402MS)
    # disable(bus)

def startIntegration(bus):
    #bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_IGNORE)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_MANUAL | TSL2561_VALUE_INTEGRATION_IGNORE)

def stopIntegration(bus):
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_IGNORE)

def getLuminosity(bus):
    # read word
    lower = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_LOW)
    higher = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_HIGH)

    return (higher << 8 | lower)

def getIR(bus):
    lower = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH1_LOW)
    higher = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH1_HIGH)

    return (higher << 8 | lower)

def main():
    bus = smbus.SMBus(1)

    start_time = time()

    # look for sensor
    if not begin(bus):
        print "Couldn't find TSL2561, exiting..."
        sys.exit()

    setIntegrationTime(bus)
    enable(bus)

    for i in range(100):
        startIntegration(bus)
        sleep(0.025)
        stopIntegration(bus)
        print getLuminosity(bus)

    disable(bus)

    print("Total time: %s\n" % (time() - start_time))



if __name__ == '__main__':
    main()
