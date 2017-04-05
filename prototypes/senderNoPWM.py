import RPi.GPIO as GPIO
from time import sleep, time
from random import randrange

ledPin = 18

GPIO.setmode(GPIO.BCM)

GPIO.setup(ledPin, GPIO.OUT)

toSend = [1,0,1,0,1,1,0,1]

# Start connection BIT
GPIO.output(ledPin, GPIO.HIGH)
sleep(0.10182)

for i in range(8):
	#randBit = randrange(0,2)
	if toSend[i] == 0:
		GPIO.output(ledPin, GPIO.LOW)
	else:
		GPIO.output(ledPin, GPIO.HIGH)
	sleep(0.10182)

GPIO.cleanup()
