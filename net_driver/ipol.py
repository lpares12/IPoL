#!/bin/python
import sys
import smbus
import RPi.GPIO as GPIO
from time import time, sleep

##########
# Settings
INTEGRATION_TIME = 0.15 # TODO: Change
INTEGRATION_TIME_WITH_OFFSET = 0.152 # TODO: Change
LOWER_THRESHOLD = 363
UPPER_THRESHOLD = 368
RESYNC_BYTES = 16
IPOL_PREAMBLE = 211 # 11010011 in decimal
IPOL_MTU = 96

LED_PIN = 18

# I2C address of the TSL2561 sensor
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

# Init communication with TSL2561
def begin(bus):
	b = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_REGISTER_ID)
	if b & 0x0A:
		return True
	return False

# Enable the TSL2561 sensor
def enable(bus):
	# address, register (command | control), value (0x03 enable)
	bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_ON)

# Disable the TSL2561 sensor
def disable(bus):
	# address, register (command | control), value (0x00 disable)
	bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_CONTROL, TSL2561_VALUE_CONTROL_OFF)

# Start an integration cycle
def startIntegration(bus):
	#bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_IGNORE)
	bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_MANUAL | TSL2561_VALUE_INTEGRATION_IGNORE)

# End an integration cycle
def stopIntegration(bus):
	bus.write_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_REGISTER_TIMING, TSL2561_VALUE_GAIN_16X | TSL2561_VALUE_INTEGRATION_IGNORE)

# Retrieve the last read BDM value from TSL2561 register
def getLuminosity(bus):
	# read word
	lower = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_LOW)
	higher = bus.read_byte_data(TSL2561_ADDRESS, TSL2561_COMMAND_BIT | TSL2561_WORD_BIT | TSL2561_REGISTER_CH0_HIGH)

	return (higher << 8 | lower)

# Calculate the checksum from the bytearray
# http://www.planetimming.com/checksum8.html
def checksum8(data):
	result = 0
	fctr = 16

	hexStr = "0123456789ABCDEF"

	for value in data:
		index = hexStr.index(str(value).upper())
		result += index * fctr
		if fctr == 16:
			fctr = 1
		else:
			fctr = 16

	if fctr == 1:
		return "odd number of characters"
	else:
		result = (~(result & 0xff) + 1) & 0xff # result&0xff discards all bytes after low-end one
		# In hex:
		# strResult = hexStr[result/16] + hexStr[result%16]
		# return strResult
		return result

# Start the receiver
def startIpolReceive():
	bus = smbus.SMBus(1)
	# if not begin(bus):
	# 	print "Sensor not found"
	# 	return None
	# else:
	enable(bus)

	startIntegration(bus)
	sleep(0.01)
	stopIntegration(bus)
	return bus

# Stop the receiver
def endIpolReceive(bus):
	disable(bus)

# Start the sender
def startIpolSend():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(LED_PIN, GPIO.OUT)

# Send a byte through led. Byte must be an integer number, not string.
def ipolSendByte(byte, sleepTime = INTEGRATION_TIME_WITH_OFFSET):
	i = 7
	while i > -1:
		bit = (byte >> i) & 1
		if bit == 1:
			GPIO.output(LED_PIN, GPIO.HIGH)
		else:
			GPIO.output(LED_PIN, GPIO.LOW)
		sleep(sleepTime)
		i -= 1

# Send the data through the LED
def ipolSend(data):
	# Send size
	size = len(data)
	if size > IPOL_MTU: # If we received data bigger than MTU, discard
		return -1

	checksum = checksum8(str(data.encode('hex_codec')))

	# Send the start bit
	GPIO.output(LED_PIN, GPIO.HIGH)
	sleep(INTEGRATION_TIME_WITH_OFFSET)
	# Send the preamble
	ipolSendByte(IPOL_PREAMBLE)

	# Send size
	ipolSendByte(size)
	# Send checksum
	ipolSendByte(checksum)

	print "Sent size: " + str(size)
	print "Sent checksum: " + str(checksum)

	# Send packet
	resync = 0
	for byte in data:
		if resync == RESYNC_BYTES:
			GPIO.output(LED_PIN, GPIO.LOW)
			resync = 0
			# Send resync bit wait for INTEGRATION_TIME, to let the receiver catch up
			sleep(2*INTEGRATION_TIME)
			GPIO.output(LED_PIN, GPIO.HIGH)
			sleep(INTEGRATION_TIME_WITH_OFFSET)
		resync += 1
		ipolSendByte(ord(byte))
	
	# LED OFF
	GPIO.output(LED_PIN, GPIO.LOW)

	file = open('/tmp/sendfilebinary', 'wb')
	for value in data:
		file.write(("{0:b}".format(ord(value))))
		file.write('\n')
	file.close()

# Receive a byte
def ipolReceiveByte(bus, lastbit = 0):
	byte = 0
	for i in range(8):
		startIntegration(bus)
		sleep(INTEGRATION_TIME)
		stopIntegration(bus)
		value = getLuminosity(bus)
		if value > LOWER_THRESHOLD:
			if value > UPPER_THRESHOLD:
				lastbit = 1
				byte = (byte << 1) + 1
			elif lastbit == 1:
				lastbit = 0
				byte = (byte << 1)
			else:
				lastbit = 1
				byte = (byte << 1) + 1
		else:
			lastbit = 0
			byte = (byte << 1)
	return (byte, lastbit)

# Receive a packet through IPoL
def ipolReceive(bus):
	ret = ""
	# Wait for start connection bit
	while(True):
		startIntegration(bus)
		sleep(INTEGRATION_TIME)
		stopIntegration(bus)
		value = getLuminosity(bus)

		# If start connection bit received
		if value > LOWER_THRESHOLD:
			if ipolReceiveByte(bus)[0] != IPOL_PREAMBLE:
				continue

			size, lastbit = ipolReceiveByte(bus,1)
			checksum, lastbit = ipolReceiveByte(bus, lastbit)

			print "Received size: " + str(size)
			print "Received checksum: " + str(checksum)

			# Receive packet, every RESYNC_BYTES we will resync with the sender
			resync = 0
			for i in range(size):
				if resync == RESYNC_BYTES:
					resync = 0
					lastbit = 1
					sleep(INTEGRATION_TIME/3)
					while True:
						startIntegration(bus)
						sleep(INTEGRATION_TIME)
						stopIntegration(bus)
						if getLuminosity(bus) > LOWER_THRESHOLD:
							break
				
				byte, lastbit = ipolReceiveByte(bus, lastbit)
				ret += chr(byte)
				resync += 1

			# To Debug
			# file = open('/tmp/receivedbinary', 'wb')
			# for value in ret:
			# 	file.write(("{0:b}".format(ord(value))))
			# 	file.write('\n')
			# file.close()

			if checksum8(str(ret.encode('hex_codec'))) == checksum:
				print "Packet correct"
				return ret
			else:
				print "Checksum incorrect, discarding packet"
				ret = ""

	# Should not get here
	return ret