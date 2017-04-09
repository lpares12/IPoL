import sys
import smbus
from time import sleep, time

TSL2561_ADDRESS = 0x39

# Bit to indicate a command is "being sent"
TSL2561_COMMAND_BIT = 0x80
# Bit to indicate a word is going to be read
TSL2561_WORD_BIT = 0x20

TSL2561_REGISTER_ID = 0x0A
TSL2561_REGISTER_CONTROL = 0x00
TSL2561_REGISTER_TIMING = 0x01
    # Visible light channel
TSL2561_REGISTER_CH0_LOW = 0x0C # low significance byte
TSL2561_REGISTER_CH0_HIGH = 0x0D # high significance byte

TSL2561_VALUE_INTEGRATION_IGNORE = 0x03
TSL2561_VALUE_INTEGRATION_MANUAL = 0x08
TSL2561_VALUE_GAIN_16X = 0x10

TSL2561_VALUE_CONTROL_ON = 0x03
TSL2561_VALUE_CONTROL_OFF = 0x00

def begin(bus):
    b = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_REGISTER_ID)
    if b & 0x0A:
        return True
    return False

def enable(bus):
    # address, register (command | control), value (0x03 enable)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_ON)

def disable(bus):
    # address, register (command | control), value (0x00 disable)
    bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_OFF)

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

def read(bus, integrationTime, lowerThreshold, upperThreshold):
    oldValue = 0
    result = 0

    for i in range(8): # byte
        startIntegration(bus)
        sleep(integrationTime)
        stopIntegration(bus)
        newValue = getLuminosity(bus)
        if newValue > lowerThreshold:
            if newValue > upperThreshold:
                oldValue = 1
                result = ((result << 1) + 1)
            elif oldValue == 1:
                # A 0 was read
                oldValue = 0
                result = (result << 1)
            else:
                # A 1 was read
                oldValue = 1
                result = ((result << 1) + 1)
        else:
            # A 0 was read
            oldValue = 0
            result = (result << 1)
    return result

# python receiver.py 256 0.025 77 81
# python receiver.py 256 0.05 157 160
# python receiver.py 256 0.1 310 320
# python receiver.py 256 0.15 470 475
# python receiver.py 256 0.20 627 632
def main():
    bits = int(sys.argv[1])
    integrationTime = float(sys.argv[2])
    lowerThreshold = int(sys.argv[3])
    upperThreshold = int(sys.argv[4])

    bytesCount = bits/8
    result = []

    bus = smbus.SMBus(1)

    if not begin(bus):
        print "Sensor not found"
        sys.exit()

    enable(bus)

    # Wait for start connection bit
    while(True):
        startIntegration(bus)
        sleep(integrationTime)
        stopIntegration(bus)
        value = getLuminosity(bus)

        # If start connection bit received
        if value > lowerThreshold:
            for i in range(bytesCount):
                result.append(read(bus, integrationTime, lowerThreshold, upperThreshold))
            break


    disable(bus)

    print result

if __name__ == '__main__':
    main()