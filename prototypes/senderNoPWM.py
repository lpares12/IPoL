import RPi.GPIO as GPIO
from time import sleep, time
from random import randrange

ledPin = 18

toSend = []

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

# Start connection BIT
GPIO.output(ledPin, GPIO.HIGH)
sleep(0.10182)

for i in range(64):
	randBit = randrange(0,2)
	toSend.append(randBit)
	if randBit == 0:
		GPIO.output(ledPin, GPIO.LOW)
	else:
		GPIO.output(ledPin, GPIO.HIGH)
	sleep(0.10182)

GPIO.cleanup()

output = 0
for bit in toSend:
	if bit == 0:
		output = (output << 1)
	else:
		output = ((output << 1) + 1)

print output