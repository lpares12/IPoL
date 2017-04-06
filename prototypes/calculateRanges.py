import sys
import smbus
import RPi.GPIO as GPIO
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
TSL2561_VALUE_GAIN_1X = 0x00
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

def getLuminosityLine(bus, sleepTime, numIterations):

    high100 = []
    high75 = []
    high50 = []
    high25 = []
    high0 = []

    enable(bus)

    for i in range(numIterations):
        # HIGH 100%
        GPIO.output(18, GPIO.HIGH)
        startIntegration(bus)
        sleep(sleepTime)
        sleep(sleepTime)
        stopIntegration(bus)    
        high100.append(getLuminosity(bus))

        # HIGH 75%
        GPIO.output(18, GPIO.HIGH)
        startIntegration(bus)
        sleep(sleepTime + sleepTime/2)
        GPIO.output(18, GPIO.LOW)
        sleep(sleepTime/2)
        stopIntegration(bus)
        high75.append(getLuminosity(bus))

        # HIGH 50%
        GPIO.output(18, GPIO.HIGH)
        startIntegration(bus)
        sleep(sleepTime)
        GPIO.output(18, GPIO.LOW)
        sleep(sleepTime)
        stopIntegration(bus)    
        high50.append(getLuminosity(bus))

        # HIGH 25%
        GPIO.output(18, GPIO.HIGH)
        startIntegration(bus)
        sleep(sleepTime/2)
        GPIO.output(18, GPIO.LOW)
        sleep(sleepTime + sleepTime/2)
        stopIntegration(bus)
        high25.append(getLuminosity(bus))

        # HIGH 0%
        GPIO.output(18, GPIO.LOW)
        startIntegration(bus)
        sleep(sleepTime)
        sleep(sleepTime)
        stopIntegration(bus)    
        high0.append(getLuminosity(bus))

    disable(bus)

    print "High 100%:", sum(high100)/numIterations
    print "High 75%:", sum(high75)/numIterations
    print "High 50%:", sum(high50)/numIterations
    print "High 25%:", sum(high25)/numIterations
    print "High 0%:", sum(high0)/numIterations


# for i in 0.025 0.05 0.075 0.1 0.15 0.2 0.25 0.3 0.4 0.5 0.75 1; do python calculateThreshold.py $i 3; sleep 1; done
def main():
    integrationTime = float(sys.argv[1])
    sleepTime = integrationTime/2
    numIterations = int(sys.argv[2])

    print("Integration time: %s" % integrationTime)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18, GPIO.OUT)
    bus = smbus.SMBus(1)

    if not begin(bus):
        print "Sensor not found"
        sys.exit()

    getLuminosityLine(bus, sleepTime, numIterations)

    
if __name__ == '__main__':
    main()