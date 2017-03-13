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

def setIntegrationTime(bus, manual=False, avtivate=True):
	enable(bus)
	# https://cdn-shop.adafruit.com/datasheets/TSL2561.pdf pag 15, could be done manually would be faster than 13ms
	# TODO: if manual: set it/unset it manually
	# todo: pagina 20 mirar instruccion
	if manual:
		if active:
			bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_MANUAL | TSL2561_VALUE_INTEGRATION_IGNORE)
		else:
			bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_IGNORE)
	else:
		bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_402MS)
	disable(bus)

def getLuminosity(bus):
	# enable
	enable(bus)
	# wait for integration time (should be set to the minimum, 13ms)
	sleep(0.4) # TODO: Should be equal to integration time
	# read word
	lower = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_LOW)
	higher = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_HIGH)
	# disable
	disable(bus)

	return (higher << 8 | lower)

def getIR(bus):
	enable(bus)
	sleep(0.4) # TODO: Should be equal to integration time
	lower = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH1_LOW)
	higher = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH1_HIGH)
	disable(bus)

	return (higher << 8 | lower)


bus = smbus.SMBus(1)

if not begin(bus):
	print "Couldn't find TSL2561, exiting..."
	sys.exit()

start_time = time()

setIntegrationTime(bus)
for i in range(100):
	print getLuminosity(bus)
	#sleep(0.4)

print("Total time: %s\n" % (time() - start_time))
