# Calculates Derive Time

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


def calculateGap(bus, integrationTime, threshold):
    enable(bus)

    result = 0
    # Print how much time it takes for each iteration.
    start_time = time()
    for i in range(8):
        startIntegration(bus)
        sleep(integrationTime)
        stopIntegration(bus)
        newValue = getLuminosity(bus)
        if newValue > (threshold):
            # A 1 was read
            result = ((result << 1) + 1)
        else:
            # A 0 was read
            result = (result << 1)

    totalTime = time() - start_time # ignore sleep time, and calculate avg execution time  for each iteration.
    disable(bus)

    return ((totalTime-(integrationTime*8))/8)

# for i in 0.025 0.05 0.075 0.1 0.15 0.2 0.25 0.3 0.4 0.5 0.75 1; do python calculateGapTime.py $i 3; sleep 1; done
def main():
    integrationTime = float(sys.argv[1])
    iterations = int(sys.argv[2])
    print("Integration time: %s" % integrationTime) 
    threshold = 100 # Not important for this calculation

    bus = smbus.SMBus(1)

    if not begin(bus):
        print "Sensor not found"
        sys.exit()

    value = 0
    for i in range(iterations):
        value += calculateGap(bus, integrationTime, threshold)
    
    print("Iteration time: %s\n" % (value/iterations))

if __name__ == '__main__':
    main()