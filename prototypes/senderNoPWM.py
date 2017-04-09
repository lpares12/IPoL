import RPi.GPIO as GPIO
from time import sleep, time
from random import randrange
import sys

# python senderNoPWM.py 256 0.1 0.00182
bits = int(sys.argv[1])
bytesCount = bits/8
integrationTime = float(sys.argv[2])
deriveTime = float(sys.argv[3])

ledPin = 18
sleepTime = integrationTime + deriveTime
toSend = []

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

# Start connection BIT
GPIO.output(ledPin, GPIO.HIGH)
sleep(sleepTime)

for i in range(bytesCount):
	byte = 0
	for i in range(8):
		randBit = randrange(0,2)
		if randBit == 0:
			GPIO.output(ledPin, GPIO.LOW)
			byte = (byte << 1)
		else:
			GPIO.output(ledPin, GPIO.HIGH)
			byte = ((byte << 1) + 1)
		sleep(sleepTime)
	toSend.append(byte)

GPIO.cleanup()

print toSend